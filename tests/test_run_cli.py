from __future__ import annotations

from python import run_cli


def test_build_arg_parser_parses_representative_j100_style_invocation() -> None:
    # Mirrors an actual invocation shape from scripts/run_anaFit_J100.sh:
    # backgroundfile/signalfile present, no --signame, no --dosignal/
    # --dolimit/--doprefit/--sysfile (all left at their defaults).
    parser = run_cli.build_arg_parser()

    args = parser.parse_args(
        [
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
    )

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


def test_build_arg_parser_description_uses_argparse_prog_placeholder() -> None:
    # A regression test for a real bug (caught in review): argparse does
    # not substitute the old optparse-style "%prog" placeholder in
    # `description` - it would appear literally in --help output.
    # "%(prog)s" is the argparse-native placeholder, and IS substituted.
    #
    # Rendered in isolation via the formatter's add_text()/format_help(),
    # not parser.format_help()/print_help() directly, because a separate,
    # pre-existing, unrelated bug in one of the --sigwidth help text
    # (a stray literal "%" that argparse's help-string expansion chokes
    # on) makes the *full* help output crash - out of scope for this fix
    # per doc/TIER3_COMPLETION_PLAN.md's guardrail against fixing
    # pre-existing issues noticed incidentally; noted in the activity log
    # instead.
    parser = run_cli.build_arg_parser()
    assert "%prog" not in parser.description

    formatter = parser._get_formatter()
    formatter.add_text(parser.description)
    rendered = formatter.format_help().strip()

    assert rendered == f"{parser.prog} [options]"


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
