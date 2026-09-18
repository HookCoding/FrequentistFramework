"""Small ROOT helpers shared by the fit-path unit tests.

Two jobs only: build a detached histogram from plain numbers, and assert two histograms agree.
Both are needed by more than one test module, which is the only reason they live here rather
than beside their first caller.
"""

import array
import math


def make_hist(name, edges, contents, errors=None):
    """Build a TH1D on the given variable bin edges, detached from any directory.

    SetDirectory(0) is not decoration: without it the histogram is owned by whatever TFile
    happens to be current, and it dies when that file closes. Every histogram a test builds is
    detached, so a test can never pass or fail because of file lifetime.

    errors=None gives sqrt(content), matching the Poisson errors the data histograms carry.
    """
    import ROOT

    h = ROOT.TH1D(name, "", len(edges) - 1, array.array("d", [float(e) for e in edges]))
    h.SetDirectory(0)
    for i, content in enumerate(contents, start=1):
        h.SetBinContent(i, float(content))
        h.SetBinError(i, float(errors[i - 1]) if errors is not None else math.sqrt(abs(content)))
    return h


def assert_hists_equal(got, want, rel=1e-12, context=""):
    """Assert two histograms agree in binning, contents and errors.

    rel defaults to 1e-12 rather than to an exact comparison because a re-run of the same
    extraction on the same inputs is deterministic to the last bit in practice but goes through
    ROOT's own I/O rounding; 1e-12 is far tighter than the 1e-6 tests/repro.py uses for the same
    quantities, so nothing physically meaningful can hide under it.
    """
    where = f" [{context}]" if context else ""
    assert got is not None, f"missing histogram{where}"
    assert want is not None, f"missing reference histogram{where}"

    assert got.GetNbinsX() == want.GetNbinsX(), (
        f"bin count {got.GetNbinsX()} != {want.GetNbinsX()}{where}"
    )

    for i in range(1, want.GetNbinsX() + 2):
        assert got.GetBinLowEdge(i) == want.GetBinLowEdge(i), (
            f"bin {i} low edge {got.GetBinLowEdge(i)} != {want.GetBinLowEdge(i)}{where}"
        )

    for i in range(1, want.GetNbinsX() + 1):
        _assert_close(got.GetBinContent(i), want.GetBinContent(i), rel,
                      f"bin {i} content{where}")
        _assert_close(got.GetBinError(i), want.GetBinError(i), rel, f"bin {i} error{where}")

    # Bin labels carry meaning in the six-bin chi2 summary and in the postfit parameter
    # histogram, where they are the only thing naming which number is which.
    for i in range(1, want.GetNbinsX() + 1):
        assert got.GetXaxis().GetBinLabel(i) == want.GetXaxis().GetBinLabel(i), (
            f"bin {i} label {got.GetXaxis().GetBinLabel(i)!r} != "
            f"{want.GetXaxis().GetBinLabel(i)!r}{where}"
        )


def _assert_close(got, want, rel, what):
    if math.isnan(got) or math.isnan(want):
        # NaN == NaN is false, and treating it as a match is exactly the hole tests/repro.py's
        # comparator had (KNOWN_ISSUES issue 22). A NaN on either side is a failure.
        raise AssertionError(f"{what}: NaN present (got {got}, want {want})")
    if got == want:
        return
    scale = max(abs(got), abs(want))
    if scale == 0.0 or abs(got - want) / scale <= rel:
        return
    raise AssertionError(f"{what}: {got!r} != {want!r} (relative {abs(got - want) / scale:.3e})")
