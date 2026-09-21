"""Unit tests for python/FindBHWindow.py's split (decomposition plan section 7).

The plan expected this module to be untestable from the main environment - "it runs in its own
virtual environment and cannot be imported from the main one", with the uproot-dependent test
skipping automatically. Measured before writing any of this: matplotlib 3.4.3, uproot 4.2.0 and
numpy 1.22.3 all come from the LCG_102a view, so the module imports and every function here is
reachable, including the one that reads a ROOT file.

The one thing that is genuinely absent is `pyBumpHunter`. `import pyBumpHunter` from the
repository root resolves to the *clone directory* of the same name as an implicit namespace
package - `__file__` is None and `BumpHunter1D` is not in it. Production is unaffected, because
`python3 python/FindBHWindow.py` puts `python/` on sys.path rather than the repository root and
the venv's installed egg wins. Here it means `_configure_hunter` has to be exercised against a
stand-in, which is what the plan asked for anyway.

`tests/repro.py` compares `seed` and `npe` exactly, so the configuration assertions below are not
redundant with it - they fail in seconds rather than after a full re-fit.
"""

import json
import re

import numpy as np
import pytest

from conftest import FIXTURES

import FindBHWindow
from FindBHWindow import (
    NpEncoder,
    _build_parser,
    _load_histograms,
    _crop_data_to_bkg_range,
    _configure_hunter,
    _run_scan,
    _mask_window,
    _write_results,
)

J50_POSTFIT = str(FIXTURES / "PostFit_J50_sixPar_masked.root")
J50_BKGHIST = "J50yStar06_rebinned/postfit"
J50_DATAHIST = "J50yStar06_rebinned/data"

# The recorded BumpHunter result for the J50 run, from tests/fixtures/BHresults_J50.json.
RECORDED_STATE = {"min_loc_ar": [12], "min_width_ar": [3]}
RECORDED_MASKMIN = 582.0
RECORDED_MASKMAX = 662.0
RECORDED_BLINDRANGE = "582,662"


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------

def test_build_parser_accepts_what_run_anafit_passes():
    """run_anaFit.py:482 composes exactly these four options and no more. Nothing else checks
    the boundary between that shell string and this module."""
    args = _build_parser().parse_args([
        "--inputfile", "run/PostFit_anaFit_sixPar_bkgOnly.root",
        "--bkghist", "J50yStar06_rebinned/postfit",
        "--datahist", "J50yStar06_rebinned/data",
        "--outputjson", "run/BHresults.json",
    ])

    assert args.inputfile == "run/PostFit_anaFit_sixPar_bkgOnly.root"
    assert args.bkghist == "J50yStar06_rebinned/postfit"
    assert args.datahist == "J50yStar06_rebinned/data"
    assert args.outputjson == "run/BHresults.json"
    # neither Run 2 driver sets this, so the observable-value branch is the live one
    assert args.usebinnumbers is False


def test_build_parser_requires_an_input_file():
    with pytest.raises(SystemExit):
        _build_parser().parse_args([])


# ---------------------------------------------------------------------------
# _load_histograms
# ---------------------------------------------------------------------------

def test_load_histograms_reads_four_arrays_from_the_recorded_postfit():
    bkg, bins, data, bins_data = _load_histograms(J50_POSTFIT, J50_BKGHIST, J50_DATAHIST)

    assert len(bkg) == 65 and len(bins) == 66
    assert len(data) == 65 and len(bins_data) == 66
    assert bins[0] == 302.0 and bins[-1] == 2997.0


def test_load_histograms_returns_plain_numpy_after_the_file_closes():
    """to_numpy() copies out of the file, so nothing here depends on it staying open."""
    bkg, bins, data, bins_data = _load_histograms(J50_POSTFIT, J50_BKGHIST, J50_DATAHIST)

    for arr in (bkg, bins, data, bins_data):
        assert isinstance(arr, np.ndarray)
    assert float(bins[12]) == RECORDED_MASKMIN


# ---------------------------------------------------------------------------
# _crop_data_to_bkg_range
# ---------------------------------------------------------------------------

def test_crop_keeps_exactly_the_bins_inside_the_background_range():
    """Six data bins on unit edges, background covering [2, 4). The two bins whose left edges are
    2 and 3 lie wholly inside and both survive - the exclusive slice end is the index of the edge
    at 4, not one before it."""
    data = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    bins_data = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    bins = np.array([2.0, 3.0, 4.0])

    cropped, firstbindata = _crop_data_to_bkg_range(data, bins_data, bins)

    assert firstbindata == 2
    assert list(cropped) == [12.0, 13.0]
    assert len(cropped) == len(bins) - 1  # one data bin per background bin


