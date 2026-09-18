"""Unit tests for main()'s split in run_anaFit.py (plan section 3, tail of the plan).

main() used to build its argument parser and load the signal systematics dict inline; both are
now their own functions. _build_parser() is checked against the exact argument list
scripts/run_anaFit_run2.sh passes - this is the only place that boundary between the shell and
the Python was checked at all before this test existed.
"""

import json

import pytest

from run_anaFit import _build_parser, _load_systdict


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------

def test_build_parser_parses_the_j100_driver_argument_list():
    # scripts/run_anaFit_run2.sh:90-106, one rangelow/pars iteration, dosignal=dolimit=0,
    # doprefit=1 (so $flags is just "--doprefit").
    argv = [
        "--datafile", "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
        "--datahist", "hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
        "--backgroundfile", "config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template",
        "--signalfile", "config/dijetTLA/signal/signal_dijetTLA.template",
        "--categoryfile", "config/dijetTLA/category_dijetTLA.template",
        "--topfile", "config/dijetTLA/dijetTLA_J100yStar06.template",
        "--wsfile", "run/run_481_3000_sixPar/dijetTLA_combWS_sixPar.root",
        "--sigmean", "1000",
        "--sigwidth", "8",
        "--nbkg", "dummy",
        "--rangelow", "481",
        "--rangehigh", "3000",
        "--outputfile", "run/run_481_3000_sixPar/FitResult_anaFit_sixPar_bkgOnly.root",
        "--maskthreshold", "0.01",
        "--folder", "run/run_481_3000_sixPar",
        "--rebinfile", "Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
        "--rebinhist", "Dijet mass distribution (J100)/Hist1D_y1",
        "--doprefit",
    ]

    args = _build_parser().parse_args(argv)

    assert args.rangelow == 481 and isinstance(args.rangelow, int)
    assert args.rangehigh == 3000 and isinstance(args.rangehigh, int)
    assert args.sigmean == 1000 and isinstance(args.sigmean, int)
    assert args.sigwidth == 8.0 and isinstance(args.sigwidth, float)
    assert args.maskthreshold == pytest.approx(0.01)
    assert args.nbkg == "dummy"  # kept as a string, not parsed as a number
    # spaces (and the leading capital) survive argparse's own tokenising, not just the shell's.
    assert args.rebinhist == "Dijet mass distribution (J100)/Hist1D_y1"
    assert args.doprefit is True
    assert args.dosignal is False
    assert args.dolimit is False


def test_build_parser_defaults_for_unset_store_true_flags():
    argv = [
        "--datafile", "d", "--datahist", "h", "--topfile", "t", "--categoryfile", "c",
        "--wsfile", "w", "--outputfile", "o", "--nbkg", "n",
    ]
    args = _build_parser().parse_args(argv)
    assert args.dosignal is False
    assert args.dolimit is False
    assert args.doprefit is False


# ---------------------------------------------------------------------------
# _load_systdict
# ---------------------------------------------------------------------------

def test_load_systdict_returns_none_without_sysfile():
    assert _load_systdict(None, 1000) is None


def test_load_systdict_returns_entry_keyed_by_sigmean(tmp_path):
    sysfile = tmp_path / "syst.json"
    sysfile.write_text(json.dumps({"1000": {"nominal_mean": 1000.0}, "2000": {"nominal_mean": 2000.0}}))

    assert _load_systdict(str(sysfile), 1000) == {"nominal_mean": 1000.0}


def test_load_systdict_raises_where_the_file_is_read_when_sigmean_absent(tmp_path):
    sysfile = tmp_path / "syst.json"
    sysfile.write_text(json.dumps({"2000": {"nominal_mean": 2000.0}}))

    with pytest.raises(KeyError):
        _load_systdict(str(sysfile), 1000)
