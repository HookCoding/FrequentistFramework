"""Unit tests for the masking-branch group in run_anaFit.py (plan section 3, Group F).

This is the last group before run_anaFit()'s own coordinator role and main()'s split. Two of
these functions (_run_bumphunter, _run_limit) are pure command-string builders like Group A's;
_run_limit in particular is unreached by either locked analysis, so this exact-string test is
its only check anywhere in the repository.
"""

import json

import pytest

from conftest import FIXTURES

from run_anaFit import (
    _fit_accepted,
    _run_bumphunter,
    _read_bh_results,
    _masked_card_paths,
    _write_masked_cards,
    _run_limit,
)


# ---------------------------------------------------------------------------
# _fit_accepted
# ---------------------------------------------------------------------------

def test_fit_accepted_above_threshold():
    assert _fit_accepted(0.5, maskthreshold=0.01) is True


def test_fit_accepted_below_threshold():
    assert _fit_accepted(0.005, maskthreshold=0.01) is False


def test_fit_accepted_exactly_at_threshold_fails():
    """The comparison is a strict >, so a p-value exactly equal to the threshold does not pass -
    worth having on its own since this decides whether a fit is published as-is or re-fitted
    with a window masked."""
    assert _fit_accepted(0.01, maskthreshold=0.01) is False


# ---------------------------------------------------------------------------
# _run_bumphunter
# ---------------------------------------------------------------------------

def test_run_bumphunter_exact_command(monkeypatch):
    import run_anaFit
    calls = []
    monkeypatch.setattr(run_anaFit, "execute", lambda cmd: calls.append(cmd) or 0)

    _run_bumphunter("run/PostFit_anaFit_sixPar_bkgOnly.root", "J100yStar06", "run")

    assert len(calls) == 1
    assert calls[0] == (
        "source pyBumpHunter/pyBH_env/bin/activate; "
        "python3 python/FindBHWindow.py "
        "--inputfile run/PostFit_anaFit_sixPar_bkgOnly.root "
        "--bkghist J100yStar06_rebinned/postfit "
        "--datahist J100yStar06_rebinned/data "
        "--outputjson run/BHresults.json; "
        "deactivate"
    )
    # the non-background-only rebinned histograms - a real asymmetry with the p(chi2) gate,
    # which reads J100yStar06_bkgonly_rebinned. Not this function's mistake to fix.
    assert "bkgonly_rebinned" not in calls[0]


# ---------------------------------------------------------------------------
# _read_bh_results
# ---------------------------------------------------------------------------

def test_read_bh_results_matches_fixture(tmp_path):
    (tmp_path / "BHresults.json").write_text(
        (FIXTURES / "BHresults_J50.json").read_text()
    )

    got = _read_bh_results(str(tmp_path))

    assert got["MaskMin"] == 582.0
    assert got["MaskMax"] == 662.0
    assert got["BlindRange"] == "582,662"


def test_read_bh_results_truncated_file_raises(tmp_path):
    (tmp_path / "BHresults.json").write_text('{"MaskMin": 582.0, "MaskMax":')  # truncated

    with pytest.raises(json.JSONDecodeError):
        _read_bh_results(str(tmp_path))


# ---------------------------------------------------------------------------
# _masked_card_paths
# ---------------------------------------------------------------------------

def test_masked_card_paths_xml_and_root_suffixes():
    got = _masked_card_paths(
        tmptopfile="run/dijetTLA_fromTemplate.xml",
        tmpcategoryfile="run/category_dijetTLA_fromTemplate.xml",
        wsfile="run/ws.root",
        outputfile="run/FitResult_anaFit_sixPar_bkgOnly.root",
    )
    assert got == (
        "run/dijetTLA_fromTemplate_masked.xml",
        "run/category_dijetTLA_fromTemplate_masked.xml",
        "run/ws_masked.root",
        "run/FitResult_anaFit_sixPar_bkgOnly_masked.root",
    )


def test_masked_card_paths_pins_str_replace_hitting_a_directory_name_too():
    """These use str.replace, not a suffix operation, so a ".root" occurring in a directory
    component - not just the file's own extension - is replaced there too. Pinned as today's
    behaviour; neither driver's paths trigger it."""
    got = _masked_card_paths(
        tmptopfile="run/top.xml",
        tmpcategoryfile="run/category.xml",
        wsfile="run/x.root_dir/ws.root",
        outputfile="run/FitResult.root",
    )
    assert got[2] == "run/x_masked.root_dir/ws_masked.root"


# ---------------------------------------------------------------------------
# _write_masked_cards
# ---------------------------------------------------------------------------

def test_write_masked_cards_injects_blind_attributes(tmp_path):
    tmpcategoryfile = tmp_path / "category.xml"
    tmpcategoryfile.write_text('<Category Binning="20"/>\n')
    tmptopfile = tmp_path / "top.xml"
    # CategoryFile carries tmpcategoryfile's own path, exactly as _fill_top_card() wrote it.
    tmptopfile.write_text(
        '<Input CategoryFile="%s" OutputFile="run/ws.root"/>\n' % tmpcategoryfile
    )

    tmptopfilemasked = tmp_path / "top_masked.xml"
    tmpcategoryfilemasked = tmp_path / "category_masked.xml"

    _write_masked_cards(
        str(tmptopfilemasked), str(tmpcategoryfilemasked),
        str(tmptopfile), str(tmpcategoryfile),
        wsfile="run/ws.root", wsfilemasked="run/ws_masked.root",
        blindrange="582,662",
    )

    top_text = tmptopfilemasked.read_text()
    assert 'OutputFile="run/ws_masked.root" Blind="true"' in top_text
    assert str(tmpcategoryfile) not in top_text  # repointed at the masked category card
    assert str(tmpcategoryfilemasked) in top_text

    cat_text = tmpcategoryfilemasked.read_text()
    assert 'Binning="20" BlindRange="582,662"' in cat_text


# ---------------------------------------------------------------------------
# _run_limit
# ---------------------------------------------------------------------------

def test_run_limit_exact_command(monkeypatch):
    import run_anaFit
    calls = []
    monkeypatch.setattr(run_anaFit, "execute_checked",
                         lambda cmd, what, logfile=None: calls.append((cmd, what)) or 0)

    _run_limit("run/ws.root", "nsig_mean1000_width7.0", "run/FitResult_anaFit_sixPar_bkgOnly.root")

    assert len(calls) == 1
    cmd, what = calls[0]
    assert cmd == (
        "quickLimit -f run/ws.root -d combData -p nsig_mean1000_width7.0 --checkWS 1 "
        "--initialGuess 100000 --minTolerance 1E-06 --muScanPoints 20 --minStrat 2 --nllOffset 0 "
        "--GKIntegrator 1 -o run/Limits_anaFit_sixPar_bkgOnly.root"
    )
    assert what == "quickLimit on run/ws.root"
