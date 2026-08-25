from __future__ import annotations

from pathlib import Path

import pytest

from python.analysis_templates import replaceinfile


def test_replaceinfile_replaces_matching_patterns(tmp_path: Path) -> None:
    template = tmp_path / "template.xml"
    template.write_text("DATAFILE OUTPUTFILE\n")

    replaceinfile(template, [("DATAFILE", "input.root"), ("OUTPUTFILE", "fit.root")])

    assert template.read_text() == "input.root fit.root\n"


def test_replaceinfile_supports_regular_expression_patterns(tmp_path: Path) -> None:
    template = tmp_path / "template.xml"
    template.write_text("Value=123\n")

    replaceinfile(template, [(r"Value=\d+", "Value=456")])

    assert template.read_text() == "Value=456\n"


def test_replaceinfile_exits_on_invalid_replacement_pattern(tmp_path: Path) -> None:
    template = tmp_path / "template.xml"
    template.write_text("Value\n")

    with pytest.raises(SystemExit):
        replaceinfile(template, [("[", "broken")])
