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
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tolerance classes, plan section 4. "exact" and "note" are markers;
# anything else is an {"rtol":..., "atol":...} dict.
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

NOTE_LEAVES = {"root_version", "active_view"}


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


def classify(path):
    leaf = path.rsplit(".", 1)[-1].split("[", 1)[0]
    if leaf in NOTE_LEAVES:
        return "note"
    return TOLERANCE_BY_LEAF.get(leaf, "exact")


def compare(baseline, candidate, rtol_scale=1.0):
    """Compare two nested baseline/candidate structures.

    Returns (failures, notes), both lists of human-readable strings.
    Reports every mismatch, not just the first; a missing or extra key
    is a failure. Keys classified "note" are recorded but never fail.
    """
    failures = []
    notes = []
    base_flat = dict(flatten(baseline))
    cand_flat = dict(flatten(candidate))

    for path in sorted(set(base_flat) - set(cand_flat)):
        failures.append(f"missing: {path!r} (baseline has {base_flat[path]!r})")
    for path in sorted(set(cand_flat) - set(base_flat)):
        failures.append(f"unexpected: {path!r} (candidate has {cand_flat[path]!r})")

    for path in sorted(set(base_flat) & set(cand_flat)):
        b, c = base_flat[path], cand_flat[path]
        cls = classify(path)

        if cls == "note":
            if b != c:
                notes.append(f"{path}: baseline={b!r} candidate={c!r} (informational)")
            continue

        if cls == "exact" or isinstance(b, bool) or not isinstance(b, (int, float)):
            if b != c:
                failures.append(f"{path}: expected {b!r}, got {c!r} (exact match required)")
            continue

        rtol, atol = cls["rtol"] * rtol_scale, cls["atol"] * rtol_scale
        diff = abs(c - b)
        if diff > atol + rtol * abs(b):
            failures.append(
                f"{path}: expected {b!r}, got {c!r} "
                f"(|diff|={diff:.3g} > atol {atol:.3g} + rtol*|baseline| {rtol * abs(b):.3g})"
            )

    return failures, notes


def cmd_selfcheck(args):
    """Exercise compare() against synthetic data covering every tolerance
    class, a missing key, an extra key, and a note-class difference."""
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
        "provenance": {"root_version": "6.26/08"},
    }

    # Should PASS: every tight/pvalue float nudged well inside tolerance,
    # one note-class field that legitimately differs (never fails).
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
        "provenance": {"root_version": "6.40/04"},
    }
    failures, notes = compare(baseline, passing)
    assert failures == [], f"expected a clean pass, got: {failures}"
    assert len(notes) == 1 and "root_version" in notes[0], f"expected one root_version note, got: {notes}"

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
        "provenance": {"root_version": "6.40/04"},
        "extra_key": 1,
    }  # fitResult.covQual is dropped above: a missing key
    failures, notes = compare(baseline, failing)
    failure_text = "\n".join(failures)
    for expected in ("minNll", "status", "pval", "missing:", "unexpected:"):
        assert expected in failure_text, f"expected {expected!r} among failures, got:\n{failure_text}"
    assert len(failures) == 5, f"expected exactly 5 failures, got {len(failures)}:\n{failure_text}"

    # --rtol scaling: the same near-miss must fail at the default scale
    # and pass once the tolerance is widened.
    tight_baseline = {"chi2": {"c": {"pval": 0.0149}}}
    tight_candidate = {"chi2": {"c": {"pval": 0.0149015}}}
    at_default, _ = compare(tight_baseline, tight_candidate)
    assert at_default != [], "expected this near-miss to fail at the default tolerance"
    at_100x, _ = compare(tight_baseline, tight_candidate, rtol_scale=100.0)
    assert at_100x == [], f"expected rtol_scale=100 to absorb the same difference, got: {at_100x}"

    print("PASS: comparator selfcheck (tolerance classes, missing/extra keys, notes, rtol scaling)")
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
EXPECTED_PYBUMPHUNTER_EGG_VERSION = "0.4.3.dev16+g91f49a6"
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
        if m and m.group(1) != "..":
            current_dir = m.group(1)
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
    eggs = sorted(pyBH_env_dir.glob("lib/python*/site-packages/pyBumpHunter-*.egg"))
    if not eggs:
        return None
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
        roofit_shas[fw] = expected
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

    pyBH_env_dir = root / "pyBumpHunter" / "pyBH_env"
    egg_version = find_pybumphunter_egg_version(pyBH_env_dir) if pyBH_env_dir.is_dir() else None
    check("pyBumpHunter installed egg version", egg_version == EXPECTED_PYBUMPHUNTER_EGG_VERSION,
          f"installed egg is {egg_version!r}, expected {EXPECTED_PYBUMPHUNTER_EGG_VERSION!r}")

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
            check(f"binary present: {rel_path}", True,
                  f"sha256={binary_hashes[rel_path]} "
                  f"(not yet compared: no baseline provenance exists until 'record' is built)")
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

    pins = {fw: install_pins.get(fw) for fw in FRAMEWORKS}
    pins["RooFitExtensions"] = roofit_shas
    pins["active_view"] = agreed_view
    pins["pyBH_python_version"] = parse_pyvenv_cfg(pyvenv_path).get("version") if pyvenv_path.is_file() else None
    pins["pyBumpHunter_egg_version"] = egg_version

    return checks, pins, recorded


