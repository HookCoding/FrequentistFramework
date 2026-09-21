"""derived_outputs() against the two recorded baselines.

The point of these tests is not that the string manipulation works - it is that the list of
files run_anaFit() deletes stays equal to the list it produces. Both baselines record the
directory listing of a real run, so a product added to run_anaFit.py without being added to
run_outputs.py makes these fail. That is the failure mode that would quietly reintroduce
KNOWN_ISSUES.md issue 49.

Run: python3 -m pytest tests/test_run_outputs.py

No ROOT and no ATLAS environment - run_outputs.py imports nothing but the standard library, so
the plain lxplus system python3 runs these, which is also the interpreter tests/repro.py needs.
Deliberately not the repository's gitignored .venv: that venv is a local artefact, absent from a
fresh clone, and a shell with it active is exactly the shell `repro.py check` refuses.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from run_outputs import derived_outputs  # noqa: E402

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

# The arguments the two Run 2 drivers pass, read off scripts/run_anaFit_run2*.sh.
ANALYSES = {
    "J100": {"folder": "run/run_481_3000_sixPar"},
    "J50": {"folder": "run/run_J50_302_2997_sixPar"},
}
for _spec in ANALYSES.values():
    _spec["wsfile"] = _spec["folder"] + "/dijetTLA_combWS_sixPar.root"
    _spec["outputfile"] = _spec["folder"] + "/FitResult_anaFit_sixPar_bkgOnly.root"
    _spec["sigwidth"] = 8  # neither driver is in Z' mode
    _spec["dolimit"] = False


def recorded_listing(analysis):
    """The run folder as tests/baseline_<analysis>.json recorded it, minus the one file
    derived_outputs() deliberately leaves alone."""
    with open(os.path.join(TESTS_DIR, "baseline_%s.json" % analysis)) as f:
        listing = json.load(f)["directory_listing"]
    return set(listing) - {"AnaWSBuilder.dtd"}


def derived_basenames(analysis):
    spec = ANALYSES[analysis]
    return set(os.path.basename(p) for p in derived_outputs(**spec))


def test_j50_derived_set_is_exactly_its_recorded_run():
    """J50's recorded run masked, so its listing is the complete product set - every name
    derived_outputs() returns and no other."""
    assert derived_basenames("J50") == recorded_listing("J50")


def test_j100_recorded_run_is_the_unmasked_half():
    """J100 passed p(chi2) first time and never entered the masking path, so its listing is a
    strict subset - and the difference is exactly that path's products: the masked twins and
    BHresults.json, which FindBHWindow.py writes only when it runs. Nothing else may differ,
    or derived_outputs() is naming a file no run produces."""
    derived, recorded = derived_basenames("J100"), recorded_listing("J100")
    assert recorded < derived
    assert derived - recorded == {
        "BHresults.json",
        "FitResult_anaFit_sixPar_bkgOnly_masked.root",
        "PostFit_anaFit_sixPar_bkgOnly_masked.root",
        "FitParameters_anaFit_sixPar_bkgOnly_masked.root",
        "quickFitLog_anaFit_sixPar_bkgOnly_masked.log",
        "edm_anaFit_sixPar_bkgOnly_masked.pdf",
        "dijetTLA_combWS_sixPar_masked.root",
        "dijetTLA_combWS_sixPar_masked.pdf",
        "dijetTLA_fromTemplate_masked.xml",
        "category_dijetTLA_fromTemplate_masked.xml",
    }


def test_masked_twins_are_returned_even_for_a_run_that_will_not_mask():
    """The whole point of the fix: a run that does not mask still deletes the masked names,
    because their presence is what the drivers read as 'this run masked'."""
    names = derived_basenames("J100")
    assert "PostFit_anaFit_sixPar_bkgOnly_masked.root" in names
    assert "FitParameters_anaFit_sixPar_bkgOnly_masked.root" in names
    assert "BHresults.json" in names


def test_zprime_mode_renames_the_top_and_category_cards():
    names = set(os.path.basename(p) for p in derived_outputs(
        folder="run/x", wsfile="run/x/ws.root",
        outputfile="run/x/FitResult_anaFit_fivePar.root",
        sigmean=550, sigwidth=-999))
    assert "dijetTLA_fromTemplate_mR550.xml" in names
    assert "category_dijetTLA_fromTemplate_mR550.xml" in names
    # The background and signal cards are not renamed in Z' mode.
    assert "background_dijetTLA_fromTemplate.xml" in names
    assert "signal_dijetTLA_fromTemplate.xml" in names


def test_limits_file_only_when_limits_are_requested():
    spec = dict(ANALYSES["J100"])
    assert not any("Limits" in p for p in derived_outputs(**spec))
    spec["dolimit"] = True
    assert any("Limits" in p for p in derived_outputs(**spec))


def test_every_path_is_inside_the_run_folder():
    """A deletion list is about to be built from this. Nothing in it may point outside the
    folder the run owns."""
    for analysis, spec in ANALYSES.items():
        for path in derived_outputs(**spec):
            assert os.path.dirname(path) == spec["folder"], (analysis, path)


def test_the_dtd_symlink_is_never_returned():
    for analysis in ANALYSES:
        assert "AnaWSBuilder.dtd" not in derived_basenames(analysis)
