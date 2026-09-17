#!/usr/bin/env python3
"""Reproducibility regression harness for the J50/J100 dijet TLA fits.

Subcommands land incrementally, see plans/2026-09-15-reproducibility-lock.md.
`selfcheck` tests the comparator below against synthetic data, without
touching ROOT or the ATLAS environment. `env` verifies the software stack
(sub-framework SHAs, the CVMFS LCG view, the pyBumpHunter venv) against the
files that already declare it, and records what cannot be pinned. `record`
captures a baseline (fit results, chi2/postfit, BumpHunter output, the four
input spectra's hashes and the software provenance) from an existing run
directory.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tolerance classes, plan section 4. "exact" is a marker; anything else is
# an {"rtol":..., "atol":...} dict.
TIGHT = {"rtol": 1e-6, "atol": 1e-8}
PVALUE = {"rtol": 1e-5, "atol": 1e-8}

TOLERANCE_BY_LEAF = {
    "minNll": TIGHT,
    "value": TIGHT,
    "error": TIGHT,
    "chi2": TIGHT,
    "chi2/ndof": TIGHT,
    "postfit": TIGHT,
    "data_integral": TIGHT,
    "pval": PVALUE,
    "global_Pval": PVALUE,
    "significance": PVALUE,
    "status": "exact",
    "covQual": "exact",
    "nbins": "exact",
    "npars": "exact",
    "ndof": "exact",
    "MaskMin": "exact",
    "MaskMax": "exact",
    "BlindRange": "exact",
    "seed": "exact",
    "npe": "exact",
    "directory_listing": "exact",
}


def flatten(obj, prefix=""):
    """Yield (dotted.path, leaf_value) for every leaf in a nested dict/list."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten(value, path)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from flatten(value, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def leaf_name(path):
    """The final component of a dotted path, with any list index stripped:
    `unmasked.postfit_bins.X_rebinned.postfit[3]` -> `postfit`."""
    return path.rsplit(".", 1)[-1].split("[", 1)[0]


def classify(path):
    # The default is "exact" deliberately: an unclassified leaf fails on the
    # last ULP rather than passing on a real move. compare() says so in the
    # failure text, because "exact match required" alone reads like a physics
    # finding when the real cause is a leaf nobody added to the table.
    return TOLERANCE_BY_LEAF.get(leaf_name(path), "exact")


def compare(baseline, candidate, tol_scale=1.0):
    """Compare two nested baseline/candidate structures.

    Returns a list of human-readable failure strings, reporting every
    mismatch rather than just the first; a missing or extra key is always
    a failure.
    """
    failures = []
    base_flat = dict(flatten(baseline))
    cand_flat = dict(flatten(candidate))

    for path in sorted(set(base_flat) - set(cand_flat)):
        failures.append(f"missing: {path!r} (baseline has {base_flat[path]!r})")
    for path in sorted(set(cand_flat) - set(base_flat)):
        failures.append(f"unexpected: {path!r} (candidate has {cand_flat[path]!r})")

    for path in sorted(set(base_flat) & set(cand_flat)):
        b, c = base_flat[path], cand_flat[path]
        cls = classify(path)

        numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (b, c))
        if cls == "exact" or not numeric:
            if b != c:
                # A type change is reported as such rather than reaching the
                # arithmetic below, where it used to raise TypeError three
                # frames deep instead of being a readable failure.
                if type(b) is not type(c):
                    why = f"type changed: {type(b).__name__} -> {type(c).__name__}"
                elif numeric and leaf_name(path) not in TOLERANCE_BY_LEAF:
                    # A float quantity nobody classified. Say so, or this
                    # reads as a physics move when it is a missing table
                    # entry - the coming refactor is expected to add leaves.
                    why = (f"compared exactly: leaf {leaf_name(path)!r} has no tolerance class. "
                           f"If this is a float quantity, add one to TOLERANCE_BY_LEAF")
                else:
                    why = "exact match required"
                failures.append(f"{path}: expected {b!r}, got {c!r} ({why})")
            continue

        if math.isnan(b) or math.isnan(c):
            # Every comparison against NaN is False, so the tolerance test
            # below would silently pass a NaN candidate against any baseline.
            if math.isnan(b) != math.isnan(c):
                failures.append(f"{path}: expected {b!r}, got {c!r} (NaN mismatch)")
            continue

        rtol, atol = cls["rtol"] * tol_scale, cls["atol"] * tol_scale
        diff = abs(c - b)
        if diff > atol + rtol * abs(b):
            failures.append(
                f"{path}: expected {b!r}, got {c!r} "
                f"(|diff|={diff:.3g} > atol {atol:.3g} + rtol*|baseline| {rtol * abs(b):.3g})"
            )

    return failures


class _Text:
    """A read_text()-only stand-in for a Path, so the install.sh/setup_lxplus.sh/
    pyvenv.cfg parsers below can be unit-tested against synthetic strings with
    no real file on disk."""

    def __init__(self, text):
        self.text = text

    def read_text(self):
        return self.text