def cmd_env(args):
    checks, pins, recorded = run_env_checks()

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
    baseline_paths = sorted((REPO_ROOT / "tests").glob("baseline_*.json"))
    if not baseline_paths:
        print("\nNo baseline exists yet - nothing to compare those versions against.")
    else:
        reference = json.loads(baseline_paths[0].read_text())["provenance"]["versions"]
        diffs = {k: (reference.get(k), live_versions.get(k))
                 for k in set(reference) | set(live_versions)
                 if reference.get(k) != live_versions.get(k)}
        if diffs:
            print(f"\nWARNING: versions differ from {baseline_paths[0].name}'s provenance (non-fatal):")
            for k, (was, now) in sorted(diffs.items()):
                print(f"  {k}: baseline={was!r} now={now!r}")
        else:
            print(f"\nVersions match {baseline_paths[0].name}'s provenance.")

    failed = [c for c in checks if not c[1]]
    print()
    if failed:
        print(f"FAIL: {len(failed)}/{len(checks)} environment checks failed")
        return 1
    print(f"PASS: all {len(checks)} environment checks passed")
    return 0


# --- record: capture a baseline from an existing run directory -----------

ANALYSES = {
    "J100": {
        "default_dir": "run/run_481_3000_sixPar",
        "stem": "anaFit_sixPar_bkgOnly",
        "top_dir": "J100yStar06",
        "inputs": ["Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
                   "Input/data/dijetTLA/fullRun2TLAJ100mjj.root"],
    },
    "J50": {
        "default_dir": "run/run_J50_302_2997_sixPar",
        "stem": "anaFit_sixPar_bkgOnly",
        "top_dir": "J50yStar06",
        "inputs": ["Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
                   "Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root"],
    },
}


def extract_fit_result(path):
    """fitResult's minNll/status/covQual and every floatParsFinal() entry."""
    import ROOT
    f = ROOT.TFile.Open(str(path))
    fr = f.Get("fitResult")
    pars = fr.floatParsFinal()
    params = {pars.at(i).GetName(): {"value": pars.at(i).getVal(), "error": pars.at(i).getError()}
              for i in range(pars.getSize())}
    result = {"minNll": fr.minNll(), "status": fr.status(), "covQual": fr.covQual(), "params": params}
    f.Close()
    return result


def extract_postfit(path, top_dir):
    """The 6-bin chi2 block for every TDirectory, plus postfit bins and the
    data integral for the two *_rebinned directories only (plan section 3)."""
    import ROOT
    f = ROOT.TFile.Open(str(path))
    chi2, postfit_bins = {}, {}
    for name in (top_dir, f"{top_dir}_bkgonly", f"{top_dir}_rebinned", f"{top_dir}_bkgonly_rebinned"):
        d = f.Get(name)
        if d is None:
            raise RuntimeError(f"{path}: missing TDirectory {name!r}")
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


def extract_variant(folder, stem, top_dir, masked):
    """None if the fit set (unmasked or masked) is not present in folder."""
    suffix = "_masked" if masked else ""
    fit_path = folder / f"FitResult_{stem}{suffix}.root"
    post_path = folder / f"PostFit_{stem}{suffix}.root"
    if not fit_path.is_file() or not post_path.is_file():
        return None
    chi2, postfit_bins = extract_postfit(post_path, top_dir)
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

    unmasked = extract_variant(folder, spec["stem"], spec["top_dir"], masked=False)
    if unmasked is None:
        print(f"FAIL: no FitResult/PostFit files for {spec['stem']!r} found in {folder}")
        return 1
    document = {
        "analysis": args.analysis,
        "source_dir": str(folder.relative_to(REPO_ROOT)) if folder.is_relative_to(REPO_ROOT) else str(folder),
        "directory_listing": sorted(os.listdir(folder)),
        "unmasked": unmasked,
    }
    masked = extract_variant(folder, spec["stem"], spec["top_dir"], masked=True)
    if masked is not None:
        document["masked"] = masked
    else:
        print(f"  note: no masked fit set in {folder} (p(chi2) presumably passed the threshold)")

    _, pins, recorded = run_env_checks()
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

    args = parser.parse_args()
    if args.command == "selfcheck":
        return cmd_selfcheck(args)
    if args.command == "env":
        return cmd_env(args)
    if args.command == "record":
        return cmd_record(args)


if __name__ == "__main__":
    sys.exit(main())