def test_crop_is_a_no_op_when_the_ranges_are_identical():
    """The production case: both histograms come from the same rebinning call, so the arrays of
    edges are equal and nothing is cut."""
    data = np.array([1.0, 2.0, 3.0])
    bins = np.array([0.0, 1.0, 2.0, 3.0])

    cropped, firstbindata = _crop_data_to_bkg_range(data, bins, bins)

    assert firstbindata == 0
    assert list(cropped) == [1.0, 2.0, 3.0]


def test_crop_is_a_no_op_on_the_recorded_j50_postfit():
    """Measured rather than assumed: run_anaFit.py passes <channel>_rebinned/postfit and
    <channel>_rebinned/data, which are rebinned onto the same edges, so on the one recorded run
    that reached BumpHunter this function returns its input untouched."""
    bkg, bins, data, bins_data = _load_histograms(J50_POSTFIT, J50_BKGHIST, J50_DATAHIST)
    assert np.array_equal(bins, bins_data)

    cropped, firstbindata = _crop_data_to_bkg_range(data, bins_data, bins)

    assert firstbindata == 0
    assert np.array_equal(cropped, data)
    assert len(cropped) == len(bkg)


def test_crop_trims_only_the_low_side_when_the_data_starts_lower():
    data = np.array([10.0, 11.0, 12.0, 13.0])
    bins_data = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    bins = np.array([1.0, 2.0, 3.0, 4.0])

    cropped, firstbindata = _crop_data_to_bkg_range(data, bins_data, bins)

    assert firstbindata == 1
    assert list(cropped) == [11.0, 12.0, 13.0]


def test_crop_returns_nothing_when_the_background_range_sits_below_the_data():
    """Degenerate, and silent: lastbindata keeps its initial 0, so the slice is empty and the
    scan would run on no data rather than complain. Unreachable from either driver, which passes
    two histograms out of the same file with the same binning. Pinned, not guarded."""
    data = np.array([1.0, 2.0, 3.0])
    bins_data = np.array([10.0, 11.0, 12.0, 13.0])
    bins = np.array([0.0, 1.0, 2.0])

    cropped, firstbindata = _crop_data_to_bkg_range(data, bins_data, bins)

    assert firstbindata == 0
    assert len(cropped) == 0


# ---------------------------------------------------------------------------
# _configure_hunter
# ---------------------------------------------------------------------------

class _RecordingBH:
    """Stand-in for the pyBumpHunter module, which is not importable here - see the module
    docstring."""

    def __init__(self):
        self.kwargs = None

    def BumpHunter1D(self, **kwargs):
        self.kwargs = kwargs
        return "hunter"


def test_configure_hunter_passes_the_pinned_configuration(monkeypatch):
    recorder = _RecordingBH()
    monkeypatch.setattr(FindBHWindow, "BH", recorder)
    bins = np.array([0.0, 1.0, 2.0])

    hunter = _configure_hunter(bins)

    assert hunter == "hunter"
    assert recorder.kwargs == {
        "width_min": 2,
        "width_max": 3,
        "width_step": 1,
        "scan_step": 1,
        "npe": 10000,
        "nworker": 1,
        "seed": 666,
        "bins": recorder.kwargs["bins"],
    }
    assert recorder.kwargs["bins"] is bins


def test_configure_hunter_pins_seed_and_single_worker(monkeypatch):
    """Asserted on their own because they are the two that move global_Pval without changing any
    input: nworker above 1 reorders the pseudo-experiments even at a fixed seed."""
    recorder = _RecordingBH()
    monkeypatch.setattr(FindBHWindow, "BH", recorder)

    _configure_hunter(np.array([0.0, 1.0]))

    assert recorder.kwargs["seed"] == 666
    assert recorder.kwargs["nworker"] == 1
    assert recorder.kwargs["npe"] == 10000


# ---------------------------------------------------------------------------
# _run_scan
# ---------------------------------------------------------------------------

class _FakeHunter:
    def __init__(self):
        self.calls = []

    def bump_scan(self, data, bkg, is_hist):
        self.calls.append((list(data), list(bkg), is_hist))


def test_run_scan_passes_is_hist_and_prints_the_banner(capsys):
    """is_hist=True is load-bearing: data and bkg are bin contents, not samples, and BumpHunter
    would otherwise treat them as unbinned values."""
    hunter = _FakeHunter()

    _run_scan(hunter, np.array([1.0, 2.0]), np.array([3.0, 4.0]))

    assert hunter.calls == [([1.0, 2.0], [3.0, 4.0], True)]
    assert "####bump_scan call####" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _mask_window
# ---------------------------------------------------------------------------