def cmd_selfcheck(args):
    """Exercise compare() against synthetic data covering every tolerance
    class, a missing key, and an extra key."""
    baseline = {
        "fitResult": {
            "minNll": 1259.1119375388664,
            "status": 0,
            "covQual": 3,
            "params": {"nbkg": {"value": 7.6524e8, "error": 1.2e4}},
        },
        "chi2": {"J100yStar06_rebinned": {"chi2": 75.4, "chi2/ndof": 1.478,
                                           "nbins": 57, "npars": 6,
                                           "ndof": 51, "pval": 0.0149}},
        "postfit_bins": {"J100yStar06_rebinned": {"postfit": [1.0, 2.0, 3.0],
                                                    "data_integral": 6.0}},
        "directory_listing": ["FitResult_anaFit_sixPar_bkgOnly.root",
                               "PostFit_anaFit_sixPar_bkgOnly.root"],
    }

    # Should PASS: every tight/pvalue float nudged well inside tolerance.
    passing = {
        "fitResult": {
            "minNll": 1259.1119375388664 + 1e-9,
            "status": 0,
            "covQual": 3,
            "params": {"nbkg": {"value": 7.6524e8, "error": 1.2e4}},
        },
        "chi2": {"J100yStar06_rebinned": {"chi2": 75.4, "chi2/ndof": 1.478,
                                           "nbins": 57, "npars": 6,
                                           "ndof": 51, "pval": 0.0149 + 1e-9}},
        "postfit_bins": {"J100yStar06_rebinned": {"postfit": [1.0, 2.0, 3.0],
                                                    "data_integral": 6.0}},
        "directory_listing": ["FitResult_anaFit_sixPar_bkgOnly.root",
                               "PostFit_anaFit_sixPar_bkgOnly.root"],
    }
    failures = compare(baseline, passing)
    assert failures == [], f"expected a clean pass, got: {failures}"

    # Should FAIL on the exact, tight and pvalue classes at once, plus a
    # missing key and an extra key.
    failing = {
        "fitResult": {
            "minNll": 1259.1119375388664 + 1.0,  # tight, way outside
            "status": 1,                          # exact, mismatched
            "params": {"nbkg": {"value": 7.6524e8, "error": 1.2e4}},
        },
        "chi2": {"J100yStar06_rebinned": {"chi2": 75.4, "chi2/ndof": 1.478,
                                           "nbins": 57, "npars": 6,
                                           "ndof": 51, "pval": 0.02}},  # pvalue, outside
        "postfit_bins": {"J100yStar06_rebinned": {"postfit": [1.0, 2.0, 3.0],
                                                    "data_integral": 6.0}},
        "directory_listing": ["FitResult_anaFit_sixPar_bkgOnly.root",
                               "PostFit_anaFit_sixPar_bkgOnly.root"],
        "extra_key": 1,
    }  # fitResult.covQual is dropped above: a missing key
    failures = compare(baseline, failing)
    failure_text = "\n".join(failures)
    for expected in ("minNll", "status", "pval", "missing:", "unexpected:"):
        assert expected in failure_text, f"expected {expected!r} among failures, got:\n{failure_text}"
    assert len(failures) == 5, f"expected exactly 5 failures, got {len(failures)}:\n{failure_text}"

    # --tol-scale scaling: the same near-miss must fail at the default scale
    # and pass once the tolerance is widened.
    tight_baseline = {"chi2": {"c": {"pval": 0.0149}}}
    tight_candidate = {"chi2": {"c": {"pval": 0.0149015}}}
    at_default = compare(tight_baseline, tight_candidate)
    assert at_default != [], "expected this near-miss to fail at the default tolerance"
    at_100x = compare(tight_baseline, tight_candidate, tol_scale=100.0)
    assert at_100x == [], f"expected tol_scale=100 to absorb the same difference, got: {at_100x}"

    # NaN is a mismatch in either direction and a match only against itself:
    # every comparison against NaN is False, so an unguarded tolerance test
    # passes a NaN candidate against any baseline value (KNOWN_ISSUES 22).
    nan_baseline = {"fitResult": {"minNll": 1259.11}}
    assert compare(nan_baseline, {"fitResult": {"minNll": float("nan")}}) != [], \
        "a NaN candidate must not pass against a real baseline value"
    assert compare({"fitResult": {"minNll": float("nan")}}, nan_baseline) != [], \
        "a real candidate must not pass against a NaN baseline value"
    assert compare({"fitResult": {"minNll": float("nan")}},
                   {"fitResult": {"minNll": float("nan")}}) == [], "NaN must match itself"

    # A leaf whose type changes is a readable failure, not a TypeError raised
    # out of the arithmetic (KNOWN_ISSUES 26).
    type_changed = compare({"fitResult": {"minNll": 1259.11}}, {"fitResult": {"minNll": "nope"}})
    assert len(type_changed) == 1 and "type changed" in type_changed[0], \
        f"expected a type-change failure, got: {type_changed}"

    # An unclassified float leaf is compared exactly - the safe direction -
    # but the failure has to name the missing tolerance class, or it reads as
    # a physics move (KNOWN_ISSUES 34).
    unclassified = compare({"fitResult": {"newQuantity": 1.0}},
                           {"fitResult": {"newQuantity": 1.0 + 1e-15}})
    assert len(unclassified) == 1 and "no tolerance class" in unclassified[0], \
        f"expected the failure to name the missing tolerance class, got: {unclassified}"
    assert "newQuantity" in unclassified[0], f"expected the leaf to be named, got: {unclassified}"
    # A classified leaf of the same shape must still pass on the same nudge.
    assert compare({"fitResult": {"minNll": 1.0}}, {"fitResult": {"minNll": 1.0 + 1e-15}}) == [], \
        "a classified leaf must still compare within tolerance"

    print("PASS: comparator selfcheck (tolerance classes, missing/extra keys, tol_scale scaling, "
          "NaN, type changes, unclassified leaves)")

    # compare_binary_digests: no baseline, match, mismatch, missing digest.
    observed = {"a/bin": "aaaa", "b/bin": "bbbb"}
    assert compare_binary_digests(observed, None) == [], "no baseline means nothing to compare"
    results = compare_binary_digests(observed, {"a/bin": "aaaa", "b/bin": "bbbb"})
    assert all(ok for _, ok, _ in results), f"expected both digests to match, got: {results}"
    results = compare_binary_digests(observed, {"a/bin": "aaaa", "b/bin": "cccc"})
    by_name = {name: (ok, detail) for name, ok, detail in results}
    assert by_name["binary matches baseline: a/bin"][0], "a/bin should still match"
    mismatch_ok, mismatch_detail = by_name["binary matches baseline: b/bin"]
    assert not mismatch_ok and "cccc" in mismatch_detail, f"expected a mismatch detail, got: {results}"
    results = compare_binary_digests(observed, {"a/bin": "aaaa"})
    missing_ok, missing_detail = dict((n, (o, d)) for n, o, d in results)["binary matches baseline: b/bin"]
    assert not missing_ok and "no digest" in missing_detail, f"expected a missing-digest failure, got: {results}"

    print("PASS: compare_binary_digests selfcheck (match, mismatch, missing digest, no baseline)")

    # compare_recorded_pins: no baseline, agreement, a drifted SHA, an extra
    # pin the baseline never recorded.
    live_pins = {"quickFit": "a" * 40, "RooFitExtensions": {"quickFit": "b" * 40},
                 "active_view": "LCG_102a x86_64-centos9-gcc11-opt"}
    assert compare_recorded_pins(live_pins, None) == [], "no baseline means nothing to compare"
    agreed = compare_recorded_pins(live_pins, dict(live_pins))
    assert len(agreed) == 1 and agreed[0][1], f"expected identical pins to pass, got: {agreed}"
    drifted = compare_recorded_pins(live_pins, {**live_pins, "quickFit": "c" * 40})
    assert len(drifted) == 1 and not drifted[0][1], f"expected a drifted pin to fail, got: {drifted}"
    assert "quickFit" in drifted[0][2] and "record --force" in drifted[0][2], \
        f"expected the failure to name the pin and the way out, got: {drifted}"
    # A nested RooFitExtensions SHA must be reached too, not just top-level keys.
    nested = compare_recorded_pins(live_pins,
                                   {**live_pins, "RooFitExtensions": {"quickFit": "d" * 40}})
    assert len(nested) == 1 and not nested[0][1] and "RooFitExtensions" in nested[0][2], \
        f"expected a nested pin drift to fail, got: {nested}"
    extra = compare_recorded_pins(live_pins, {k: v for k, v in live_pins.items() if k != "quickFit"})
    assert len(extra) == 1 and not extra[0][1] and "unexpected" in extra[0][2], \
        f"expected a pin absent from the baseline to fail, got: {extra}"

    print("PASS: compare_recorded_pins selfcheck (agreement, drifted SHA, nested SHA, extra pin, "
          "no baseline)")

    # parse_install_sh_pins: a blank line between `cd` and its checkout (as
    # pyBumpHunter's own block has), the literal `cd $x` from install.sh's
    # build loop (must not produce a spurious pin), and `cd ..` immediately
    # followed by a checkout line (must never be read as a directory name).
    synthetic_install_sh = """\
cd xmlAnaWSBuilder
git checkout 6b84050f3c0206a6f30eb40b103cc101e68505cc
cd ..
git checkout deadbeefdeadbeefdeadbeefdeadbeefdeadbeef

cd pyBumpHunter

git checkout 91f49a622bd77622edb02a1a2788fc12835e5b72
cd ..

for x in xmlAnaWSBuilder quickFit; do
  cd $x
  . setup_lxplus.sh
  cd ../..
done
"""
    pins = parse_install_sh_pins(_Text(synthetic_install_sh))
    assert pins == {
        "xmlAnaWSBuilder": "6b84050f3c0206a6f30eb40b103cc101e68505cc",
        "pyBumpHunter": "91f49a622bd77622edb02a1a2788fc12835e5b72",
    }, f"unexpected pins: {pins}"
    assert "$x" not in pins, "literal `cd $x` must not produce a pin"
    assert ".." not in pins, "`cd ..` must never be read as a directory name"

    # Stepping out of a directory voids a pending pairing: `cd quickFit` then
    # `cd ..` then a checkout must pin nothing, not pin quickFit to a SHA the
    # script checks out somewhere else entirely (KNOWN_ISSUES 36).
    stepped_out = parse_install_sh_pins(_Text(
        "cd quickFit\ncd ..\n" + f"git checkout {'e' * 40}\n"))
    assert stepped_out == {}, f"a checkout after `cd ..` must pin nothing, got: {stepped_out}"
    stepped_out_twice = parse_install_sh_pins(_Text(
        "cd quickFit\ncd build\ncd ../..\n" + f"git checkout {'f' * 40}\n"))
    assert stepped_out_twice == {}, f"`cd ../..` must void the pairing too, got: {stepped_out_twice}"

    # parse_lsetup_view: extracts the view, and is None when absent.
    view = parse_lsetup_view(_Text('lsetup "views LCG_102a x86_64-centos9-gcc11-opt"\n'))
    assert view == "LCG_102a x86_64-centos9-gcc11-opt", f"unexpected view: {view!r}"
    assert parse_lsetup_view(_Text("# no lsetup line here\n")) is None

    # parse_pyvenv_cfg: key = value pairs, blank/malformed lines ignored.
    cfg = parse_pyvenv_cfg(_Text("home = /some/path\nversion = 3.9.12\n\nnot-a-pair\n"))
    assert cfg == {"home": "/some/path", "version": "3.9.12"}, f"unexpected cfg: {cfg}"

    print("PASS: parser selfcheck (install.sh pins, lsetup view, pyvenv.cfg)")
    return 0


