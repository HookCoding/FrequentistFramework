"""Tests for analysis_config module.

These tests verify configuration validation and normalization functions
using temporary directories for file I/O and synthetic data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from python.analysis_config import (
    detect_parameter_count,
    normalize_signal_name,
    validate_fit_range,
    validate_output_folder,
)


class TestValidateFitRange:
    """Tests for validate_fit_range function."""

    def test_accepts_valid_j100_range(self) -> None:
        """Valid J100 fit range should not raise."""
        validate_fit_range(481, 3000)  # Should not raise

    def test_accepts_valid_j50_range(self) -> None:
        """Valid J50 fit range should not raise."""
        validate_fit_range(344, 2079)  # Should not raise

    def test_rejects_reversed_bounds(self) -> None:
        """Reversed bounds should raise ValueError."""
        with pytest.raises(ValueError, match="must be less than"):
            validate_fit_range(3000, 481)

    def test_rejects_equal_bounds(self) -> None:
        """Equal bounds should raise ValueError."""
        with pytest.raises(ValueError, match="must be less than"):
            validate_fit_range(1000, 1000)

    def test_rejects_negative_rangelow(self) -> None:
        """Negative rangelow should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_fit_range(-100, 1000)

    def test_rejects_negative_rangehigh(self) -> None:
        """Negative rangehigh should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_fit_range(100, -1000)

    def test_rejects_zero_rangelow(self) -> None:
        """Zero rangelow should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_fit_range(0, 1000)

    def test_rejects_zero_rangehigh(self) -> None:
        """Zero rangehigh should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_fit_range(100, 0)

    def test_rejects_float_rangelow(self) -> None:
        """Float rangelow should raise ValueError."""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_fit_range(481.5, 3000)  # type: ignore

    def test_rejects_float_rangehigh(self) -> None:
        """Float rangehigh should raise ValueError."""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_fit_range(481, 3000.5)  # type: ignore


class TestValidateOutputFolder:
    """Tests for validate_output_folder function."""

    def test_creates_new_folder(self, tmp_path: Path) -> None:
        """Non-existent folder should be created."""
        new_folder = tmp_path / "new_run" / "fits" / "J100"
        result = validate_output_folder(str(new_folder))

        assert result.exists()
        assert result.is_dir()
        assert result == new_folder.resolve()

    def test_accepts_existing_folder(self, tmp_path: Path) -> None:
        """Existing folder should be accepted."""
        existing = tmp_path / "existing"
        existing.mkdir()

        result = validate_output_folder(str(existing))

        assert result == existing.resolve()
        assert result.is_dir()

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        """Returned path should be absolute."""
        relative_path = "relative/folder"
        result = validate_output_folder(relative_path)

        assert result.is_absolute()

    def test_rejects_file_path(self, tmp_path: Path) -> None:
        """Existing file should raise error."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(OSError, match="not a directory"):
            validate_output_folder(str(file_path))

    def test_verifies_writeability(self, tmp_path: Path) -> None:
        """Folder should be verified writable."""
        writable_folder = tmp_path / "writable"
        writable_folder.mkdir()

        # This should succeed without raising
        result = validate_output_folder(str(writable_folder))
        assert result == writable_folder.resolve()


class TestNormalizeSignalName:
    """Tests for normalize_signal_name function."""

    def test_gaussian_model(self) -> None:
        """Gaussian model should format as mean_width."""
        result = normalize_signal_name(400, 8.0)
        assert result == "mean400_width8"

    def test_gaussian_model_integer_width(self) -> None:
        """Gaussian with integer width should format cleanly."""
        result = normalize_signal_name(400, 8)
        assert result == "mean400_width8"

    def test_gaussian_model_float_width(self) -> None:
        """Gaussian with non-integer width should preserve precision."""
        result = normalize_signal_name(400, 7.5)
        assert result == "mean400_width7.5"

    def test_zprime_model(self) -> None:
        """Z' model (sigwidth=-999) should format as mR."""
        result = normalize_signal_name(400, -999)
        assert result == "mR400"

    def test_zprime_model_different_mass(self) -> None:
        """Z' model with different mass should be formatted correctly."""
        result = normalize_signal_name(600, -999)
        assert result == "mR600"

    def test_rejects_negative_sigmean(self) -> None:
        """Negative sigmean should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            normalize_signal_name(-400, 8.0)

    def test_rejects_zero_sigmean(self) -> None:
        """Zero sigmean should raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            normalize_signal_name(0, 8.0)

    def test_rejects_non_integer_sigmean(self) -> None:
        """Non-integer sigmean should raise ValueError."""
        with pytest.raises(ValueError, match="must be an integer"):
            normalize_signal_name(400.5, 8.0)  # type: ignore


class TestDetectParameterCount:
    """Tests for detect_parameter_count function."""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("background_dijetTLA_threePar.template", 3),
            ("background_dijetTLA_fourPar.template", 4),
            ("background_dijetTLA_fivePar.template", 5),
            ("background_dijetTLA_sixPar.template", 6),
            ("background_dijetTLA_sevenPar.template", 7),
            ("background_dijetTLA_eightPar.template", 8),
            ("background_dijetTLA_ninePar.template", 9),
            ("background_dijetTLA_tenPar.template", 10),
        ],
    )
    def test_detects_parameter_count(self, filename: str, expected: int) -> None:
        """Should detect parameter count from filename."""
        result = detect_parameter_count(filename)
        assert result == expected

    def test_case_insensitive_detection(self) -> None:
        """Detection should be case-insensitive."""
        result = detect_parameter_count("background_dijetTLA_SIXPAR.template")
        assert result == 6

    def test_detects_from_full_path(self) -> None:
        """Should detect from full file path."""
        result = detect_parameter_count("/config/dijetisrTLA/background_dijetTLA_sixPar.template")
        assert result == 6

    def test_rejects_unknown_parameter_count(self) -> None:
        """Unknown parameter count should raise ValueError."""
        with pytest.raises(ValueError, match="Could not detect parameter count"):
            detect_parameter_count("background_dijetTLA_elevenPar.template")

    def test_rejects_missing_parameter_indicator(self) -> None:
        """Missing parameter indicator should raise ValueError."""
        with pytest.raises(ValueError, match="Could not detect parameter count"):
            detect_parameter_count("background_dijetTLA.template")
