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
    bash install.sh --build

Modes:
    --check
        Validate submodules, pinned revisions, nested RooFitExtensions
        checkouts, scientific setup files, and installer prerequisites.

        This mode is read-only. It does not clone, pull, build, install,
        delete, stage, or modify files.

    --build
        Run the validated installation checks, establish the authoritative
        LCG 102a environment, and build the prepared dependencies without
        deleting repositories or build directories.

Environment:
    INSTALL_JOBS
        Number of parallel CMake build jobs. Defaults to 4.
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

setup_scientific_environment() {
    local setup_status
    local python_version
    local root_version

    set +e
    set +u
    source "$repo_root/scripts/setup_buildAndFit.sh" >/dev/null
    setup_status=$?

    if (( setup_status != 0 )); then
        fail "Scientific setup failed with exit code $setup_status"
    fi

    require_command python
    require_command root-config
    require_command cmake

    python_version="$(
        python -c 'import platform; print(platform.python_version())'
    )"

    root_version="$(root-config --version)"

    if [[ "$python_version" != "3.9.12" ]]; then
        fail "Expected scientific Python 3.9.12, found $python_version"
    fi

    if [[ "$root_version" != "6.26/08" ]]; then
        fail "Expected ROOT 6.26/08, found $root_version"
    fi

    printf 'Scientific environment: Python %s, ROOT %s\n' \
        "$python_version" \
        "$root_version"
}


verify_nonempty_file() {
    local output_path="$1"

    if [[ ! -s "$output_path" ]]; then
        fail "Required build output is missing or empty: $output_path"
    fi
}


verify_executable_file() {
    local output_path="$1"

    verify_nonempty_file "$output_path"

    if [[ ! -x "$output_path" ]]; then
        fail "Required build output is not executable: $output_path"
    fi
}


build_roofit_extensions() {
    local dependency="$1"
    local source_dir="$repo_root/$dependency/RooFitExtensions"
    local build_dir="$source_dir/build"
    local parent_lib_dir="$repo_root/$dependency/lib"
    local parent_cmake_dir="$repo_root/$dependency/cmake"
    local configure_status
    local build_status

    printf '\nBuilding %s/RooFitExtensions...\n' "$dependency"

    mkdir -p \
        "$build_dir" \
        "$parent_lib_dir" \
        "$parent_cmake_dir" \
        || fail "Could not create local build-output directories"

    cmake \
        -S "$source_dir" \
        -B "$build_dir" \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON

    configure_status=$?

    if (( configure_status != 0 )); then
        fail \
            "$dependency/RooFitExtensions configuration failed with " \
            "exit code $configure_status"
    fi

    cmake --build "$build_dir" --parallel "$install_jobs"
    build_status=$?

    if (( build_status != 0 )); then
        fail \
            "$dependency/RooFitExtensions build failed with " \
            "exit code $build_status"
    fi

    verify_nonempty_file "$build_dir/libRooFitExtensions.so"
    verify_nonempty_file "$build_dir/libRooFitExtensions_rdict.pcm"
    verify_nonempty_file "$build_dir/libRooFitExtensions.rootmap"
    verify_nonempty_file "$build_dir/RooFitExtensionsConfig.cmake"

    cp \
        "$build_dir/libRooFitExtensions.so" \
        "$build_dir/libRooFitExtensions_rdict.pcm" \
        "$build_dir/libRooFitExtensions.rootmap" \
        "$parent_lib_dir/" \
        || fail \
            "Could not copy RooFitExtensions libraries for $dependency"

    cp \
        "$build_dir/RooFitExtensionsConfig.cmake" \
        "$parent_cmake_dir/RooFitExtensionsConfig.cmake" \
        || fail \
            "Could not copy the RooFitExtensions CMake configuration " \
            "for $dependency"

    printf 'PASS %s/RooFitExtensions\n' "$dependency"
}


build_cpp_dependency() {
    local dependency="$1"
    local source_dir="$repo_root/$dependency"
    local build_dir="$source_dir/build"
    local roofit_build="$source_dir/RooFitExtensions/build"
    local configure_status
    local build_status

    printf '\nBuilding %s...\n' "$dependency"

    mkdir -p "$build_dir" \
        || fail "Could not create build directory for $dependency"

    cmake \
        -S "$source_dir" \
        -B "$build_dir" \
        -DRooFitExtensions_DIR="$roofit_build" \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON

    configure_status=$?

    if (( configure_status != 0 )); then
        fail \
            "$dependency configuration failed with exit code " \
            "$configure_status"
    fi

    cmake --build "$build_dir" --parallel "$install_jobs"
    build_status=$?

    if (( build_status != 0 )); then
        fail \
            "$dependency build failed with exit code $build_status"
    fi

    case "$dependency" in
        xmlAnaWSBuilder)
            verify_executable_file "$build_dir/bin/XMLReader"
            verify_nonempty_file \
                "$build_dir/lib/libxmlAnaWSBuilder.so"
            ;;
        quickFit)
            verify_executable_file "$build_dir/quickFit"
            verify_nonempty_file "$build_dir/libquick.so"
            ;;
        workspaceCombiner)
            verify_executable_file "$build_dir/manager"
            verify_nonempty_file \
                "$build_dir/libworkspaceCombiner.so"
            ;;
        *)
            fail "Unsupported C++ dependency: $dependency"
            ;;
    esac

    printf 'PASS %s\n' "$dependency"
}


run_build() {
    local dependency
    local install_jobs_value

    run_check
    setup_scientific_environment

    install_jobs_value="${INSTALL_JOBS:-4}"

    if [[ ! "$install_jobs_value" =~ ^[1-9][0-9]*$ ]]; then
        fail "INSTALL_JOBS must be a positive integer"
    fi

    install_jobs="$install_jobs_value"

    printf 'Parallel build jobs: %s\n' "$install_jobs"

    for dependency in \
        xmlAnaWSBuilder \
        quickFit \
        workspaceCombiner
    do
        build_roofit_extensions "$dependency"
        build_cpp_dependency "$dependency"
    done

    printf '\n%s\n' 'Validating pyBumpHunter environment...'

    if ! "$repo_root/scripts/install_pyBumpHunter.sh"; then
        fail \
            "pyBumpHunter environment installation or validation failed"
    fi

    printf '\n%s\n' \
        'Non-destructive dependency build completed successfully.'
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
    --build)
        run_build
        ;;
    --help|-h)
        usage
        ;;
    *)
        usage >&2
        fail "Unsupported installer mode: $1"
        ;;
esac
