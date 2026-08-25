"""Configuration validation for analysis execution.

This module provides focused functions for validating and normalizing
analysis configuration parameters. Each function has explicit inputs and
return values, enabling independent testing.
"""

from __future__ import annotations

from pathlib import Path


def validate_fit_range(rangelow: int, rangehigh: int) -> None:
    """Validate that fit range bounds are valid.

    Args:
        rangelow: Low end of fit range (in GeV)
        rangehigh: High end of fit range (in GeV)

    Raises:
        ValueError: If bounds are invalid (non-positive, reversed, or equal)
    """
    if not isinstance(rangelow, int):
        raise ValueError(f"rangelow must be an integer, got {type(rangelow).__name__}")

    if not isinstance(rangehigh, int):
        raise ValueError(f"rangehigh must be an integer, got {type(rangehigh).__name__}")

    if rangelow <= 0:
        raise ValueError(f"rangelow must be positive, got {rangelow}")

    if rangehigh <= 0:
        raise ValueError(f"rangehigh must be positive, got {rangehigh}")

    if rangelow >= rangehigh:
        raise ValueError(f"rangelow ({rangelow}) must be less than rangehigh ({rangehigh})")


def validate_output_folder(folder: str) -> Path:
    """Validate and create output folder if needed.

    Args:
        folder: Path to output folder (relative or absolute)

    Returns:
        Absolute Path object to folder

    Raises:
        OSError: If folder cannot be created or is not writable
    """
    folder_path = Path(folder).resolve()

    if not folder_path.exists():
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise OSError(f"Could not create output folder {folder_path}: {error}") from error

    if not folder_path.is_dir():
        raise OSError(f"Output path exists but is not a directory: {folder_path}")

    try:
        # Test writeability by creating a temporary marker file
        test_file = folder_path / ".writetest"
        test_file.touch()
        test_file.unlink()
    except OSError as error:
        raise OSError(f"Output folder is not writable: {folder_path}") from error

    return folder_path


def normalize_signal_name(sigmean: int, sigwidth: float) -> str:
    """Normalize signal parameter name based on mass and width.

    Args:
        sigmean: Mean mass in GeV (e.g., 400)
        sigwidth: Width as percentage (e.g., 8.0) or special value -999 for Z'

    Returns:
        Normalized signal name (e.g., "mean400_width8" or "mR400")

    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(sigmean, int):
        raise ValueError(f"sigmean must be an integer, got {type(sigmean).__name__}")

    if sigmean <= 0:
        raise ValueError(f"sigmean must be positive, got {sigmean}")

    if sigwidth == -999:
        # Z' model with parametrized mass
        return f"mR{sigmean}"
    else:
        # Gaussian model with explicit mean and width
        if not isinstance(sigwidth, (int, float)):
            raise ValueError(f"sigwidth must be numeric, got {type(sigwidth).__name__}")

        # Format width: if it's a whole number, use int; else use float
        if isinstance(sigwidth, float) and sigwidth.is_integer():
            width_str = str(int(sigwidth))
        else:
            width_str = str(sigwidth)

        return f"mean{sigmean}_width{width_str}"


def detect_parameter_count(backgroundfile: str) -> int:
    """Detect background-model parameter count from filename.

    Extracts the parameter count (3–10) from filenames like:
    - background_dijetTLA_sixPar.template → 6
    - background_dijetTLA_sevenPar.template → 7

    Args:
        backgroundfile: Path or filename of background XML template

    Returns:
        Detected parameter count (3–10)

    Raises:
        ValueError: If parameter count cannot be detected or is out of range
    """
    filename = Path(backgroundfile).name.lower()

    # Map of text names to parameter counts
    param_map = {
        "threepar": 3,
        "fourpar": 4,
        "fivepar": 5,
        "sixpar": 6,
        "sevenpar": 7,
        "eightpar": 8,
        "ninepar": 9,
        "tenpar": 10,
    }

    for text_name, count in param_map.items():
        if text_name in filename:
            return count

    raise ValueError(
        f"Could not detect parameter count from background file: {backgroundfile}. "
        f"Expected filename containing one of: {', '.join(param_map.keys())}"
    )