# --- env: verify the stack, without inventing a new source of truth -------
#
# Design note: unlike selfcheck's baseline/candidate JSON, most of env's
# checks either compare two peer declarations that must mutually agree
# (the three setup_lxplus.sh files), or assert a list is empty (no dirty
# tracked files), or have no "expected" value to compare against at all
# (cmake/numpy/scipy/uproot versions, which plan section 1 says to record
# rather than assert). None of that is the nested-baseline-vs-candidate
# shape compare() was built for, so env reports its own (name, ok, detail)
# checks directly instead of forcing everything through flatten()/compare().

FRAMEWORKS = ["xmlAnaWSBuilder", "quickFit", "workspaceCombiner", "pyBumpHunter"]
ROOFIT_FRAMEWORKS = ["xmlAnaWSBuilder", "quickFit", "workspaceCombiner"]
EXPECTED_PYBH_PYTHON_VERSION = "3.9.12"


def _git(args, cwd):
    return subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True)


def parse_install_sh_pins(install_sh):
    """Pair each `cd <dir>` with the checkout SHA that follows it."""
    pins = {}
    current_dir = None
    for line in install_sh.read_text().splitlines():
        line = line.strip()
        m = re.match(r"cd\s+(\S+)$", line)
        if m:
            # A `cd ..`/`cd ../..` leaves the directory it was in, so any
            # pending pairing is void: keeping it would attribute a later
            # checkout to a clone the script has already stepped out of.
            current_dir = None if m.group(1).startswith("..") else m.group(1)
            continue
        m = re.match(r"git checkout\s+([0-9a-f]{40})$", line)
        if m and current_dir:
            pins[current_dir] = m.group(1)
            current_dir = None
    return pins


def parse_checkout_sha(script_path):
    m = re.search(r"git checkout\s+([0-9a-f]{40})", script_path.read_text())
    return m.group(1) if m else None