def test_mask_window_reproduces_the_recorded_j50_window():
    """End to end against the one recorded BumpHunter run: the edges come from the fixture, the
    scan result from tests/fixtures/BHresults_J50.json, and the answer has to be the MaskMin,
    MaskMax and BlindRange that file records."""
    _, bins, _, _ = _load_histograms(J50_POSTFIT, J50_BKGHIST, J50_DATAHIST)

    maskmin, maskmax, blindrange = _mask_window(
        RECORDED_STATE, bins, firstbindata=0, usebinnumbers=False)

    assert maskmin == RECORDED_MASKMIN
    assert maskmax == RECORDED_MASKMAX
    assert blindrange == RECORDED_BLINDRANGE


def test_mask_window_uses_bin_edges_by_default():
    bins = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    state = {"min_loc_ar": [1], "min_width_ar": [2]}

    maskmin, maskmax, _ = _mask_window(state, bins, firstbindata=7, usebinnumbers=False)

    assert (maskmin, maskmax) == (200.0, 400.0)  # bins[1] and bins[1+2]; firstbindata unused


def test_mask_window_uses_bin_numbers_offset_by_firstbindata_when_asked():
    """Neither Run 2 driver sets --usebinnumbers, so this test is the only thing exercising the
    branch."""
    bins = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    state = {"min_loc_ar": [1], "min_width_ar": [2]}

    maskmin, maskmax, blindrange = _mask_window(state, bins, firstbindata=7, usebinnumbers=True)

    assert (maskmin, maskmax) == (8, 10)
    assert blindrange == "8,10"


def test_mask_window_truncates_the_blind_range_rather_than_rounding():
    """%d truncates. The mask boundary that reaches the XML card is an integer even when the bin
    edge is not, and truncation rather than rounding is a physics-visible choice."""
    bins = np.array([0.0, 100.7, 200.9, 300.0])
    state = {"min_loc_ar": [1], "min_width_ar": [1]}

    maskmin, maskmax, blindrange = _mask_window(state, bins, firstbindata=0, usebinnumbers=False)

    assert (maskmin, maskmax) == (100.7, 200.9)
    assert blindrange == "100,200"


# ---------------------------------------------------------------------------
# _write_results and NpEncoder
# ---------------------------------------------------------------------------

def test_write_results_encodes_numpy_scalars_and_arrays_as_plain_json(tmp_path):
    out = tmp_path / "BHresults.json"

    _write_results({
        "an_int": np.int64(7),
        "a_float": np.float64(1.5),
        "an_array": np.array([1.0, 2.0]),
    }, str(out))

    loaded = json.loads(out.read_text())
    assert loaded == {"an_int": 7, "a_float": 1.5, "an_array": [1.0, 2.0]}
    assert isinstance(loaded["an_int"], int)
    assert isinstance(loaded["an_array"], list)


def _cpp_get_val(json_str, key):
    """The regex plot_postfit.cpp:119 builds, transcribed. Its match group is what stof() reads."""
    match = re.search(r'"' + key + r'"\s*:\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', json_str)
    return float(match.group(1)) if match else 0.0


def test_write_results_output_is_scrapable_by_plot_postfit_cpp(tmp_path):
    """plot_postfit.cpp:127-130 scrapes four values by regex over the whole file, so it finds
    global_Pval and significance although they are nested one level down under pyBHresult. The
    nesting is recorded here so a future flattening is a deliberate change rather than an
    accident that happens to keep working."""
    out = tmp_path / "BHresults.json"

    _write_results({
        "pyBHresult": {"global_Pval": np.float64(0.0322),
                       "significance": np.float64(1.8494005228938295)},
        "MaskMin": np.float64(582.0),
        "MaskMax": np.float64(662.0),
        "BlindRange": "582,662",
    }, str(out))

    text = out.read_text()
    assert _cpp_get_val(text, "global_Pval") == pytest.approx(0.0322)
    assert _cpp_get_val(text, "significance") == pytest.approx(1.8494005228938295)
    assert _cpp_get_val(text, "MaskMin") == 582.0
    assert _cpp_get_val(text, "MaskMax") == 662.0
    # a key the macro does not know about returns its 0.0f fallback, silently
    assert _cpp_get_val(text, "NoSuchKey") == 0.0


@pytest.mark.parametrize("value,want", [
    (np.int64(3), 3),
    (np.int32(3), 3),
    (np.float64(2.5), 2.5),
    (np.float32(0.5), 0.5),
    (np.array([1, 2, 3]), [1, 2, 3]),
])
def test_npencoder_converts_each_numpy_type(value, want):
    assert json.loads(json.dumps({"v": value}, cls=NpEncoder)) == {"v": want}


def test_npencoder_still_raises_on_a_type_it_does_not_handle():
    with pytest.raises(TypeError):
        json.dumps({"v": {1, 2}}, cls=NpEncoder)
