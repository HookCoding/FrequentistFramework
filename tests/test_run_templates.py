from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

from python import run_templates


def test_replaceinfile_applies_ordered_regex_substitutions(
    tmp_path: Path,
) -> None:
    # Chaining PLACEHOLDER_A -> PLACEHOLDER_B -> final_value (rather than
    # two independent substitutions) proves substitutions apply in order
    # against the already-modified text, not all at once against the
    # original.
    target_file = tmp_path / "template.xml"
    target_file.write_text("PLACEHOLDER_A\n", encoding="utf-8")

    run_templates.replaceinfile(
        str(target_file),
        [("PLACEHOLDER_A", "PLACEHOLDER_B"), ("PLACEHOLDER_B", "final_value")],
    )

    assert target_file.read_text(encoding="utf-8") == "final_value\n"


def test_prepare_run_templates_stages_templates_for_a_representative_case(
    tmp_path: Path,
) -> None:
    # prepare_run_templates() is plainly importable and callable directly
    # now - no run_anaFit() coordinator, no ROOT/PreFit stubbing needed
    # for this doprefit=False, signalfile=None case.
    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    wsfile = output_folder / "workspace.root"

    result = run_templates.prepare_run_templates(
        folder=str(output_folder),
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        backgroundfile=str(backgroundfile),
        signalfile=None,
        signame="test_signal",
        wsfile=str(wsfile),
        sigmean=1000,
        sigwidth=7.0,
        datafile=str(datafile),
        datahist="directory/histogram",
        rangelow=481,
        rangehigh=3000,
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        doprefit=False,
        systdict=None,
    )

    tmptopfile = output_folder / "dijetTLA_fromTemplate.xml"
    tmpcategoryfile = output_folder / "category_dijetTLA_fromTemplate.xml"
    tmpbackgroundfile = output_folder / "background_dijetTLA_fromTemplate.xml"
    # Computed unconditionally in production regardless of whether
    # signalfile was actually provided - see the categoryfile assertion
    # below, which expects this same value for the SIGNALFILE placeholder.
    tmpsignalfile = output_folder / "signal_dijetTLA_fromTemplate.xml"

    xml_categoryfile = os.path.relpath(str(tmpcategoryfile), os.getcwd())
    xml_wsfile = os.path.relpath(str(wsfile), os.getcwd())
    xml_backgroundfile = os.path.relpath(str(tmpbackgroundfile), os.getcwd())
    xml_signalfile = os.path.relpath(str(tmpsignalfile), os.getcwd())

    assert result == (str(tmptopfile), str(tmpcategoryfile), xml_categoryfile, xml_wsfile)

    assert tmptopfile.read_text(encoding="utf-8") == (
        f"{xml_categoryfile}\n{xml_wsfile}\ntest_signal\n"
    )
    assert tmpcategoryfile.read_text(encoding="utf-8") == (
        f"{xml_backgroundfile}\n{datafile}\ndirectory/histogram\n481\n3000\n"
        f"2519\n1.0E+03, 0, 2.0E+03\n0, -1.0E+03, 1.0E+03\ntest_signal\n{xml_signalfile}\n"
    )
    # backgroundfile itself is copied through unmodified (no doprefit, so
    # no PAR substitution) - only referenced by the categoryfile above.
    assert tmpbackgroundfile.read_text(encoding="utf-8") == "background template\n"


def _install_fake_prefitter(
    monkeypatch: pytest.MonkeyPatch,
    captured_kwargs: dict[str, object],
    fit_return: tuple[list[float], float],
) -> None:
    class FakePreFitter:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

        def Fit(self):
            return fit_return

    fake_prefit_module = ModuleType("PreFit")
    fake_prefit_module.PreFitter = FakePreFitter
    monkeypatch.setitem(sys.modules, "PreFit", fake_prefit_module)


