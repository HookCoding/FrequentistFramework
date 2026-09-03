from __future__ import annotations

import pytest

from python import run_cli

_REPRESENTATIVE_ARGS = [
    "--datafile",
    "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    "--datahist",
    "mjj_Data_2018",
    "--backgroundfile",
    "background.xml",
    "--signalfile",
    "signal.xml",
    "--categoryfile",
    "category.xml",
    "--topfile",
    "top.xml",
    "--wsfile",
    "workspace.root",
    "--sigmean",
    "1200",
    "--sigwidth",
    "8.5",
    "--nbkg",
    "2E8,0,3E8",
    "--rangelow",
    "481",
    "--rangehigh",
    "3000",
    "--outputfile",
    "FitResult.root",
    "--maskthreshold",
    "0.01",
    "--folder",
    "run",
]


def test_build_arg_parser_parses_representative_j100_style_invocation() -> None:
    # Mirrors an actual invocation shape from scripts/run_anaFit_J100.sh:
    # backgroundfile/signalfile present, no --signame, no --dosignal/
    # --dolimit/--doprefit/--sysfile (all left at their defaults).
    parser = run_cli.build_arg_parser()

    args = parser.parse_args(_REPRESENTATIVE_ARGS)

    assert args.datafile == "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root"
    assert args.backgroundfile == "background.xml"
    assert args.signalfile == "signal.xml"
    assert args.rangelow == 481
    assert args.rangehigh == 3000
    assert args.dosignal is False
    assert args.dolimit is False
    assert args.doprefit is False
    assert args.sigmean == 1200
    assert args.sigwidth == 8.5
    assert args.nsig == "0,-1E6,1E6"  # default, not passed explicitly
    # The parser itself leaves signame as whatever was passed (None here) -
    # deriving a default from sigmean/sigwidth is normalize_signal_name()'s
    # job, not build_arg_parser()'s.
    assert args.signame is None
    assert args.maskthreshold == 0.01
    assert args.sysfile is None


def test_build_arg_parser_format_help_does_not_raise() -> None:
    # A regression test for a real bug (caught in review): the --sigwidth
    # help text contained a bare "%", which argparse's help-string
    # expansion (used for placeholders like "%(default)s") chokes on when
    # rendering the *full* help output - parser.format_help()/--help
    # raised ValueError. "%%" is the escaped literal-percent form; the
    # rendered text must contain the original wording with a single "%".
    parser = run_cli.build_arg_parser()

    rendered = parser.format_help()

    assert "Width of signal Gaussian for s+b fit (in %). If -999" in rendered


def test_build_arg_parser_rangehigh_help_does_not_duplicate_start() -> None:
    # A regression test for a real bug (caught in review): --rangehigh's
    # help text read "End Start of fit range (in GeV)" - an accidental
    # duplication/typo, apparently copied from --rangelow's own
    # "Start of fit range (in GeV)" text.
    parser = run_cli.build_arg_parser()
    (rangehigh_action,) = (a for a in parser._actions if a.dest == "rangehigh")

    assert rangehigh_action.help == "End of fit range (in GeV)"


@pytest.mark.parametrize("missing_flag", ["--rangelow", "--rangehigh"])
def test_build_arg_parser_requires_range_flags(
    missing_flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A regression test for a real bug (caught in review): --rangelow/
    # --rangehigh were parsed as optional, but run_anaFit() immediately
    # does "rangehigh - rangelow" arithmetic, so omitting either would
    # previously parse to None and crash later with a confusing
    # TypeError instead of a clear argparse usage error at parse time.
    parser = run_cli.build_arg_parser()
    args = list(_REPRESENTATIVE_ARGS)
    flag_index = args.index(missing_flag)
    del args[flag_index : flag_index + 2]  # drop the flag and its value

    with pytest.raises(SystemExit):
        parser.parse_args(args)

    assert missing_flag in capsys.readouterr().err


def test_build_arg_parser_description_uses_argparse_prog_placeholder() -> None:
    # A regression test for a real bug (caught in review): argparse does
    # not substitute the old optparse-style "%prog" placeholder in
    # `description` - it would appear literally in --help output.
    # "%(prog)s" is the argparse-native placeholder, and IS substituted.
    parser = run_cli.build_arg_parser()
    assert "%prog" not in parser.description

    rendered = parser.format_help()

    assert f"{parser.prog} [options]" in rendered


def test_normalize_signal_name_derives_default_for_normal_width() -> None:
    assert run_cli.normalize_signal_name(1200, 8.5, None) == "mean1200_width8.5"


def test_normalize_signal_name_preserves_integer_valued_float_width() -> None:
    # 7.0 must format as "7.0", not "7" -- str(7.0) == "7.0" in the "%s"-
    # style formatting this function uses. Easy to accidentally "clean up"
    # into "%g"-style formatting, which would silently turn 7.0 into 7.
    assert run_cli.normalize_signal_name(1000, 7.0, None) == "mean1000_width7.0"


def test_normalize_signal_name_uses_zprime_naming_when_sigwidth_is_minus_999() -> None:
    assert run_cli.normalize_signal_name(1400, -999, None) == "mR1400"


def test_normalize_signal_name_respects_explicit_override() -> None:
    # An explicit signame must survive unchanged, even though it doesn't
    # match what the default-naming logic would have derived for the same
    # sigmean/sigwidth.
    assert run_cli.normalize_signal_name(1200, 8.5, "customSignal") == "customSignal"
