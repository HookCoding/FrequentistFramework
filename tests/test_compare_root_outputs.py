"""Tests for the Tier 1 ROOT-output comparison logic."""

import math

from scripts.compare_root_outputs import (
    calculate_relative_difference,
    close_enough,
    compare_histograms,
    get_histogram,
)


def test_identical_values_agree():
    assert close_enough(
        reference=1.0,
        candidate=1.0,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_different_values_fail_exact_comparison():
    assert not close_enough(
        reference=1.0,
        candidate=1.0001,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_small_absolute_difference_can_pass():
    assert close_enough(
        reference=0.0,
        candidate=1e-12,
        relative_tolerance=0.0,
        absolute_tolerance=1e-10,
    )


def test_small_relative_difference_can_pass():
    assert close_enough(
        reference=100.0,
        candidate=100.000001,
        relative_tolerance=1e-7,
        absolute_tolerance=0.0,
    )


def test_nan_only_agrees_with_nan():
    assert close_enough(
        reference=math.nan,
        candidate=math.nan,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert not close_enough(
        reference=math.nan,
        candidate=1.0,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_relative_difference():
    assert calculate_relative_difference(100.0, 101.0) == 0.01


def test_relative_difference_with_two_zero_values():
    assert calculate_relative_difference(0.0, 0.0) == 0.0


def test_relative_difference_with_zero_reference():
    assert math.isinf(calculate_relative_difference(0.0, 1.0))


class FakeAxis:
    def __init__(self, bin_edges):
        self._bin_edges = bin_edges

    def GetBinLowEdge(self, bin_index):
        return self._bin_edges[bin_index - 1]


class FakeHistogram:
    def __init__(
        self,
        contents,
        errors,
        bin_edges,
        class_name="TH1D",
    ):
        self._contents = contents
        self._errors = errors
        self._axis = FakeAxis(bin_edges)
        self._class_name = class_name

    def InheritsFrom(self, class_name):
        return class_name == "TH1"

    def ClassName(self):
        return self._class_name

    def GetNbinsX(self):
        return len(self._contents) - 2

    def GetBinContent(self, bin_index):
        return self._contents[bin_index]

    def GetBinError(self, bin_index):
        return self._errors[bin_index]

    def GetXaxis(self):
        return self._axis


class FakeNonHistogram:
    def InheritsFrom(self, class_name):
        return False

    def ClassName(self):
        return "TGraph"


class FakeRootFile:
    def __init__(self, objects):
        self._objects = objects
        self.requested_paths = []

    def Get(self, object_path):
        self.requested_paths.append(object_path)
        return self._objects.get(object_path)


def make_histogram(
    *,
    contents=None,
    errors=None,
    bin_edges=None,
    class_name="TH1D",
):
    if contents is None:
        contents = [0.0, 10.0, 20.0, 0.0]
    if errors is None:
        errors = [0.0, 1.0, 2.0, 0.0]
    if bin_edges is None:
        bin_edges = [100.0, 200.0, 300.0]

    return FakeHistogram(
        contents=contents,
        errors=errors,
        bin_edges=bin_edges,
        class_name=class_name,
    )


def test_get_histogram_rejects_missing_object():
    root_file = FakeRootFile({})

    try:
        get_histogram(root_file, "nested/missing")
    except KeyError as error:
        assert "ROOT object not found: nested/missing" in str(error)
    else:
        raise AssertionError("Missing ROOT object was not rejected")


def test_get_histogram_rejects_wrong_object_type():
    root_file = FakeRootFile({"nested/graph": FakeNonHistogram()})

    try:
        get_histogram(root_file, "nested/graph")
    except TypeError as error:
        assert "TGraph" in str(error)
        assert "TH1 histogram was expected" in str(error)
    else:
        raise AssertionError("Non-histogram ROOT object was not rejected")


def test_compare_histograms_accepts_identical_nested_histograms():
    object_path = "directory/subdirectory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile({object_path: make_histogram()})

    differences = compare_histograms(
        reference_file,
        candidate_file,
        object_path=object_path,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert differences == []
    assert reference_file.requested_paths == [object_path]
    assert candidate_file.requested_paths == [object_path]


def test_compare_histograms_rejects_different_classes():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram(class_name="TH1D")})
    candidate_file = FakeRootFile({object_path: make_histogram(class_name="TH1F")})

    try:
        compare_histograms(
            reference_file,
            candidate_file,
            object_path=object_path,
            relative_tolerance=0.0,
            absolute_tolerance=0.0,
        )
    except TypeError as error:
        assert "histogram classes differ" in str(error)
    else:
        raise AssertionError("Histogram class mismatch was not rejected")


def test_compare_histograms_rejects_different_bin_counts():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile(
        {
            object_path: make_histogram(
                contents=[0.0, 10.0, 20.0, 30.0, 0.0],
                errors=[0.0, 1.0, 2.0, 3.0, 0.0],
                bin_edges=[100.0, 200.0, 300.0, 400.0],
            )
        }
    )

    try:
        compare_histograms(
            reference_file,
            candidate_file,
            object_path=object_path,
            relative_tolerance=0.0,
            absolute_tolerance=0.0,
        )
    except ValueError as error:
        assert "numbers of bins differ" in str(error)
    else:
        raise AssertionError("Histogram bin-count mismatch was not rejected")


def test_compare_histograms_detects_changed_bin_content():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile({object_path: make_histogram(contents=[0.0, 10.0, 21.0, 0.0])})

    differences = compare_histograms(
        reference_file,
        candidate_file,
        object_path=object_path,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert len(differences) == 1
    assert differences[0].component == "contents"
    assert differences[0].bin_index == 2
    assert differences[0].reference == 20.0
    assert differences[0].candidate == 21.0


def test_compare_histograms_detects_changed_bin_error():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile({object_path: make_histogram(errors=[0.0, 1.0, 2.5, 0.0])})

    differences = compare_histograms(
        reference_file,
        candidate_file,
        object_path=object_path,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert len(differences) == 1
    assert differences[0].component == "errors"
    assert differences[0].bin_index == 2


def test_compare_histograms_detects_changed_bin_edge():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile({object_path: make_histogram(bin_edges=[100.0, 201.0, 300.0])})

    differences = compare_histograms(
        reference_file,
        candidate_file,
        object_path=object_path,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert len(differences) == 1
    assert differences[0].component == "bin_edges"
    assert differences[0].bin_index == 1


def test_compare_histograms_accepts_content_drift_within_tolerance():
    object_path = "directory/histogram"
    reference_file = FakeRootFile({object_path: make_histogram()})
    candidate_file = FakeRootFile(
        {object_path: make_histogram(contents=[0.0, 10.0, 20.000001, 0.0])}
    )

    differences = compare_histograms(
        reference_file,
        candidate_file,
        object_path=object_path,
        relative_tolerance=1e-6,
        absolute_tolerance=0.0,
    )

    assert differences == []