def parse_lsetup_view(setup_lxplus_path):
    m = re.search(r'lsetup\s+"views\s+([^"]+)"', setup_lxplus_path.read_text())
    return m.group(1).strip() if m else None


def parse_pyvenv_cfg(pyvenv_cfg_path):
    cfg = {}
    for line in pyvenv_cfg_path.read_text().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg


def find_pybumphunter_egg_version(pyBH_env_dir):
    """The installed egg's version string, or a string saying why there isn't
    exactly one. Two eggs in the venv is itself the finding - picking one and
    reporting it as 'the' version is how a stale egg hides behind a fresh one."""
    eggs = sorted(pyBH_env_dir.glob("lib/python*/site-packages/pyBumpHunter-*.egg"))
    if not eggs:
        return None
    if len(eggs) > 1:
        return f"ambiguous: {len(eggs)} eggs installed ({', '.join(e.name for e in eggs)})"
    m = re.match(r"pyBumpHunter-(.+)-py3\.\d+\.egg$", eggs[0].name)
    return m.group(1) if m else eggs[0].name


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atlas_probe(script, timeout=90):
    """Run a snippet after sourcing the ATLAS/CVMFS environment.

    Returns (stdout, error): error is None on success, a short string on
    failure. Never raises - plan section 1 records these values rather
    than asserting them, precisely because they cannot be pinned from
    this repository.
    """
    preamble = "setupATLAS >/dev/null 2>&1\n"
    try:
        proc = subprocess.run(
            ["bash", "-c", preamble + script],
            text=True, capture_output=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return None, str(exc)
    if proc.returncode != 0:
        return None, (proc.stderr.strip()[-500:] or f"exit {proc.returncode}")
    return proc.stdout.strip(), None


def _lcg_view_dir(view):
    return Path("/cvmfs/sft.cern.ch/lcg/views", *view.split())


def _view_binary_version(view, binary, *version_args):
    """Version string of a binary read directly from inside the LCG view,
    bypassing `lsetup`: in this session lsetup's PATH edits never take
    effect non-interactively, so a probe like `lsetup views; cmake
    --version` silently reports /usr/bin's cmake instead of the view's
    (see KNOWN_ISSUES.md). Going straight to the view's own bin/ is what
    the framework's compiled binaries actually built against, and is both
    faster and correct where the lsetup-based probe was not."""
    exe = _lcg_view_dir(view) / "bin" / binary
    if not exe.is_file():
        return f"unavailable (no {exe})"
    proc = subprocess.run([str(exe), *version_args], text=True, capture_output=True, timeout=30)
    if proc.returncode != 0:
        return f"unavailable (exit {proc.returncode}: {proc.stderr.strip()[-200:]})"
    return proc.stdout.strip().splitlines()[0]


def resolve_cmake_version(view):
    return _view_binary_version(view, "cmake", "--version")


def resolve_root_version(view):
    return _view_binary_version(view, "root-config", "--version")


def resolve_bumphunter_pypackages(pyBH_env_dir):
    """Import numpy/scipy/uproot exactly as python/FindBHWindow.py's own
    activation line does (source pyBH_env/bin/activate, then python3) -
    but preceded by the real scripts/setup_buildAndFit.sh, not a bare
    `lsetup views` line. A bare line leaves PYTHONPATH empty in this
    session; the real chain (both sub-frameworks' setup_lxplus.sh) does
    not - confirmed by rerunning this probe both ways (see CHANGELOG)."""
    script = f'''\
cd "{REPO_ROOT}"
source scripts/setup_buildAndFit.sh >/dev/null 2>&1
source "{pyBH_env_dir}/bin/activate"
python3 <<'PYEOF'
import importlib
for m in ("numpy", "scipy", "uproot"):
    try:
        mod = importlib.import_module(m)
        print(m, getattr(mod, "__version__", "?"))
    except Exception as e:
        print(m, "unavailable:", e)
PYEOF
deactivate
'''
    out, err = _atlas_probe(script, timeout=240)
    if out is None:
        return {pkg: f"probe failed ({err})" for pkg in ("numpy", "scipy", "uproot")}
    versions = {}
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            versions[parts[0]] = parts[1]
    return versions


def run_env_checks(root=REPO_ROOT):
    """Run every check in plan section 1.

    Returns (checks, pins, recorded): checks is a list of (name, ok, detail)
    covering every assertable pin; pins is what those pins actually resolved
    to (for `record`'s provenance block); recorded is a dict of observe-only
    values that plan section 1 says to record without asserting.
    """
    checks = []

    def check(name, ok, detail):
        checks.append((name, ok, detail))

    install_pins = parse_install_sh_pins(root / "install.sh")

    observed_heads = {}
    for fw in FRAMEWORKS:
        expected = install_pins.get(fw)
        clone_dir = root / fw
        if expected is None:
            check(f"install.sh pin: {fw}", False, "no cd/checkout pair found in install.sh")
            continue
        if not clone_dir.is_dir():
            check(f"install.sh pin: {fw}", False, f"{fw}/ does not exist (not cloned)")
            continue
        actual = _git(["rev-parse", "HEAD"], clone_dir).stdout.strip()
        observed_heads[fw] = actual or None
        check(f"install.sh pin: {fw}", actual == expected,
              f"install.sh pins {expected}, HEAD is {actual or '(git rev-parse failed)'}")

    roofit_shas = {}
    for fw in ROOFIT_FRAMEWORKS:
        script_path = root / fw / "scripts" / "install_roofitext.sh"
        if not script_path.is_file():
            check(f"RooFitExtensions pin: {fw}", False, f"{script_path} does not exist")
            continue
        expected = parse_checkout_sha(script_path)
        rfe_dir = root / fw / "RooFitExtensions"
        if not rfe_dir.is_dir():
            check(f"RooFitExtensions pin: {fw}", False, f"{rfe_dir} does not exist (not built)")
            continue
        actual = _git(["rev-parse", "HEAD"], rfe_dir).stdout.strip()
        roofit_shas[fw] = actual or None
        check(f"RooFitExtensions pin: {fw}", actual == expected,
              f"{script_path.relative_to(root)} pins {expected}, HEAD is {actual or '(git rev-parse failed)'}")

    if len(set(roofit_shas.values())) > 1:
        check("RooFitExtensions pin agreement", False, f"sub-frameworks disagree: {roofit_shas}")

    views = {}
    for fw in ROOFIT_FRAMEWORKS:
        setup_path = root / fw / "setup_lxplus.sh"
        if not setup_path.is_file():
            check(f"lsetup view declared: {fw}", False, f"{setup_path} does not exist")
            continue
        view = parse_lsetup_view(setup_path)
        views[fw] = view
        check(f"lsetup view declared: {fw}", view is not None, f"{setup_path.relative_to(root)}: {view!r}")

    distinct_views = {v for v in views.values() if v}
    agreed_view = next(iter(distinct_views)) if len(distinct_views) == 1 else None
    check("lsetup view agreement", agreed_view is not None,
          f"all three agree on {agreed_view!r}" if agreed_view else f"sub-frameworks disagree: {views}")

    pyvenv_path = root / "pyBumpHunter" / "pyBH_env" / "pyvenv.cfg"
    if not pyvenv_path.is_file():
        check("pyBH_env pyvenv.cfg", False, f"{pyvenv_path} does not exist (venv not created)")
    else:
        cfg = parse_pyvenv_cfg(pyvenv_path)
        home = cfg.get("home", "")
        version = cfg.get("version", "")
        view_in_home = agreed_view is not None and all(part in home for part in agreed_view.split())
        check("pyBH_env venv matches LCG view", view_in_home,
              f"pyvenv.cfg home={home!r}, expected view {agreed_view!r}")
        check("pyBH_env python version", version == EXPECTED_PYBH_PYTHON_VERSION,
              f"pyvenv.cfg version={version!r}, expected {EXPECTED_PYBH_PYTHON_VERSION!r}")

    # The egg carries the short SHA of the commit it was built from, so the
    # expectation is derived from install.sh's own pin rather than from a
    # constant here: a deliberate pin bump then fails with "the venv needs
    # rebuilding", not with "the egg disagrees with a number nobody updated".
    pyBH_env_dir = root / "pyBumpHunter" / "pyBH_env"
    egg_version = find_pybumphunter_egg_version(pyBH_env_dir) if pyBH_env_dir.is_dir() else None
    pybh_pin = install_pins.get("pyBumpHunter")
    expected_egg_suffix = f"+g{pybh_pin[:7]}" if pybh_pin else None
    check("pyBumpHunter installed egg version",
          bool(expected_egg_suffix) and isinstance(egg_version, str)
          and egg_version.endswith(expected_egg_suffix),
          f"installed egg is {egg_version!r}, expected one built from install.sh's pin "
          f"(version ending {expected_egg_suffix!r})" if expected_egg_suffix
          else f"installed egg is {egg_version!r}, but install.sh declares no pyBumpHunter pin")

    for fw in FRAMEWORKS:
        clone_dir = root / fw
        if not clone_dir.is_dir():
            continue
        dirty = [line for line in _git(["status", "--porcelain"], clone_dir).stdout.splitlines()
                 if not line.startswith("??")]
        check(f"no modified tracked files: {fw}", not dirty, "clean" if not dirty else "\n".join(dirty))

    binary_hashes = {}
    for rel_path in ("xmlAnaWSBuilder/build/bin/XMLReader", "quickFit/build/quickFit"):
        full = root / rel_path
        if full.is_file():
            binary_hashes[rel_path] = sha256_of(full)
            check(f"binary present: {rel_path}", True, f"sha256={binary_hashes[rel_path]}")
        else:
            check(f"binary present: {rel_path}", False, "not built")

    recorded = {"binary_sha256": binary_hashes}
    if agreed_view:
        recorded["cmake_version"] = resolve_cmake_version(agreed_view)
        recorded["root_version"] = resolve_root_version(agreed_view)
        recorded["bumphunter_pypackages"] = resolve_bumphunter_pypackages(pyBH_env_dir)
    else:
        recorded["cmake_version"] = "skipped (no agreed LCG view)"
        recorded["root_version"] = "skipped (no agreed LCG view)"
        recorded["bumphunter_pypackages"] = {}

    pins = {fw: observed_heads.get(fw) for fw in FRAMEWORKS}
    pins["RooFitExtensions"] = roofit_shas
    pins["active_view"] = agreed_view
    pins["pyBH_python_version"] = parse_pyvenv_cfg(pyvenv_path).get("version") if pyvenv_path.is_file() else None
    pins["pyBumpHunter_egg_version"] = egg_version

    return checks, pins, recorded


def compare_binary_digests(observed, baseline_digests):
    """Compare observed {rel_path: sha256} against a baseline provenance's
    own binary_sha256 dict. baseline_digests is None when no baseline exists
    yet, in which case there is nothing to compare and this returns []."""
    if baseline_digests is None:
        return []
    results = []
    for rel_path, digest in sorted(observed.items()):
        baseline_digest = baseline_digests.get(rel_path)
        if baseline_digest is None:
            results.append((f"binary matches baseline: {rel_path}", False,
                             f"sha256={digest}, but the baseline provenance has no digest "
                             f"recorded for this path"))
        elif digest == baseline_digest:
            results.append((f"binary matches baseline: {rel_path}", True, f"sha256={digest}"))
        else:
            results.append((f"binary matches baseline: {rel_path}", False,
                             f"sha256={digest}, baseline recorded {baseline_digest}. If this "
                             f"binary was deliberately rebuilt, re-cut the baseline with "
                             f"'record --force --reason \"...\"' rather than ignoring this."))
    return results


def compare_recorded_pins(observed, baseline_pins):
    """Compare the live pins against a baseline provenance's own `pins` block.

    Reuses compare(): every leaf here is a SHA, a view name or a version
    string, which classify() already handles as an exact match, and it
    reports a missing or extra key too. baseline_pins is None when there is
    no baseline to compare against, in which case this returns [].

    This closes the last of the three provenance blocks that was recorded and
    never read back. `versions` warns (plan section 1: it cannot be enforced)
    and `binary_sha256` fails (KNOWN_ISSUES 12); pins belong with the latter -
    they *are* the enforceable part of the stack, and a baseline whose pins no
    longer describe the tree has stopped saying which software produced its
    numbers."""
    if baseline_pins is None:
        return []
    failures = compare(baseline_pins, observed)
    if not failures:
        return [("pins match baseline", True, "every recorded pin agrees with this tree")]
    return [("pins match baseline", False, "\n".join(failures) + "\n  If install.sh's pins "
             "(or a sub-framework's RooFitExtensions pin, the LCG view or the pyBumpHunter "
             "venv) were deliberately changed, re-cut the baseline with 'record --force "
             "--reason \"...\"' rather than ignoring this.")]


def _report_env(checks, recorded, pins):
    """Print every env check plus the recorded-but-unasserted versions and
    any drift from each existing baseline's provenance (shared by `env` and
    `check`, which runs the same checks before touching any fit). Returns
    True iff every assertable check passed."""
    baseline_paths = sorted((REPO_ROOT / "tests").glob("baseline_*.json"))
    provenances = []
    for path in baseline_paths:
        # A hand-edited or half-written baseline is named and skipped rather
        # than raising KeyError/ValueError from three frames down.
        try:
            provenance = json.loads(path.read_text()).get("provenance")
        except ValueError as exc:
            print(f"WARNING: {path.name} is not valid JSON ({exc}) - skipping its comparisons")
            continue
        missing = [k for k in ("versions", "binary_sha256", "pins")
                   if not isinstance(provenance, dict) or k not in provenance]
        if missing:
            print(f"WARNING: {path.name} has no usable provenance block "
                  f"(missing {', '.join(missing) if isinstance(provenance, dict) else 'provenance'})"
                  " - skipping its comparisons")
            continue
        provenances.append((path.name, provenance))

    for name, provenance in provenances:
        against_baseline = (compare_binary_digests(recorded["binary_sha256"], provenance["binary_sha256"])
                            + compare_recorded_pins(pins, provenance["pins"]))
        checks = checks + [(f"{check_name} ({name})", ok, detail)
                           for check_name, ok, detail in against_baseline]

    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    print("\nRecorded (not asserted, plan section 1 - cannot be pinned from this repository):")
    print(f"  root: {recorded['root_version']}")
    print(f"  cmake: {recorded['cmake_version']}")
    for pkg, value in recorded["bumphunter_pypackages"].items():
        print(f"  {pkg} (as seen by the BumpHunter step): {value}")
    for rel_path, digest in recorded["binary_sha256"].items():
        print(f"  sha256 {rel_path}: {digest}")

    live_versions = {"root_version": recorded["root_version"], "cmake_version": recorded["cmake_version"],
                      **recorded["bumphunter_pypackages"]}
    if not provenances:
        print("\nNo baseline exists yet - nothing to compare those versions against.")
    else:
        for name, provenance in provenances:
            reference = provenance["versions"]
            diffs = {k: (reference.get(k), live_versions.get(k))
                     for k in set(reference) | set(live_versions)
                     if reference.get(k) != live_versions.get(k)}
            if diffs:
                print(f"\nWARNING: versions differ from {name}'s provenance (non-fatal):")
                for k, (was, now) in sorted(diffs.items()):
                    print(f"  {k}: baseline={was!r} now={now!r}")
            else:
                print(f"\nVersions match {name}'s provenance.")

    failed = [c for c in checks if not c[1]]
    print()
    if failed:
        print(f"FAIL: {len(failed)}/{len(checks)} environment checks failed")
    else:
        print(f"PASS: all {len(checks)} environment checks passed")
    return not failed


def cmd_env(args):
    checks, pins, recorded = run_env_checks()
    return 0 if _report_env(checks, recorded, pins) else 1


# --- record: capture a baseline from an existing run directory -----------

ANALYSES = {
    "J100": {
        "default_dir": "run/run_481_3000_sixPar",
        "driver": "scripts/run_anaFit_run2.sh",
        "stem": "anaFit_sixPar_bkgOnly",
        "inputs": ["Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
                   "Input/data/dijetTLA/fullRun2TLAJ100mjj.root"],
    },
    "J50": {
        "default_dir": "run/run_J50_302_2997_sixPar",
        "driver": "scripts/run_anaFit_run2_J50.sh",
        "stem": "anaFit_sixPar_bkgOnly",
        "inputs": ["Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
                   "Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root"],
    },
}


def _import_root():
    """import ROOT with a diagnosable error instead of a bare traceback three
    frames deep in extract_fit_result/extract_postfit. The plain lxplus
    system python3 has PyROOT importable with no setup at all (see the
    README's Reproducibility section) - but only when nothing upstream in
    the invoking shell put a different python3 first on $PATH, e.g. an
    activated pyBumpHunter/pyBH_env venv (which carries no ROOT bindings at
    all, only the pyBumpHunter egg) or a sourced ATLAS/lsetup environment."""
    try:
        import ROOT
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"ERROR: {sys.executable} has no ROOT module ({exc}). record/check need a "
            "python3 with PyROOT already importable - the plain lxplus system python3 has "
            "this with no setup. Deactivate any active virtualenv (check $VIRTUAL_ENV) and "
            "unset any sourced ATLAS/lsetup environment in this shell, then re-run."
        )
    return ROOT


