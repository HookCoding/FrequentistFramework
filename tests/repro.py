#!/usr/bin/env python3
"""Reproducibility regression harness for the J50/J100 dijet TLA fits.

Subcommands land incrementally, see plans/2026-09-15-reproducibility-lock.md.
Only `selfcheck` exists so far: it tests the comparator below against
synthetic data, without touching ROOT or the ATLAS environment.
"""
import argparse
import sys

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("selfcheck", help="test the comparator itself; no ROOT, instant")

    args = parser.parse_args()
    if args.command == "selfcheck":
        return cmd_selfcheck(args)


if __name__ == "__main__":
    sys.exit(main())
