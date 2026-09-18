"""Unit tests for the command-construction/failure-reporting group in run_anaFit.py
(plan section 3, Group A).

These six functions are pure string/print builders pulled out of build_fit_extract() and
execute_checked(): none of them touches ROOT, a file or a subprocess, so this file needs no
fixtures and no LCG environment beyond what conftest.py already puts on sys.path.
"""

import pytest

from run_anaFit import (
    _failure_message,
    _xmlreader_command,
    _quickfit_command,
    _poi_option,
    _mask_options,
    _derived_output_paths,
)


# ---------------------------------------------------------------------------
# _failure_message
# ---------------------------------------------------------------------------

def test_failure_message_signal_killed():
    msg = _failure_message("XMLReader (workspace build) on top.xml", 139, logfile=None)
    assert "killed by signal 11" in msg


def test_failure_message_no_signal_sentence_for_plain_nonzero_exit():
    msg = _failure_message("quickFit on ws.root", 1, logfile=None)
    assert "signal" not in msg


def test_failure_message_includes_logfile_when_given():
    msg = _failure_message("quickFit on ws.root", 1, logfile="run/quickFitLog.log")
    assert "run/quickFitLog.log" in msg


def test_failure_message_omits_logfile_reference_when_absent():
    msg = _failure_message("quickFit on ws.root", 1, logfile=None)
    assert "output is in" not in msg


# ---------------------------------------------------------------------------
# _xmlreader_command / _quickfit_command
# ---------------------------------------------------------------------------

def test_xmlreader_command_exact_string():
    assert _xmlreader_command("run/dijetTLA_fromTemplate.xml") == (
        'xmlAnaWSBuilder/build/bin/XMLReader -x run/dijetTLA_fromTemplate.xml '
        '-o "logy integral" --minimizerStrategy 0'
    )


def test_quickfit_command_exact_string():
    got = _quickfit_command(
        wsfile="run/ws.root",
        poi_option="-p nsig_mean1000_width7.0",
        range_option="--range SBLo_J100yStar06,SBHi_J100yStar06",
        fitresultfile="run/FitResult_anaFit_sixPar_bkgOnly.root",
        logfile="run/quickFitLog_anaFit_sixPar_bkgOnly.log",
    )
    assert got == (
        "quickFit/build/quickFit --chi2fit 1 --poissonerror 1 -f run/ws.root -d combData "
        "-p nsig_mean1000_width7.0 --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 "
        "--saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-6 "
        "--range SBLo_J100yStar06,SBHi_J100yStar06 -o run/FitResult_anaFit_sixPar_bkgOnly.root "
        "&> run/quickFitLog_anaFit_sixPar_bkgOnly.log"
    )


# ---------------------------------------------------------------------------
# _poi_option
# ---------------------------------------------------------------------------

def test_poi_option_with_name():
    assert _poi_option("nsig_mean1000_width7.0") == "-p nsig_mean1000_width7.0"


def test_poi_option_none_gives_empty_string():
    assert _poi_option(None) == ""


# ---------------------------------------------------------------------------
# _mask_options
# ---------------------------------------------------------------------------

def test_mask_options_with_window():
    range_option, maskmin, maskmax = _mask_options((120, 140), "J100yStar06")
    assert range_option == "--range SBLo_J100yStar06,SBHi_J100yStar06"
    assert maskmin == 120
    assert maskmax == 140


def test_mask_options_without_window_gives_both_minus_one():
    range_option, maskmin, maskmax = _mask_options(None, "J100yStar06")
    assert range_option == ""
    assert maskmin == -1
    assert maskmax == -1


# ---------------------------------------------------------------------------
# _derived_output_paths
# ---------------------------------------------------------------------------

def test_derived_output_paths():
    paths = _derived_output_paths("run/FitResult_anaFit_sixPar_bkgOnly.root")
    assert paths == {
        "logfile": "run/quickFitLog_anaFit_sixPar_bkgOnly.log",
        "edmplot": "run/edm_anaFit_sixPar_bkgOnly.pdf",
        "postfitfile": "run/PostFit_anaFit_sixPar_bkgOnly.root",
        "parameterfile": "run/FitParameters_anaFit_sixPar_bkgOnly.root",
    }
    # plot_postfit.cpp:34 independently builds this same name via
    # Form("%s/PostFit_anaFit_%sPar_bkgOnly.root", in_dir, pars_str) with in_dir="run", pars_str="six".
    assert paths["postfitfile"] == "run/PostFit_anaFit_sixPar_bkgOnly.root"