def extract_fit_result(path):
    """fitResult's minNll/status/covQual and every floatParsFinal() entry."""
    ROOT = _import_root()
    f = ROOT.TFile.Open(str(path))
    fr = f.Get("fitResult")
    pars = fr.floatParsFinal()
    params = {pars.at(i).GetName(): {"value": pars.at(i).getVal(), "error": pars.at(i).getError()}
              for i in range(pars.getSize())}
    result = {"minNll": fr.minNll(), "status": fr.status(), "covQual": fr.covQual(), "params": params}
    f.Close()
    return result


def extract_postfit(path):
    """The 6-bin chi2 block for every TDirectory, plus postfit bins and the
    data integral for the two *_rebinned directories only (plan section 3).
    compare() catches a missing or renamed directory as a missing/unexpected
    key, so nothing here needs to know the directory names in advance."""
    ROOT = _import_root()
    f = ROOT.TFile.Open(str(path))
    chi2, postfit_bins = {}, {}
    seen = set()
    for key in f.GetListOfKeys():
        name = key.GetName()
        if name in seen:
            continue  # ROOT key cycles can list one name more than once
        seen.add(name)
        cls = ROOT.TClass.GetClass(key.GetClassName())
        if cls is None or not cls.InheritsFrom("TDirectory"):
            continue
        d = f.Get(name)
        h = d.Get("chi2")
        chi2[name] = {h.GetXaxis().GetBinLabel(i): h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1)}
        if name.endswith("_rebinned"):
            postfit, data = d.Get("postfit"), d.Get("data")
            postfit_bins[name] = {
                "postfit": [postfit.GetBinContent(i) for i in range(1, postfit.GetNbinsX() + 1)],
                "data_integral": data.Integral(),
            }
    f.Close()
    return chi2, postfit_bins


