REQUIRED_PATHS = (
    "scripts/run_anaFit_J100.sh",
    "scripts/run_anaFit_J50.sh",
    "scripts/setup_buildAndFit.sh",
    "scripts/quality_check.py",
    "python/analysis_reference.py",
    "python/repo_utils.py",
    "scripts/compare_root_outputs.py",
    "tests/test_analysis_reference.py",
    "tests/test_compare_root_outputs.py",
    "tests/test_repo_utils.py",
    "tests/references/analysis_reference.json",
    "tests/references/repo_snapshot.json",
    "doc/TIER1_SYSTEM.md",
    "doc/TIER1_ENVIRONMENT_PROVENANCE.md",
    "doc/ACTIVITY_LOG.md",
)

OPTIONAL_PATHS = (
    "xmlAnaWSBuilder/setup_lxplus.sh",
    "quickFit/setup_lxplus.sh",
)

WORKFLOWS = {
    "J100": {
        "script": "scripts/run_anaFit_J100.sh",
        "input": "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
        "fit_dir": "run/fits/J100/run_481_3000_sixPar",
        "log": "quickFitLog_anaFit_sixPar_bkgOnly.log",
    },
    "J50": {
        "script": "scripts/run_anaFit_J50.sh",
        "input": "Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
        "fit_dir": "run/fits/J50/run_344_2079_sixPar",
        "log": "quickFitLog_anaFit_sixPar_bkgOnly.log",
    },
}
