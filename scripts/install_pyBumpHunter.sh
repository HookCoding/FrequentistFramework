#!/bin/bash

set -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

pybh_source="$repo_root/pyBumpHunter"
pybh_environment="$pybh_source/pyBH_env"
environment_python="$pybh_environment/bin/python3"

scientific_setup="$repo_root/scripts/setup_buildAndFit.sh"
find_bh_window="$repo_root/python/FindBHWindow.py"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_file() {
    local required_path="$1"

    if [[ ! -f "$required_path" ]]; then
        fail "Required file is missing: $required_path"
    fi
}

require_directory() {
    local required_path="$1"

    if [[ ! -d "$required_path" ]]; then
        fail "Required directory is missing: $required_path"
    fi
}

verify_environment() {
    local python_executable="$1"

    "$python_executable" - <<'PYTHON_VERIFY'
import matplotlib
import numpy
import pyBumpHunter
import scipy
import uproot

print(f"pyBumpHunter={pyBumpHunter.__file__}")
print(f"numpy={numpy.__version__}")
print(f"scipy={scipy.__version__}")
print(f"matplotlib={matplotlib.__version__}")
print(f"uproot={uproot.__version__}")
PYTHON_VERIFY
}

require_directory "$pybh_source"
require_file "$pybh_source/pyproject.toml"
require_file "$scientific_setup"
require_file "$find_bh_window"

cd "$repo_root" || fail "Could not enter repository root: $repo_root"

# The existing ATLAS setup scripts are not compatible with nounset or errexit.
set +u
set +e
source "$scientific_setup" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    fail "Scientific setup failed with exit code $setup_status"
fi

scientific_python="$(command -v python)"

if [[ -z "$scientific_python" ]]; then
    fail "Scientific Python is unavailable after setup"
fi

scientific_python_version="$(
    "$scientific_python" -c \
        'import platform; print(platform.python_version())'
)"

if [[ "$scientific_python_version" != "3.9.12" ]]; then
    fail \
        "Expected scientific Python 3.9.12, found " \
        "$scientific_python_version"
fi

if [[ -e "$pybh_environment" ]]; then
    if [[ ! -x "$environment_python" ]]; then
        fail \
            "Existing pyBH_env is incomplete. It has been preserved. " \
            "Move it aside explicitly before rebuilding."
    fi

    existing_python_version="$(
        "$environment_python" -c \
            'import platform; print(platform.python_version())'
    )" || fail "Could not determine the existing pyBH_env Python version"

    if [[ "$existing_python_version" != "$scientific_python_version" ]]; then
        fail \
            "Existing pyBH_env uses Python $existing_python_version; expected " \
            "$scientific_python_version. It has been preserved."
    fi

    if ! verify_environment "$environment_python"; then
        fail \
            "Existing pyBH_env failed import validation. It has been " \
            "preserved. Move it aside explicitly before rebuilding."
    fi

    if ! "$environment_python" "$find_bh_window" --help >/dev/null; then
        fail \
            "Existing pyBH_env cannot start FindBHWindow.py. " \
            "It has been preserved."
    fi

    printf '%s\n' \
        "Existing pyBumpHunter environment is valid; no changes were made."

    exit 0
fi

printf 'Creating %s with scientific Python %s\n' \
    "$pybh_environment" \
    "$scientific_python_version"

if ! "$scientific_python" -m venv \
    --system-site-packages \
    "$pybh_environment"
then
    fail "Could not create pyBH_env"
fi

if ! "$environment_python" -m pip install \
    --no-deps \
    --no-build-isolation \
    "$pybh_source"
then
    fail \
        "Could not install pyBumpHunter. The incomplete pyBH_env has " \
        "been preserved for inspection."
fi

if ! verify_environment "$environment_python"; then
    fail \
        "The new pyBH_env failed import validation. It has been " \
        "preserved for inspection."
fi

if ! "$environment_python" "$find_bh_window" --help >/dev/null; then
    fail \
        "The new pyBH_env cannot start FindBHWindow.py. It has been " \
        "preserved for inspection."
fi

printf '%s\n' \
    "pyBumpHunter environment installed and validated successfully."
