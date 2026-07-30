#!/usr/bin/env python3
"""Compare selected histograms in two ROOT output files."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass

try:
     import ROOT  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
     ROOT = None  # type: ignore

@dataclass
class Difference:
    """A numerical difference found between two ROOT histograms."""

    object_path: str
    component: str
    bin_index: int
    reference: float
    candidate: float
    absolute_difference: float
    relative_difference: float


def close_enough(
    reference: float,
    candidate: float,
    relative_tolerance: float,
    absolute_tolerance: float,
) -> bool:
    """Return whether two values agree within the specified tolerances."""
    if math.isnan(reference) or math.isnan(candidate):
        return math.isnan(reference) and math.isnan(candidate)

    if math.isinf(reference) or math.isinf(candidate):
        return reference == candidate

    return abs(candidate - reference) <= (
        absolute_tolerance + relative_tolerance * abs(reference)
    )

def calculate_relative_difference(
    reference: float,
    candidate: float,
) -> float:
    """Return the relative difference between two values."""
    absolute_difference = abs(candidate - reference)

    if reference == 0:
        return 0.0 if absolute_difference == 0 else math.inf

    return absolute_difference / abs(reference)

def open_root_file(path: str):
    """Open a ROOT file and fail cleanly if it cannot be read."""
    if ROOT is None:
        raise RuntimeError(
             "PyROOT is required to open ROOT files; install CERN ROOT/PyROOT and retry."
        )
    root_file = ROOT.TFile.Open(path, "READ")

    if not root_file or root_file.IsZombie():
        raise OSError(f"Could not open ROOT file: {path}")

    return root_file

def get_histogram(root_file, object_path: str):
    """Retrieve a histogram and validate that it exists."""
    histogram = root_file.Get(object_path)

    if not histogram:
        raise KeyError(f"ROOT object not found: {object_path}")

    if not histogram.InheritsFrom("TH1"):
        raise TypeError(
            f"{object_path} has class {histogram.ClassName()}, "
            "but a TH1 histogram was expected"
        )

    return histogram


def compare_component(
    object_path: str,
    component: str,
    reference_values: list[float],
    candidate_values: list[float],
    relative_tolerance: float,
    absolute_tolerance: float,
) -> list[Difference]:
    """Compare one numerical component of a histogram."""
    if len(reference_values) != len(candidate_values):
        raise ValueError(
            f"{object_path}/{component}: lengths differ: "
            f"{len(reference_values)} != {len(candidate_values)}"
        )

    differences = []

    for bin_index, (reference, candidate) in enumerate(
        zip(reference_values, candidate_values)
    ):
        if not close_enough(
            reference,
            candidate,
            relative_tolerance,
            absolute_tolerance,
        ):
            differences.append(
                Difference(
                    object_path=object_path,
                    component=component,
                    bin_index=bin_index,
                    reference=reference,
                    candidate=candidate,
                    absolute_difference=abs(candidate - reference),
                    relative_difference=calculate_relative_difference(
                        reference,
                        candidate,
                    ),
                )
            )

    return differences


def extract_histogram_components(histogram) -> dict[str, list[float]]:
    """Extract contents, errors, and bin edges from a histogram."""
    number_of_bins = histogram.GetNbinsX()

    return {
        "contents": [
            float(histogram.GetBinContent(bin_index))
            for bin_index in range(number_of_bins + 2)
        ],
        "errors": [
            float(histogram.GetBinError(bin_index))
            for bin_index in range(number_of_bins + 2)
        ],
        "bin_edges": [
            float(histogram.GetXaxis().GetBinLowEdge(bin_index))
            for bin_index in range(1, number_of_bins + 2)
        ],
    }


def compare_histograms(
    reference_file,
    candidate_file,
    object_path: str,
    relative_tolerance: float,
    absolute_tolerance: float,
):
    """Compare the numerical components of one histogram."""
    reference_histogram = get_histogram(
        reference_file,
        object_path,
    )
    candidate_histogram = get_histogram(
        candidate_file,
        object_path,
    )

    if reference_histogram.ClassName() != candidate_histogram.ClassName():
        raise TypeError(
            f"{object_path}: histogram classes differ: "
            f"{reference_histogram.ClassName()} != "
            f"{candidate_histogram.ClassName()}"
        )

    if (
        reference_histogram.GetNbinsX()
        != candidate_histogram.GetNbinsX()
    ):
        raise ValueError(
            f"{object_path}: numbers of bins differ: "
            f"{reference_histogram.GetNbinsX()} != "
            f"{candidate_histogram.GetNbinsX()}"
        )

    reference_components = extract_histogram_components(
        reference_histogram
    )
    candidate_components = extract_histogram_components(
        candidate_histogram
    )

    differences = []

    for component in reference_components:
        differences.extend(
            compare_component(
                object_path=object_path,
                component=component,
                reference_values=reference_components[component],
                candidate_values=candidate_components[component],
                relative_tolerance=relative_tolerance,
                absolute_tolerance=absolute_tolerance,
            )
        )

    return differences

def parse_arguments():
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare selected histograms in two ROOT output files."
        )
    )

    parser.add_argument(
        "reference",
        help="Reference ROOT file from the unchanged baseline run.",
    )
    parser.add_argument(
        "candidate",
        help="Candidate ROOT file to compare against the baseline.",
    )
    parser.add_argument(
        "--object",
        dest="object_paths",
        action="append",
        required=True,
        help=(
            "Complete ROOT histogram path. "
            "Repeat this option to compare multiple histograms."
        ),
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help="Relative tolerance. Default: 0 for exact comparison.",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="Absolute tolerance. Default: 0 for exact comparison.",
    )
    parser.add_argument(
        "--max-differences",
        type=int,
        default=50,
        help="Maximum number of numerical differences to print.",
    )

    return parser.parse_args()


def print_difference(difference):
    """Print one numerical difference in a readable form."""
    print(
        f"{difference.object_path} "
        f"{difference.component}[{difference.bin_index}]: "
        f"reference={difference.reference:.17g}, "
        f"candidate={difference.candidate:.17g}, "
        f"absolute={difference.absolute_difference:.17g}, "
        f"relative={difference.relative_difference:.17g}"
    )


def main():
    """Compare every requested histogram."""
    arguments = parse_arguments()

    reference_file = open_root_file(arguments.reference)
    candidate_file = open_root_file(arguments.candidate)

    all_differences = []

    try:
        for object_path in arguments.object_paths:
            differences = compare_histograms(
                reference_file=reference_file,
                candidate_file=candidate_file,
                object_path=object_path,
                relative_tolerance=arguments.rtol,
                absolute_tolerance=arguments.atol,
            )

            all_differences.extend(differences)

            if differences:
                print(
                    f"FAIL {object_path}: "
                    f"{len(differences)} differences"
                )
            else:
                print(f"PASS {object_path}")

    finally:
        reference_file.Close()
        candidate_file.Close()

    if not all_differences:
        print("All selected ROOT histograms agree.")
        return 0

    print()
    print(
        f"Found {len(all_differences)} numerical differences "
        "outside tolerance."
    )

    for difference in all_differences[: arguments.max_differences]:
        print_difference(difference)

    omitted = (
        len(all_differences) - arguments.max_differences
    )

    if omitted > 0:
        print(f"... {omitted} additional differences omitted")

    return 1


if __name__ == "__main__":
    sys.exit(main())