def extract_bhresults(path):
    bh = json.loads(path.read_text())
    r = bh["pyBHresult"]
    return {"MaskMin": bh["MaskMin"], "MaskMax": bh["MaskMax"], "BlindRange": bh["BlindRange"],
            "global_Pval": r["global_Pval"], "significance": r["significance"],
            "seed": r["seed"], "npe": r["npe"]}


def extract_variant(folder, stem, masked):
    """None if the fit set (unmasked or masked) is not present in folder."""
    suffix = "_masked" if masked else ""
    fit_path = folder / f"FitResult_{stem}{suffix}.root"
    post_path = folder / f"PostFit_{stem}{suffix}.root"
    if not fit_path.is_file() or not post_path.is_file():
        return None
    chi2, postfit_bins = extract_postfit(post_path)
    variant = {"fitResult": extract_fit_result(fit_path), "chi2": chi2, "postfit_bins": postfit_bins}
    if masked:
        bh_path = folder / "BHresults.json"
        if bh_path.is_file():
            variant["bumphunter"] = extract_bhresults(bh_path)
    return variant


def cmd_record(args):
    spec = ANALYSES[args.analysis]
    folder = Path(args.dir) if args.dir else REPO_ROOT / spec["default_dir"]
    if not folder.is_dir():
        print(f"FAIL: {folder} does not exist")
        return 1

    baseline_path = REPO_ROOT / "tests" / f"baseline_{args.analysis}.json"
    if baseline_path.exists() and not args.force:
        print(f"FAIL: {baseline_path} already exists. Re-cut deliberately with --force --reason \"...\".")
        return 1
    if args.force and not args.reason:
        print("FAIL: --force requires --reason \"...\" explaining why this baseline is being re-cut")
        return 1

    env_checks, pins, recorded = run_env_checks()
    failed_checks = [c for c in env_checks if not c[1]]
    # Printed whether or not --force is given. Re-cutting an existing baseline
    # always needs --force, so gating the *report* on it (as this used to)
    # meant the only route anyone is documented to take was also the one that
    # never showed what was wrong with the tree it was cutting from.
    if failed_checks:
        print(f"{len(failed_checks)}/{len(env_checks)} environment check(s) failed:")
        for name, ok, detail in failed_checks:
            print(f"  [FAIL] {name}: {detail}")
        if not args.force:
            print("FAIL: refusing to record a baseline against a pin this tree does not meet. "
                  "Re-cut deliberately with --force --reason \"...\" if this is intentional.")
            return 1
        print("WARNING: recording anyway because --force was given. The provenance block below "
              "describes the tree as it actually is, not as install.sh declares it.")

    unmasked = extract_variant(folder, spec["stem"], masked=False)
    if unmasked is None:
        print(f"FAIL: no FitResult/PostFit files for {spec['stem']!r} found in {folder}")
        return 1
    document = {
        "analysis": args.analysis,
        "source_dir": str(folder.relative_to(REPO_ROOT)) if folder.is_relative_to(REPO_ROOT) else str(folder),
        "directory_listing": sorted(os.listdir(folder)),
        "unmasked": unmasked,
    }
    masked = extract_variant(folder, spec["stem"], masked=True)
    if masked is not None:
        document["masked"] = masked
    else:
        print(f"  note: no masked fit set in {folder} (p(chi2) presumably passed the threshold)")

    versions = {"root_version": recorded["root_version"], "cmake_version": recorded["cmake_version"],
                **recorded["bumphunter_pypackages"]}

    other = "J50" if args.analysis == "J100" else "J100"
    other_path = REPO_ROOT / "tests" / f"baseline_{other}.json"
    if other_path.exists():
        other_versions = json.loads(other_path.read_text())["provenance"]["versions"]
        diffs = {k: (other_versions.get(k), versions.get(k))
                 for k in set(other_versions) | set(versions) if other_versions.get(k) != versions.get(k)}
        if diffs:
            print(f"WARNING: versions disagree with {other_path.name} (recording anyway):")
            for k, (theirs, ours) in sorted(diffs.items()):
                print(f"  {k}: {other}={theirs!r} {args.analysis}={ours!r}")

    document["provenance"] = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pins": pins,
        "versions": versions,
        "input_sha256": {rel: sha256_of(REPO_ROOT / rel) for rel in spec["inputs"]},
        "binary_sha256": recorded["binary_sha256"],
        "reason": args.reason,
    }

    baseline_path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")
    print(f"PASS: wrote {baseline_path.relative_to(REPO_ROOT)} ({baseline_path.stat().st_size} bytes)")
    return 0


