from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_FITRESULT_FILE = (
    _REPO_ROOT
    / "run"
    / "fits"
    / "J100"
    / "run_481_3000_sixPar"
    / "FitResult_anaFit_sixPar_bkgOnly.root"
)

# python/ExtractFitParameters.py does `import ROOT` at module scope,
# unconditionally - unlike every deferred-import module elsewhere in
# this plan, this file is not being restructured (Chunk 15's own
# Rationale: forcing a decomposition here would relocate, not reduce,
# its complexity). Two different testing strategies are needed as a
# result: the real-ROOT end-to-end test below runs as a subprocess
# snippet (this repository's own pytest dev venv cannot import ROOT at
# all, real or fake, for a module-scope `import ROOT`), while the fast
# GetNsig()/GetNsigErr() regression test stubs sys.modules["ROOT"] with
# a trivial empty ModuleType purely so the module-level `import ROOT`
# resolves - it constructs the extractor and sets its state directly,
# never calling the real Extract(). (The follow-up lint-fix commit for
# this chunk also removed the file's original `from ROOT import *`,
# replacing its two wildcard-resolved names with explicit
# `ROOT.TH1D`/`ROOT.TH2D` - this module-level `import ROOT` is
# unaffected either way.)


def _run_real_root_snippet(snippet: str) -> subprocess.CompletedProcess[str]:
    probe = f"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

python - <<'INNER_PY'
{snippet}
INNER_PY
"""
    return subprocess.run(
        ["bash", "-lc", probe],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_snippet_ok(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, (
        "real-ROOT snippet failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "SNIPPET_OK" in completed.stdout, completed.stdout


# --- Extract()/accessors/WriteRoot(): real ROOT, real committed fixture ----


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_extract_and_accessors_and_writeroot_against_real_fixture(
    tmp_path: Path,
) -> None:
    # Reads exactly what production passes (run_fit.py:168 -
    # `fpe = FitParameterExtractor(wsfile=fitresultfile)`): the
    # already-committed FitResult_*.root, despite the "wsfile" name
    # (it is the fit-result file, not the workspace file - documented,
    # not renamed, in this chunk's activity-log entry and again in
    # Chunk 18's Known Limitations).
    assert (
        _FIXTURE_FITRESULT_FILE.exists()
    ), f"expected committed fixture missing: {_FIXTURE_FITRESULT_FILE}"

    outfile = tmp_path / "out.root"
    snippet = f"""
import sys
sys.path.insert(0, "python")
from ExtractFitParameters import FitParameterExtractor

fpe = FitParameterExtractor({str(_FIXTURE_FITRESULT_FILE)!r})
fpe.Extract()

h1_params = fpe.GetH1Params()
h2_cov = fpe.GetH2Cov()
h2_cor = fpe.GetH2Cor()
nsig = fpe.GetNsig()
nsig_err = fpe.GetNsigErr()

assert h1_params is not None
assert h1_params.GetNbinsX() > 0, h1_params.GetNbinsX()
assert h2_cov is not None
assert h2_cov.GetNbinsX() > 0, h2_cov.GetNbinsX()
assert h2_cor is not None
assert h2_cor.GetNbinsX() > 0, h2_cor.GetNbinsX()
# This fixture is a bkg-only fit (FitResult_anaFit_sixPar_bkgOnly.root) -
# confirmed directly by dumping floatParsFinal(): its 6 parameters are
# nbkg/p2/p3/p4/p5/p6, none containing the substring "nsig", so
# self.nsig/self.nsigErr genuinely stay None after a real Extract() here.
# This is the real, observed behavior against production's own fixture,
# not a gap in this test - pinned down exactly as such rather than
# assumed non-null.
assert nsig is None, nsig
assert nsig_err is None, nsig_err

fpe.WriteRoot({str(outfile)!r})
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))

    assert outfile.exists()

    verify_snippet = f"""
import ROOT
f = ROOT.TFile.Open({str(outfile)!r})
h1_params = f.Get("postfit_params")
h2_cov = f.Get("h2_cov")
h2_cor = f.Get("h2_cor")
assert h1_params, "postfit_params histogram missing from output file"
assert h1_params.GetEntries() > 0, h1_params.GetEntries()
assert h2_cov, "h2_cov histogram missing from output file"
assert h2_cov.GetEntries() > 0, h2_cov.GetEntries()
assert h2_cor, "h2_cor histogram missing from output file"
assert h2_cor.GetEntries() > 0, h2_cor.GetEntries()
f.Close()
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(verify_snippet))


# --- GetNsig()/GetNsigErr(): the `if not self.nsig:` falsiness quirk ------
#
# Preserved, not fixed: a genuinely-zero nsig (falsy) currently re-triggers
# Extract() on every single accessor call, unlike any other non-zero
# value. Pinned down exactly as-is, matching Chunk 5's own precedent for
# characterizing rather than silently cleaning up an existing quirk.


def _make_stubbed_extractor(monkeypatch: pytest.MonkeyPatch):
    fake_root_module = ModuleType("ROOT")
    monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)

    from python import ExtractFitParameters as extract_fit_parameters

    return extract_fit_parameters.FitParameterExtractor(wsfile="unused")


def test_getnsig_and_getnsigerr_refire_extract_when_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fpe = _make_stubbed_extractor(monkeypatch)
    fpe.nsig = 0.0
    fpe.nsigErr = 0.0

    call_count = {"n": 0}

    def _counting_extract():
        call_count["n"] += 1

    monkeypatch.setattr(fpe, "Extract", _counting_extract)

    fpe.GetNsig()
    fpe.GetNsig()
    assert call_count["n"] == 2, "a falsy (zero) nsig should re-trigger Extract() every call"

    call_count["n"] = 0
    fpe.GetNsigErr()
    fpe.GetNsigErr()
    assert call_count["n"] == 2, "a falsy (zero) nsigErr should re-trigger Extract() every call"


def test_getnsig_and_getnsigerr_do_not_refire_extract_when_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fpe = _make_stubbed_extractor(monkeypatch)
    fpe.nsig = 5.0
    fpe.nsigErr = 1.5

    call_count = {"n": 0}

    def _counting_extract():
        call_count["n"] += 1

    monkeypatch.setattr(fpe, "Extract", _counting_extract)

    fpe.GetNsig()
    fpe.GetNsig()
    assert call_count["n"] == 0, "a truthy (non-zero) nsig must not re-trigger Extract()"

    fpe.GetNsigErr()
    fpe.GetNsigErr()
    assert call_count["n"] == 0, "a truthy (non-zero) nsigErr must not re-trigger Extract()"
