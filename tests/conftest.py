"""pytest configuration for the J100/J50 fit-path unit suite.

RUN THIS AFTER `. setup.sh` (or `. scripts/setup_buildAndFit.sh`), from the repository root:

    . setup.sh
    python3 -m pytest tests -q

The LCG_102a view is not optional. `python/ExtractPostfitFromWS.py` and
`python/ExtractFitParameters.py` both do `from ROOT import *`, and ROOT 6.40 - which is what the
plain lxplus system python3 carries - refuses a wildcard import outright:

    ImportError: Wildcard import e.g. `from module import *` is bad practice, so it is
    disallowed in ROOT. Please import explicitly.

The view supplies ROOT 6.26/08, which accepts it. The view also supplies pytest 7.0.1; a bare
shell instead picks up pytest 8.4.2 from ~/.local, which is broken here (it dies importing
pygments). Sourcing setup.sh first puts the view ahead of user-site on sys.path and resolves
both.

`python/` is not a package and must not become one - `run_anaFit.py` is executed as a program,
which is how `python/` lands on sys.path at runtime and how its three sibling imports resolve.
The path insertion below reproduces that for the tests, and nothing else.
"""

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"

sys.path.insert(0, str(REPO_ROOT / "python"))


@pytest.fixture(autouse=True)
def _preserve_root_globals():
    """Stop one test's ROOT global state leaking into every test after it.

    `PreFitter.__init__` sets gErrorIgnoreLevel=6001 and SetDefaultMaxFunctionCalls(50000)
    process-wide (PreFit.py:35-37), so a single construction would silence ROOT diagnostics for
    the rest of the session and make later tests' pass/fail depend on collection order.
    """
    import ROOT

    saved_ignore = ROOT.gErrorIgnoreLevel
    saved_calls = ROOT.Math.MinimizerOptions.DefaultMaxFunctionCalls()
    try:
        yield
    finally:
        ROOT.gErrorIgnoreLevel = saved_ignore
        ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(saved_calls)


@pytest.fixture(autouse=True)
def _run_from_repo_root(monkeypatch):
    """Several modules hardcode repository-relative paths (run_anaFit.py:97,123,147,258), so the
    code under test only works with the repository root as the working directory. pytest's own
    rootdir is not necessarily that, and tmp_path fixtures change it for some tests."""
    monkeypatch.chdir(REPO_ROOT)
