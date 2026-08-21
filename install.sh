#!/bin/bash

set -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$script_dir"

readonly roofit_extensions_revision="ba94bfcbfa4f4a4e3541ade09580399e409e8514"

readonly dependencies=(
    "xmlAnaWSBuilder"
    "quickFit"
    "workspaceCombiner"
    "pyBumpHunter"
)

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'USAGE'
Usage:
    bash install.sh --check

Modes:
    --check
        Validate submodules, pinned revisions, nested RooFitExtensions
        checkouts, scientific setup files, and installer prerequisites.

        This mode is read-only. It does not clone, pull, build, install,
        delete, stage, or modify files.

The non-destructive build mode will be added only after the complete
read-only installation contract passes.
USAGE
}

require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        fail "Required command is unavailable: $command_name"
    fi
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

git_revision() {
    local checkout_path="$1"

    git -C "$checkout_path" rev-parse HEAD 2>/dev/null
}

verify_no_tracked_changes() {
    local checkout_path="$1"
    local tracked_changes

    tracked_changes="$(
        git -C "$checkout_path" status \
            --short \
            --untracked-files=no
    )" || fail "Could not inspect Git status: $checkout_path"

    if [[ -n "$tracked_changes" ]]; then
        printf '%s\n' "$tracked_changes" >&2
        fail "Tracked source modifications found in $checkout_path"
    fi
}

verify_parent_gitlink() {
    local dependency="$1"
    local expected_revision
    local actual_revision
    local index_entry
    local mode
    local index_revision

    expected_revision="$(
        git -C "$repo_root/$dependency" rev-parse HEAD
    )" || fail "Could not read dependency revision: $dependency"

    index_entry="$(
        git -C "$repo_root" ls-files --stage -- "$dependency"
    )" || fail "Could not read Git index entry: $dependency"

    if [[ -z "$index_entry" ]]; then
        fail "Missing Git index entry for dependency: $dependency"
    fi

    read -r mode index_revision _stage _path <<<"$index_entry"

    if [[ "$mode" != "160000" ]]; then
        fail "Dependency is not recorded as a gitlink: $dependency"
    fi

    if [[ "$index_revision" != "$expected_revision" ]]; then
        fail \
            "Dependency revision differs from its gitlink: " \
            "$dependency"
    fi

    actual_revision="$(git_revision "$repo_root/$dependency")"

    printf 'PASS %-20s gitlink=%s revision=%s\n' \
        "$dependency" \
        "$mode" \
        "$actual_revision"
}

verify_roofit_extensions() {
    local dependency="$1"
    local checkout_path="$repo_root/$dependency/RooFitExtensions"
    local actual_revision

    require_directory "$checkout_path"
    require_file "$checkout_path/CMakeLists.txt"

    actual_revision="$(git_revision "$checkout_path")"

    if [[ "$actual_revision" != "$roofit_extensions_revision" ]]; then
        fail \
            "$dependency/RooFitExtensions revision mismatch: expected " \
            "$roofit_extensions_revision, found $actual_revision"
    fi

    verify_no_tracked_changes "$checkout_path"

    printf 'PASS %-20s RooFitExtensions=%s\n' \
        "$dependency" \
        "$actual_revision"
}

verify_dependency() {
    local dependency="$1"
    local checkout_path="$repo_root/$dependency"

    require_directory "$checkout_path"

    if ! git -C "$checkout_path" rev-parse --git-dir >/dev/null 2>&1; then
        fail "Dependency is not a readable Git checkout: $dependency"
    fi

    verify_no_tracked_changes "$checkout_path"
    verify_parent_gitlink "$dependency"
}

run_check() {
    cd "$repo_root" || fail "Could not enter repository root: $repo_root"

    require_command git
    require_command bash
    require_command cmake

    require_file "$repo_root/.gitmodules"
    require_file "$repo_root/scripts/setup_buildAndFit.sh"
    require_file "$repo_root/scripts/install_pyBumpHunter.sh"
    require_file "$repo_root/python/FindBHWindow.py"

    printf '%s\n' 'Checking parent dependency gitlinks...'

    for dependency in "${dependencies[@]}"; do
        verify_dependency "$dependency"
    done

    printf '%s\n' 'Checking nested RooFitExtensions checkouts...'

    for dependency in \
        xmlAnaWSBuilder \
        quickFit \
        workspaceCombiner
    do
        verify_roofit_extensions "$dependency"
    done

    require_file "$repo_root/xmlAnaWSBuilder/setup_lxplus.sh"
    require_file "$repo_root/quickFit/setup_lxplus.sh"
    require_file "$repo_root/workspaceCombiner/setup_lxplus.sh"
    require_file "$repo_root/pyBumpHunter/pyproject.toml"

    printf '%s\n' 'Installation contract check passed.'
    printf '%s\n' 'No files were modified.'
}

if [[ $# -ne 1 ]]; then
    usage
    exit 2
fi

case "$1" in
    --check)
        run_check
        ;;
    --help|-h)
        usage
        ;;
    *)
        usage >&2
        fail "Unsupported installer mode: $1"
        ;;
esac