# --- check: the entry point ------------------------------------------------

# Baseline keys that describe the baseline itself rather than the fit, and so
# have no candidate counterpart to be compared against.
BASELINE_ONLY_KEYS = {"provenance", "analysis", "source_dir"}


def _run_driver(driver_rel, out_dir, timeout=1800):
    """Run a fit driver as a subprocess with OUT_DIR pointed at a scratch
    directory, using the same setupATLAS preamble as _atlas_probe. Returns
    None on a clean exit, else a short message - never raises and never
    signals failure by itself: XMLReader/quickFit only warn and still
    return 0 on failure (plan section 5), so the baseline diff below is the
    real failure detector, not this exit code."""
    preamble = "setupATLAS >/dev/null 2>&1\n"
    script = f'cd "{REPO_ROOT}" && OUT_DIR="{out_dir}" bash {driver_rel}'
    try:
        proc = subprocess.run(["bash", "-c", preamble + script],
                               text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"driver timed out after {timeout}s"
    except OSError as exc:
        return str(exc)
    if proc.returncode != 0:
        return f"driver exited {proc.returncode} (non-fatal - see baseline diff): {proc.stderr.strip()[-500:]}"
    return None


def _check_input_hashes(analysis):
    """Verify one analysis's input spectra against the baseline's recorded
    sha256, printing the outcome. Returns (ok, baseline_or_None)."""
    spec = ANALYSES[analysis]
    baseline_path = REPO_ROOT / "tests" / f"baseline_{analysis}.json"
    if not baseline_path.is_file():
        print(f"FAIL: no baseline at {baseline_path.relative_to(REPO_ROOT)}")
        return False, None
    baseline = json.loads(baseline_path.read_text())

    mismatches = [f"  {rel}: baseline={expected} now={sha256_of(REPO_ROOT / rel)}"
                  for rel, expected in sorted(baseline["provenance"]["input_sha256"].items())
                  if sha256_of(REPO_ROOT / rel) != expected]
    if mismatches:
        print(f"FAIL: input spectrum changed for {analysis}:")
        print("\n".join(mismatches))
        return False, None
    print(f"{analysis}: input hashes match baseline ({len(baseline['provenance']['input_sha256'])} files)")
    return True, baseline


def _check_one(analysis, baseline, out_dir_base, from_dir, tol_scale):
    spec = ANALYSES[analysis]
    baseline_path = REPO_ROOT / "tests" / f"baseline_{analysis}.json"

    if from_dir is not None:
        folder = Path(from_dir)
        print(f"comparing existing directory {folder} (--from)")
    else:
        folder = out_dir_base / Path(spec["default_dir"]).name
        # Wiped first: a driver that crashes outright must not be masked by
        # a stale FitResult/PostFit left over from a previous check run.
        shutil.rmtree(folder, ignore_errors=True)
        print(f"running {spec['driver']} with OUT_DIR={out_dir_base} ...")
        warning = _run_driver(spec["driver"], out_dir_base)
        if warning:
            print(f"  note: {warning}")

    if not folder.is_dir():
        print(f"FAIL: {folder} does not exist")
        return False

    candidate_unmasked = extract_variant(folder, spec["stem"], masked=False)
    if candidate_unmasked is None:
        print(f"FAIL: {folder} has no FitResult/PostFit for {spec['stem']!r}")
        return False
    candidate = {"directory_listing": sorted(os.listdir(folder)), "unmasked": candidate_unmasked}
    candidate_masked = extract_variant(folder, spec["stem"], masked=True)
    if candidate_masked is not None:
        candidate["masked"] = candidate_masked

    # Everything the baseline holds is compared except the keys that are
    # baseline-only metadata: a candidate has no `provenance` of its own, and
    # `analysis`/`source_dir` describe where the baseline came from rather
    # than what the fit produced. Dropping a blocklist rather than naming a
    # whitelist means a section added to `record` later is compared by
    # default - the old whitelist would have ignored it in silence, which is
    # the one direction this harness must never fail in.
    expected = {k: v for k, v in baseline.items() if k not in BASELINE_ONLY_KEYS}

    failures = compare(expected, candidate, tol_scale=tol_scale)
    if failures:
        print(f"FAIL: {analysis} mismatches {baseline_path.relative_to(REPO_ROOT)} ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
        return False
    print(f"PASS: {analysis} matches {baseline_path.relative_to(REPO_ROOT)}")
    return True


def cmd_check(args):
    print("=== env ===")
    checks, pins, recorded = run_env_checks()
    env_ok = _report_env(checks, recorded, pins)
    print()
    if not env_ok:
        print("FAIL: env checks failed - not running any fits (plan section 5)")
        return 1

    analysis = args.analysis
    if args.from_dir and not analysis:
        matches = [name for name, spec in ANALYSES.items()
                   if Path(args.from_dir).name == Path(spec["default_dir"]).name]
        if len(matches) != 1:
            print("FAIL: --from's directory name doesn't identify an analysis; pass --analysis J100|J50 too")
            return 1
        analysis = matches[0]

    if analysis:
        analyses = [analysis]
    elif args.quick:
        analyses = ["J100"]
    else:
        analyses = ["J100", "J50"]

    print("\n=== input hashes ===")
    baselines = {}
    for name in analyses:
        ok, baseline = _check_input_hashes(name)
        if not ok:
            print("\nFAIL: input hash check failed - not running any fits (plan section 5)")
            return 1
        baselines[name] = baseline

    out_dir_base = REPO_ROOT / "run" / "check_scratch"
    ok = True
    for name in analyses:
        print(f"\n=== {name} ===")
        ok = _check_one(name, baselines[name], out_dir_base, args.from_dir, args.tol_scale) and ok

    print()
    print("PASS: check" if ok else "FAIL: check")
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("selfcheck", help="test the comparator itself; no ROOT, instant")
    subparsers.add_parser("env", help="verify software pins vs what's actually on disk/CVMFS")

    record_parser = subparsers.add_parser("record", help="capture a baseline from an existing run directory")
    record_parser.add_argument("analysis", choices=sorted(ANALYSES))
    record_parser.add_argument("dir", nargs="?", default=None,
                                help=f"default: the run/ dir each analysis was last cut from")
    record_parser.add_argument("--force", action="store_true", help="overwrite an existing baseline")
    record_parser.add_argument("--reason", help="required with --force: why this baseline is being re-cut")

    check_parser = subparsers.add_parser(
        "check", help="env + input hashes, then re-run the driver(s) and compare against the baseline(s)")
    check_parser.add_argument("--quick", action="store_true",
                               help="J100 only, skips J50's BumpHunter masking path (~1 min vs ~6 min)")
    check_parser.add_argument("--from", dest="from_dir", metavar="DIR",
                               help="compare this existing output directory instead of running the driver")
    check_parser.add_argument("--analysis", choices=sorted(ANALYSES),
                               help="which baseline --from's directory belongs to "
                                    "(inferred from the directory name when omitted)")
    check_parser.add_argument("--tol-scale", dest="tol_scale", type=float, default=1.0, metavar="SCALE",
                               help="scale both the rtol and atol terms of the tight/pvalue "
                                    "tolerance classes by this factor (plan section 4)")

    args = parser.parse_args()
    if args.command == "selfcheck":
        return cmd_selfcheck(args)
    if args.command == "env":
        return cmd_env(args)
    if args.command == "record":
        return cmd_record(args)
    if args.command == "check":
        return cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