def test_prepare_run_templates_prefit_seeds_background_file_from_fitted_parameters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    # "sixPar" matches only the "six" branch of the elif chain -> nPars=6,
    # avoiding the "three"/"four" double-match quirk exercised separately
    # below.
    backgroundfile = tmp_path / "background_sixPar.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text(
        '<!-- <ModelItem name="commented_out" [PAR1,-99,99] /> -->\n'
        '<ModelItem name="par1" value="[PAR1,-5,5]" />\n'
        '<ModelItem name="par2" value="[PAR2,-6.5,6.5]" />\n',
        encoding="utf-8",
    )
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    captured_prefitter_kwargs: dict[str, object] = {}
    _install_fake_prefitter(
        monkeypatch,
        captured_prefitter_kwargs,
        ([11.0, 22.0, 33.0, 44.0, 55.0, 66.0], 12345.0),
    )

    result = run_templates.prepare_run_templates(
        folder=str(output_folder),
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        backgroundfile=str(backgroundfile),
        signalfile=None,
        signame="test_signal",
        wsfile=str(output_folder / "workspace.root"),
        sigmean=1000,
        sigwidth=7.0,
        datafile=str(datafile),
        datahist="directory/histogram",
        rangelow=481,
        rangehigh=3000,
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        doprefit=True,
        systdict=None,
    )

    assert result[0] == str(output_folder / "dijetTLA_fromTemplate.xml")

    # nPars=6 -> default range [1, -30, -30, -30, -30, -30]/[1, 30, 30, 30, 30, 30],
    # with PAR1 and PAR2's ranges (both index 0 and 1) overridden by the
    # parsed background file's two (uncommented) ModelItem lines - the
    # commented-out PAR1 line above is skipped by the "<!--" guard.
    assert captured_prefitter_kwargs["nPars"] == 6
    assert captured_prefitter_kwargs["parRangeLow"] == [-5.0, -6.5, -30, -30, -30, -30]
    assert captured_prefitter_kwargs["parRangeHigh"] == [5.0, 6.5, 30, 30, 30, 30]
    assert captured_prefitter_kwargs["nRetries1"] == 2000 * 6
    assert captured_prefitter_kwargs["nRetries2"] == 2 * 6
    assert captured_prefitter_kwargs["datafile"] == str(datafile)
    assert captured_prefitter_kwargs["xMin"] == 481
    assert captured_prefitter_kwargs["xMax"] == 3000

    # Real, verified quirk: the substitution loop does a plain
    # replaceinfile(tmpbackgroundfile, [("PAR1", "11.0")]) per parameter -
    # a naive substring/regex swap of the literal text "PARn", not a
    # replacement of the whole "[PARn,lo,hi]" range annotation. The
    # annotation brackets survive in the output with just the "PARn"
    # token inside them replaced (including inside the commented-out
    # line, since replaceinfile operates over the whole file text, blind
    # to comments). This is existing behavior, preserved exactly by the
    # move - not something this chunk may "clean up".
    tmpbackgroundfile = output_folder / "background_dijetTLA_fromTemplate.xml"
    assert tmpbackgroundfile.read_text(encoding="utf-8") == (
        '<!-- <ModelItem name="commented_out" [11.0,-99,99] /> -->\n'
        '<ModelItem name="par1" value="[11.0,-5,5]" />\n'
        '<ModelItem name="par2" value="[22.0,-6.5,6.5]" />\n'
    )

    # PreFitter's fitted nbkg is folded into the NBKG placeholder as
    # "<value>, 0, <2x value>" - confirmed via the categoryfile it feeds.
    tmpcategoryfile = output_folder / "category_dijetTLA_fromTemplate.xml"
    assert "1.2E+04, 0, 2.5E+04" in tmpcategoryfile.read_text(encoding="utf-8")


def test_prepare_run_templates_prefit_npars_detection_matching_both_three_and_four_resolves_to_four(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Regression test for a real, verified quirk: nPars detection is a
    # standalone "if 'three' in backgroundfile: nPars = 3" followed by a
    # *separate* elif chain covering "four" through "ten" - not one
    # unified if/elif ladder. A background-file path matching both
    # "three" and "four" currently resolves to nPars=4, not 3, because
    # the "four" elif branch (part of the second, independent if/elif
    # chain) runs after the standalone "three" check unconditionally
    # sets nPars=3, and overwrites it. This must survive verbatim - the
    # move must not unify this structure.
    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background_threefour.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    captured_prefitter_kwargs: dict[str, object] = {}

    def fit_return() -> tuple[list[float], float]:
        return [0.0] * captured_prefitter_kwargs["nPars"], 1.0

    class FakePreFitter:
        def __init__(self, **kwargs):
            captured_prefitter_kwargs.update(kwargs)

        def Fit(self):
            return fit_return()

    fake_prefit_module = ModuleType("PreFit")
    fake_prefit_module.PreFitter = FakePreFitter
    monkeypatch.setitem(sys.modules, "PreFit", fake_prefit_module)

    run_templates.prepare_run_templates(
        folder=str(output_folder),
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        backgroundfile=str(backgroundfile),
        signalfile=None,
        signame="test_signal",
        wsfile=str(output_folder / "workspace.root"),
        sigmean=1000,
        sigwidth=7.0,
        datafile=str(datafile),
        datahist="directory/histogram",
        rangelow=481,
        rangehigh=3000,
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        doprefit=True,
        systdict=None,
    )

    assert captured_prefitter_kwargs["nPars"] == 4


def test_prepare_run_templates_stages_signal_template_with_systematic_placeholders(
    tmp_path: Path,
) -> None:
    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background.template"
    signalfile = tmp_path / "signal.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    signalfile.write_text(
        "SIGNAME\nSIGMEAN\nSIGWIDTH\nNOMINAL_MEAN\nNOMINAL_WIDTH\n"
        "NOMINAL_ALPHAL\nNOMINAL_ALPHAH\nNOMINAL_NL\nNOMINAL_NH\n"
        "[MAG_SCALE_JES]\n[MAG_RESOLUTION_JER]\n[MAG_SCALE_UNLISTED]\n",
        encoding="utf-8",
    )
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    systdict = {
        "nominal_mean": 1234.5,
        "nominal_sigma": 12.3,
        "nominal_alpha_l": 1.1,
        "nominal_alpha_h": 1.2,
        "nominal_n_l": 5,
        "nominal_n_h": 6,
        "unc_mean_sources": {"JES": 0.02},
        "unc_sigma_sources": {"JER": 0.03},
    }

    run_templates.prepare_run_templates(
        folder=str(output_folder),
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        backgroundfile=str(backgroundfile),
        signalfile=str(signalfile),
        signame="test_signal",
        wsfile=str(output_folder / "workspace.root"),
        sigmean=1000,
        sigwidth=7.0,
        datafile=str(datafile),
        datahist="directory/histogram",
        rangelow=481,
        rangehigh=3000,
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        doprefit=False,
        systdict=systdict,
    )

    tmpsignalfile = output_folder / "signal_dijetTLA_fromTemplate.xml"
    assert tmpsignalfile.read_text(encoding="utf-8") == (
        "test_signal\n1000\n7.0\n1234.5\n12.3\n1.1\n1.2\n5\n6\n[0.02]\n[0.03]\n[0]\n"
    )
