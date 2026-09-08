import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from python.repo_utils import (
    build_repo_snapshot,
    find_repo_root,
    read_repo_snapshot,
    write_repo_snapshot,
)


def _strip_full_line_comments(text: str) -> str:
    """Drop every line whose stripped form starts with '#' (a shell or
    YAML full-line comment), so a commented-out reference to a test
    file can never satisfy a "this file is referenced" check below."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _join_continuations(text: str) -> list[str]:
    """One logical line per shell command, with backslash-continued
    lines joined, so an argument on its own physical line still counts
    as part of the command it belongs to."""
    joined: list[str] = []
    pending = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.endswith("\\"):
            pending += stripped[:-1].strip() + " "
            continue
        joined.append((pending + stripped).strip())
        pending = ""
    if pending:
        joined.append(pending.strip())
    return joined


# Command words that only *print* text. A command named in an echo is
# not a command the file runs, so these lines are dropped before any
# "this file runs that command" assertion.
_OUTPUT_ONLY_COMMANDS = re.compile(r'^(?:echo|printf|cat|:)\b|^"?\$?\w*echo')


def _executable_command_lines(text: str) -> str:
    """Only the lines of a shell script or workflow that actually run
    something: full-line comments dropped, backslash continuations
    joined, pure-output lines (echo/printf/cat) removed, and heredoc
    bodies removed - a heredoc body is data being printed, and its
    lines carry no command word of their own to filter on.

    Asserting a command is "present" by searching raw file text is
    unsound - a commented-out line, or the command quoted inside an
    echo, satisfies the search while the file no longer runs it. This
    has been found three times in this repository's own policy tests, so
    every "the file runs X" assertion below goes through here.
    """
    kept: list[str] = []
    heredoc_terminator: str | None = None
    for line in _join_continuations(_strip_full_line_comments(text)):
        if heredoc_terminator is not None:
            if line.strip() == heredoc_terminator:
                heredoc_terminator = None
            continue
        opener = re.search(r"<<-?\s*'?\"?([A-Za-z_][A-Za-z0-9_]*)'?\"?", line)
        if opener:
            heredoc_terminator = opener.group(1)
            continue
        if line and not _OUTPUT_ONLY_COMMANDS.search(line):
            kept.append(line)
    return "\n".join(kept)


_SHELL_FUNCTION_DEFINITION = re.compile(
    r"^\s*(?:function\s+)?[A-Za-z_][A-Za-z0-9_]*\s*\(\s*\)\s*\{?\s*$"
)


def _shell_invocation_lines(text: str) -> str:
    """Only the lines of a shell script that actually *call* something.

    `_executable_command_lines()` already drops comments and
    output-only lines, but a shell function's own definition line still
    carries its name. So "this script calls run_check" cannot be proved
    by searching even the executable lines for `run_check`: replacing
    every real call with `echo "run_check"` leaves the definition
    behind, and the search still succeeds. Confirmed by sabotage - it
    did, in the installer tests below. Definition lines are dropped too,
    so only real call sites remain.
    """
    return "\n".join(
        line
        for line in _executable_command_lines(text).splitlines()
        if not _SHELL_FUNCTION_DEFINITION.match(line)
    )


def _declared_submodule_paths(gitmodules_path: Path) -> set[str]:
    """Every submodule path a .gitmodules file really declares, read the
    way git itself reads that file.

    Searching the raw text for `path = <name>` also matches a
    commented-out declaration. Confirmed by sabotage: commenting one out
    and renaming the real one left the check below passing, and no other
    test in this suite reads .gitmodules at all, so nothing caught it.
    `git config --file` parses the real config syntax, where a comment
    is not a setting.
    """
    completed = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(gitmodules_path),
            "--get-regexp",
            r"^submodule\..*\.path$",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        line.split(maxsplit=1)[1]
        for line in completed.stdout.splitlines()
        if line.strip() and len(line.split(maxsplit=1)) == 2
    }


def _strip_inline_comment(line: str) -> str:
    """Drop a YAML/shell trailing `# ...` comment, respecting quotes."""
    out: list[str] = []
    quote: str | None = None
    for ch in line:
        if quote is not None:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


_YAML_NAME_KEY = re.compile(r"^\s*(?:-\s+)?name:")


def _yaml_config_lines(text: str) -> str:
    """A workflow's configuration only: no comments, no `name:` values.

    A YAML comment and a step's `name:` are both free text. A comment
    mentioning a pinned version, or a step named after the very setting
    a test is looking for, satisfies a raw-text search while the real
    configuration says something else - the same false-positive class as
    the command searches above. Neither is configuration, so neither is
    returned. Use this for "the workflow is configured with X"
    assertions, and `_workflow_run_block_lines()` for "the workflow runs
    X".
    """
    kept: list[str] = []
    for raw in _strip_full_line_comments(text).splitlines():
        line = _strip_inline_comment(raw)
        if line.strip() and not _YAML_NAME_KEY.match(line):
            kept.append(line)
    return "\n".join(kept)


def _workflow_run_block_lines(text: str) -> str:
    """Only the shell inside a GitHub Actions workflow's `run:` blocks.

    A workflow is YAML, so most of its lines are metadata, and a step's
    `name:` is free text that may quote the very command a test is
    looking for. Feeding whole-file YAML to a command search is
    therefore unsound in a way `_executable_command_lines()` alone
    cannot fix: `- name: python scripts/quality_check.py --mode full`
    carries no output-only command word, so it survives every filter
    and satisfies the search after the real `run:` command is deleted.
    Only `run:` contents are commands, so only they are returned.
    """
    kept: list[str] = []
    block_key_column: int | None = None
    for raw in text.splitlines():
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        if block_key_column is not None:
            if indent > block_key_column:
                kept.append(raw)
                continue
            block_key_column = None
        if re.match(r"\s*(?:-\s+)?run:", raw):
            inline = raw.split("run:", 1)[1].strip()
            if inline.strip("|>+-") == "":
                block_key_column = raw.index("run:")
            else:
                kept.append(inline)
    return "\n".join(kept)


def test_find_repo_root_returns_workspace_root() -> None:
    repo_root = find_repo_root()

    assert repo_root == Path(__file__).resolve().parents[1]
    assert (repo_root / "README.md").exists()
    assert (repo_root / "python").is_dir()


def test_repo_snapshot_matches_frozen_reference(tmp_path: Path) -> None:
    snapshot = build_repo_snapshot()
    reference_path = (
        Path(__file__).resolve().parents[1] / "tests" / "references" / "repo_snapshot.json"
    )

    write_repo_snapshot(tmp_path / "snapshot.json", snapshot)
    written_snapshot = read_repo_snapshot(tmp_path / "snapshot.json")

    expected_snapshot = read_repo_snapshot(reference_path)

    assert written_snapshot == expected_snapshot
    assert written_snapshot["python_dir_exists"] is True
    assert written_snapshot["tests_dir_exists"] is True
    assert written_snapshot["readme_exists"] is True
    assert written_snapshot["top_level_entries"] == json.loads(
        json.dumps(expected_snapshot["top_level_entries"])
    )


DEPENDENCY_REVISIONS = {
    "xmlAnaWSBuilder": "6b84050f3c0206a6f30eb40b103cc101e68505cc",
    "quickFit": "0408030b6c8d74a2e2c27a864a02756132d08f5a",
    "workspaceCombiner": "7d484ad3f89c4075d2c567aa4503fc56e1bb9468",
    "pyBumpHunter": "91f49a622bd77622edb02a1a2788fc12835e5b72",
}


@pytest.mark.requires_analysis_dependencies
def test_external_dependency_checkouts_match_pinned_revisions() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    for dependency, expected_revision in DEPENDENCY_REVISIONS.items():
        dependency_path = repo_root / dependency

        assert (
            dependency_path.is_dir()
        ), f"Required dependency directory is missing: {dependency_path}"

        completed = subprocess.run(
            ["git", "-C", str(dependency_path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, (
            f"{dependency} is not a readable Git checkout:\n" f"{completed.stderr}"
        )
        assert completed.stdout.strip() == expected_revision, (
            f"{dependency} revision mismatch: "
            f"expected {expected_revision}, "
            f"found {completed.stdout.strip()}"
        )


@pytest.mark.requires_analysis_dependencies
def test_external_dependency_checkouts_have_no_tracked_source_changes() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    for dependency in DEPENDENCY_REVISIONS:
        dependency_path = repo_root / dependency

        completed = subprocess.run(
            [
                "git",
                "-C",
                str(dependency_path),
                "status",
                "--short",
                "--untracked-files=no",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, (
            f"Could not inspect {dependency} checkout:\n" f"{completed.stderr}"
        )
        assert not completed.stdout.strip(), (
            f"{dependency} contains tracked source modifications:\n" f"{completed.stdout}"
        )


def test_generated_output_ignore_policy_is_narrow() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    generated_outputs = [
        "run/fits/J100/run_481_3000_sixPar/audit_generated.root",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.pdf",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.xml",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.log",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.root",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.pdf",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.xml",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.log",
    ]

    canonical_manifests = [
        "run/fits/J100/run_481_3000_sixPar/analysis_results.json",
        "run/fits/J50/run_344_2079_sixPar/analysis_results.json",
    ]

    for relative_path in generated_outputs:
        completed = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--no-index",
                relative_path,
            ],
            cwd=repo_root,
            check=False,
        )

        assert completed.returncode == 0, (
            f"Generated output is unexpectedly exposed to Git: " f"{relative_path}"
        )

    for relative_path in canonical_manifests:
        completed = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--no-index",
                relative_path,
            ],
            cwd=repo_root,
            check=False,
        )

        assert completed.returncode == 1, (
            f"Canonical analysis manifest is unexpectedly ignored: " f"{relative_path}"
        )


def test_no_untracked_generated_analysis_products() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--untracked-files=all",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )

    generated_suffixes = (".root", ".pdf", ".xml", ".log")
    unexpected = []

    for line in completed.stdout.splitlines():
        status = line[:2]
        relative_path = line[3:]

        if status == "??" and relative_path.endswith(generated_suffixes):
            unexpected.append(relative_path)

    assert not unexpected, "Unexpected untracked generated analysis products:\n" + "\n".join(
        f"  - {path}" for path in unexpected
    )


def test_ci_runs_locked_lightweight_full_gate() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workflow_path = repo_root / ".github" / "workflows" / "tier1-root-comparison.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    # Configuration keys are checked against configuration lines only -
    # comments and step names stripped - for the same reason the
    # commands below are checked against run: blocks only. A comment
    # naming a pinned version, or a step named after it, is not
    # configuration.
    config = _yaml_config_lines(workflow)
    assert "uses: actions/checkout@" in config
    assert "uses: actions/setup-python@" in config
    assert 'python-version: "3.12.13"' in config
    assert "requirements-dev-lock.txt" in config
    assert "tier-2-m365" in config

    # The two *commands* are checked against the contents of this
    # workflow's `run:` blocks only. Two separate false positives were
    # real here: commenting the gate command out left this test passing,
    # and so did deleting it while leaving its text in the step's
    # `name:`, because a YAML key is not an output-only command and
    # survives every shell-level filter. Same defect class as the
    # gate-coverage tests below.
    commands = _executable_command_lines(_workflow_run_block_lines(workflow))
    assert "python -m pip install -r requirements-dev-lock.txt" in commands
    assert "python scripts/quality_check.py --mode full" in commands

    # These stay against raw text deliberately. For a "must NOT appear"
    # check, raw text is the stricter side: it also rejects a
    # commented-out mention, which is the safe direction here.
    assert "tests/test_analysis_workflows_integration.py" not in workflow
    assert "requires_root" not in workflow
    assert "requires_analysis_dependencies" not in workflow


def test_precommit_is_not_a_locked_development_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    direct_dependencies = (repo_root / "requirements-dev.txt").read_text(encoding="utf-8")
    locked_dependencies = (repo_root / "requirements-dev-lock.txt").read_text(encoding="utf-8")

    assert "pre-commit==" not in direct_dependencies
    assert "pre-commit==" not in locked_dependencies


def test_git_hook_pre_commit_gate_matches_authoritative_commands() -> None:
    # .githooks/pre-commit is a plain git-native hook, not the
    # third-party `pre-commit` framework the test above confirms is
    # absent - it wires the two already-authoritative commands
    # (scripts/quality_check.py --mode full, and the same "integration
    # and requires_root" scientific gate every Tier 3 chunk runs before
    # committing) into a mandatory local check, per
    # doc/TIER2_SYSTEM.md's "Optional pre-commit configuration" section.
    repo_root = Path(__file__).resolve().parents[1]

    hook_path = repo_root / ".githooks" / "pre-commit"
    installer_path = repo_root / "scripts" / "install_git_hooks.sh"

    assert hook_path.is_file(), "Missing .githooks/pre-commit"
    assert hook_path.stat().st_mode & 0o111, "the pre-commit hook must be executable"
    assert installer_path.is_file(), "Missing scripts/install_git_hooks.sh"
    assert installer_path.stat().st_mode & 0o111, "the hook installer must be executable"

    hook_text = hook_path.read_text(encoding="utf-8")
    installer_text = installer_path.read_text(encoding="utf-8")

    # Checked against lines the hook actually runs, not its raw text.
    # Commenting the whole scientific gate out of this hook used to leave
    # this test passing - a false all-clear on the repository's mandatory
    # local gate. Same defect class as the two gate-coverage tests below.
    hook_commands = _executable_command_lines(hook_text)
    assert "scripts/quality_check.py --mode full" in hook_commands
    assert "setup_buildAndFit.sh" in hook_commands

    hook_pytest = _pytest_command_lines(hook_text)
    assert "tests/test_analysis_workflows_integration.py" in hook_pytest
    assert '"integration and requires_root"' in hook_pytest

    installer_commands = _executable_command_lines(installer_text)
    assert "core.hooksPath" in installer_commands
    assert ".githooks" in installer_commands


# The marker decorator, however it is validly written: bare, or called
# with empty parentheses. Matching one exact spelling would let a
# differently-written marker slip past the per-test map guard below,
# which is the same "the check looked thorough and missed a test"
# failure the map exists to prevent.
_DEPENDENCY_MARKER = re.compile(r"^@pytest\.mark\.requires_analysis_dependencies\s*(?:\(\s*\))?$")


def _tests_dir_files_marked_requires_analysis_dependencies(tests_dir: Path) -> list[str]:
    # Deliberately over-inclusive: a file merely *mentioning* the marker
    # is still required to appear in the gate lists. Erring that way
    # causes a false failure, never a false pass.
    return sorted(
        p.name
        for p in tests_dir.glob("test_*.py")
        if "requires_analysis_dependencies" in p.read_text(encoding="utf-8")
    )


def _dependency_marked_test_names(test_file: Path) -> list[str]:
    """Bare function names of every requires_analysis_dependencies-marked
    test in one file: scan for the marker line, skip over any other
    stacked `@pytest.mark....` decorator lines, and record the `def
    test_...` line that follows."""
    names: list[str] = []
    pending = False
    for line in test_file.read_text(encoding="utf-8").splitlines():
        stripped = _strip_inline_comment(line).strip()
        if _DEPENDENCY_MARKER.match(stripped):
            pending = True
            continue
        if not pending:
            continue
        if stripped.startswith("@pytest.mark."):
            continue
        if stripped.startswith("def "):
            names.append(stripped[len("def ") :].split("(")[0])
        pending = False
    return names


# Matches a real pytest invocation, anchored at the *command position*
# of a logical line: `python -m pytest`, `python3.9 -m pytest`,
# `/path/to/python -m pytest`, `"$python_bin" -m pytest`, a bare
# `pytest`/`.../bin/pytest`, and any of those behind this script's own
# `run_gate "<description>"` wrapper. Anchoring is the whole point: an
# unanchored search for `-m pytest` also matches
# `echo "python -m pytest tests/test_pre_fit.py"` and a workflow
# `- name:` mentioning the command, so deleting a real gate while
# leaving its text in an echo would still have satisfied the coverage
# assertions below - exactly the false positive this helper exists to
# prevent. test_pytest_command_lines_ignores_echoed_commands() below is
# the regression test for that.
_PYTEST_INVOCATION = re.compile(
    r'^(?:run_gate\s+"[^"]+"\s+)?'
    r'(?:(?:"?\$python_bin"?)|(?:\S*/)?python\d*(?:\.\d+)*)\s+-m\s+pytest(?:\s|$)'
    r"|^(?:\S*/)?pytest(?:\s|$)"
)


_PYTEST_NEGATION = re.compile(r"\bnot\b")


_PYTEST_TOKEN = re.compile(r"\bpytest\b")


def _pytest_option_value(line: str, option: str) -> str | None:
    """The value passed to `option` on one pytest command line, unquoted.

    Only the text after the `pytest` token is searched: `python -m
    pytest` carries an `-m` of its own for the module name, and reading
    that as the marker filter would make every marker check compare
    against the string "pytest".

    Returns None when the option is absent from that line.
    """
    token = _PYTEST_TOKEN.search(line)
    arguments = line[token.end() :] if token else line
    match = re.search(rf"{re.escape(option)}\s+(\"[^\"]*\"|'[^']*'|\S+)", arguments)
    if match is None:
        return None
    return match.group(1).strip("\"'")


def _selects_positively(value: str | None, expression: str) -> bool:
    """True when a `-k`/`-m` value selects `expression` rather than excluding it.

    Substring membership is not enough. `-k "not <test-name>"` and
    `-m "not <marker>"` both *contain* the expression while selecting the
    opposite tests, so a coverage check built on membership alone stays
    green after the real gate has been inverted. Confirmed by sabotage
    for both options: negating the runtime-readiness `-k` selector and
    the prepared-dependency `-m` filter each left the coverage tests
    passing.

    Any `not` in the value is treated as disqualifying. That is
    deliberately conservative: neither `scripts/run_all_gates.sh` nor
    `.github/workflows/scientific-analysis.yml` uses a mixed expression
    such as `-m "requires_analysis_dependencies and not slow"`, and if
    one ever legitimately needs to, this helper must be taught to parse
    the expression rather than silently accept the negation.
    """
    if value is None or expression not in value:
        return False
    return not _PYTEST_NEGATION.search(value)


def _marker_filter_keeps(value: str | None, marker: str) -> bool:
    """True when a `-m` value leaves `marker`-marked tests selected.

    No `-m` at all deselects nothing, so absence is acceptable here -
    unlike `_selects_positively()`, where the option is the only thing
    that picks the test out.
    """
    if value is None:
        return True
    return _selects_positively(value, marker)


def _pytest_command_lines(text: str) -> str:
    """Only the text of this file's actual pytest command lines.

    Full-line comments are dropped, backslash-continued lines are
    joined into single logical lines, and every logical line that does
    not itself invoke pytest is discarded. A test-file name or -k/-m
    selector that appears in an `echo`, a workflow `name:`, a variable
    assignment, a comment or any other non-pytest text therefore cannot
    satisfy the coverage assertions below - only one really passed to
    pytest can. Without this, removing a gate outright while leaving
    its name behind in an echo line would still pass these tests.
    """
    return "\n".join(
        line
        for line in _join_continuations(_strip_full_line_comments(text))
        if _PYTEST_INVOCATION.search(line)
    )


# tests/test_analysis_workflows_integration.py is exempt from the
# generic "tests/<file> appears in the gate invocation" check below:
# unlike every other requires_analysis_dependencies test file (selected
# as a whole file plus a blanket "-m requires_analysis_dependencies"
# marker filter, so the filename alone proves every marked test in it
# runs), this file's two marked tests are each selected by their own
# narrower, distinct pytest invocation (see doc/TIER1_SYSTEM.md's
# "Scientific runtime readiness" and "Executable characterization
# gate" entries) - the filename appears in both invocations' text
# regardless of whether either test is actually selected. Exempting the
# whole file without also checking each test individually would hide
# exactly this gap (confirmed: it did, until scripts/run_all_gates.sh's
# missing runtime-readiness invocation was found and fixed), so the two
# checks below assert each test's own dedicated selector by name
# instead of exempting the file outright.
_INTEGRATION_TEST_FILE = "test_analysis_workflows_integration.py"
# Each test, with the pytest option that selects it and the expression
# that option must positively carry. Checked with
# `_selects_positively()` rather than by substring membership: a bare
# search for the expression also matches `-k "not <name>"`, which runs
# the opposite tests. Confirmed by sabotage - negating the -k selector
# left the old check passing.
_INTEGRATION_TEST_SELECTORS = {
    # -k substring selector used by the dedicated runtime-readiness
    # invocation; also a substring of the test's own full name.
    "test_authoritative_setup_provides_scientific_runtime": (
        "-k",
        "authoritative_setup_provides_scientific_runtime",
    ),
    # this exact marker combination ("integration" and "requires_root"
    # together) is unique in the whole test suite to this one test -
    # confirmed by grepping every @pytest.mark.integration test.
    "test_authoritative_j100_j50_workflows_match_frozen_reference": (
        "-m",
        "integration and requires_root",
    ),
}


def _assert_covers_every_dependency_marked_test(
    raw_text: str, source_description: str, non_pytest_sentinel: str
) -> None:
    # Everything below is asserted against the real pytest command
    # lines only, never the whole file.
    command_text = _pytest_command_lines(raw_text)

    # Negative control on the extractor itself: `non_pytest_sentinel` is
    # a string this source really contains, but only outside any pytest
    # command. If it survives extraction, the extractor is letting
    # non-pytest text through and every assertion below is worthless -
    # so fail here rather than pass on a false positive later.
    assert command_text, f"No pytest invocation found in {source_description} at all"
    assert non_pytest_sentinel not in command_text, (
        f"{source_description}'s pytest-command extraction is too permissive: it kept "
        f"non-pytest text containing {non_pytest_sentinel!r}, so the coverage "
        "assertions below would no longer prove anything"
    )

    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root / "tests"

    integration_test_file = tests_dir / _INTEGRATION_TEST_FILE
    integration_marked_tests = set(_dependency_marked_test_names(integration_test_file))
    assert integration_marked_tests == set(_INTEGRATION_TEST_SELECTORS), (
        f"{_INTEGRATION_TEST_FILE}'s requires_analysis_dependencies tests changed "
        f"({sorted(integration_marked_tests)}) without updating this test's own "
        "per-test selector map"
    )
    command_lines = command_text.splitlines()
    missing_integration_selectors = [
        test_name
        for test_name, (option, expression) in _INTEGRATION_TEST_SELECTORS.items()
        if not any(
            _selects_positively(_pytest_option_value(line, option), expression)
            for line in command_lines
            if f"tests/{_INTEGRATION_TEST_FILE}" in line
        )
    ]
    assert not missing_integration_selectors, (
        f"{source_description} is missing a dedicated selector for these "
        f"{_INTEGRATION_TEST_FILE} tests: {missing_integration_selectors}"
    )

    # Naming the file is not enough: if the invocation's own marker
    # filter deselects `requires_analysis_dependencies`, every filename
    # is still present while none of the marked tests runs. Confirmed by
    # sabotage - inverting that filter left the old check passing. So a
    # file counts as covered only when some pytest line both names it
    # and carries a marker filter that keeps the marker (or none at
    # all, which deselects nothing).
    marked_files = _tests_dir_files_marked_requires_analysis_dependencies(tests_dir)
    missing_files = [
        name
        for name in marked_files
        if name != _INTEGRATION_TEST_FILE
        and not any(
            _marker_filter_keeps(_pytest_option_value(line, "-m"), "requires_analysis_dependencies")
            for line in command_lines
            if f"tests/{name}" in line
        )
    ]
    assert not missing_files, (
        f"{source_description} is missing these requires_analysis_dependencies "
        f"test files: {missing_files}"
    )


def test_executable_command_lines_ignores_comments_and_echoes() -> None:
    # Regression test for _executable_command_lines()'s contract. The
    # failure it pins down was real in two policy tests above: with the
    # pre-commit hook's whole scientific gate commented out, and with
    # the CI workflow's gate command commented out, both tests still
    # passed because they searched raw file text.
    inert = """
        # bash scripts/setup_buildAndFit.sh
        echo "running scripts/quality_check.py --mode full"
        printf '%s\\n' "core.hooksPath"
        cat <<'EOF'
        scripts/quality_check.py --mode full
        EOF
    """
    assert _executable_command_lines(inert) == ""

    real = """
        # this comment mentions quality_check.py --mode full
        echo "about to run the gate"
        python scripts/quality_check.py --mode full
        git config core.hooksPath .githooks
    """
    commands = _executable_command_lines(real)
    assert "python scripts/quality_check.py --mode full" in commands
    assert "core.hooksPath" in commands
    assert "about to run the gate" not in commands


def test_yaml_config_lines_excludes_comments_and_step_names() -> None:
    # Regression test for _yaml_config_lines(). Both inert positions it
    # removes were live false-positive paths for the configuration
    # assertions in test_ci_runs_locked_lightweight_full_gate above: a
    # comment or a step name quoting a pinned value satisfied a raw-text
    # search while the real configuration said something else.
    inert = """
    # python-version: "3.12.13"
      - name: pin python-version "3.12.13" and cover tier-2-m365
        uses: actions/nothing@v1   # tier-2-m365
    """
    config = _yaml_config_lines(inert)
    assert '"3.12.13"' not in config
    assert "tier-2-m365" not in config
    # the real key on that line still survives
    assert "uses: actions/nothing@v1" in config

    real = """
    on:
      push:
        branches:
          - tier-2-m365
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12.13"
    """
    config = _yaml_config_lines(real)
    assert "tier-2-m365" in config
    assert 'python-version: "3.12.13"' in config


def test_dependency_marker_is_recognised_however_it_is_written() -> None:
    # The per-test selector map guard is only as good as this detector:
    # a marker it fails to recognise means a marked test can exist with
    # no gate selecting it and no test objecting.
    assert _DEPENDENCY_MARKER.match("@pytest.mark.requires_analysis_dependencies")
    assert _DEPENDENCY_MARKER.match("@pytest.mark.requires_analysis_dependencies()")
    assert _DEPENDENCY_MARKER.match("@pytest.mark.requires_analysis_dependencies( )")
    # ...but a mention that is not the decorator must not count
    assert not _DEPENDENCY_MARKER.match("# @pytest.mark.requires_analysis_dependencies")
    assert not _DEPENDENCY_MARKER.match('pytestmark = "requires_analysis_dependencies"')
    assert not _DEPENDENCY_MARKER.match("@pytest.mark.requires_analysis_dependencies_extra")


def test_workflow_run_block_lines_excludes_yaml_metadata() -> None:
    # Regression test for _workflow_run_block_lines(). The failure it
    # pins down was real: a step whose `name:` quoted the gate command
    # satisfied test_ci_runs_locked_lightweight_full_gate above even
    # after the real `run:` command was deleted, because a YAML key
    # carries no output-only command word for a shell-level filter to
    # catch.
    metadata_only = """
      - name: python scripts/quality_check.py --mode full
        uses: actions/setup-python@v6
        with:
          python-version: "3.12.13"
        env:
          CC: gcc-11
    """
    assert _workflow_run_block_lines(metadata_only) == ""

    # ...while a real block scalar's contents survive, and an inline
    # `run:` command does too.
    with_blocks = """
      - name: Run the gate
        shell: bash
        run: |
          set -euo pipefail
          python scripts/quality_check.py --mode full
      - name: One-liner
        run: git config core.hooksPath .githooks
      - name: After the block
        uses: actions/checkout@v6
    """
    commands = _workflow_run_block_lines(with_blocks)
    assert "python scripts/quality_check.py --mode full" in commands
    assert "git config core.hooksPath .githooks" in commands
    assert "actions/checkout" not in commands
    assert "Run the gate" not in commands


def test_pytest_command_lines_ignores_echoed_commands() -> None:
    # Direct regression test for _pytest_command_lines()'s own contract,
    # so the two coverage tests below cannot quietly become vacuous. The
    # failure this pins down is specific: if a gate's real pytest
    # invocation is deleted but its command text survives in an echo,
    # a workflow step name or a comment, the coverage checks must stop
    # seeing that gate as covered.
    sabotaged = """
        echo "python -m pytest tests/test_pre_fit.py -k some_selector -v"
        echo '[run-all-gates] skipping python -m pytest tests/test_repo_utils.py'
        # python -m pytest tests/test_create_binning.py -v
        step_name="run python -m pytest tests/test_find_bh_window.py"
        printf '%s\\n' "python -m pytest tests/test_plot_post_fit.py"
    """
    assert _pytest_command_lines(sabotaged) == ""

    # ...while every real invocation shape actually used by
    # scripts/run_all_gates.sh and the CI workflow is still recognised,
    # including backslash-continued argument lists.
    genuine = """
        run_gate "prepared-dependency gate" "$python_bin" -m pytest tests/test_repo_utils.py \\
          -m "requires_analysis_dependencies" -v
        python -m pytest tests/test_analysis_workflows_integration.py \\
          -k authoritative_setup_provides_scientific_runtime -v
        python3 -m pytest tests/test_pre_fit.py -v
        /usr/bin/python3.9 -m pytest tests/test_create_binning.py -v
        pytest tests/test_find_bh_window.py -v
    """
    recognised = _pytest_command_lines(genuine).splitlines()
    assert len(recognised) == 5, recognised
    # continuation joining really happened, so a selector on the second
    # physical line still counts as part of the same command
    assert any('-m "requires_analysis_dependencies" -v' in line for line in recognised)
    assert any("-k authoritative_setup_provides_scientific_runtime" in line for line in recognised)


def test_shell_invocation_lines_ignores_function_definitions_and_echoes() -> None:
    """A function's own definition line is not a call to it.

    Pins the sabotage that found this: replacing `install.sh`'s two real
    `run_check` calls with `echo "would run run_check here"` left
    `test_install_script_is_non_destructive` passing, because the
    surviving `run_check() {` definition line still carried the name.
    """
    script = """#!/usr/bin/env bash
# run_check is mentioned in this comment only
run_check() {
    real_work
}
function verify_thing() {
    more_work
}
echo "would run run_check here"
printf '%s\\n' "verify_thing"
verify_thing
"""

    invocations = _shell_invocation_lines(script)

    # `verify_thing` is really called, so it survives; `run_check` is
    # only defined, commented and echoed, so it does not.
    assert "verify_thing" in invocations
    assert "run_check" not in invocations

    # The definition filter must not swallow real command lines.
    assert "real_work" in invocations
    assert "more_work" in invocations


def test_declared_submodule_paths_ignores_commented_out_declarations(tmp_path: Path) -> None:
    """A commented-out `path =` is not a declaration.

    Pins the sabotage that found this: commenting out .gitmodules'
    `path = quickFit` and renaming the real entry left
    `test_gitmodules_declares_expected_analysis_dependencies` passing,
    and nothing else in this suite reads .gitmodules.
    """
    gitmodules = tmp_path / ".gitmodules"
    gitmodules.write_text(
        '[submodule "kept"]\n'
        "\tpath = kept\n"
        '[submodule "quickFit"]\n'
        "\t# path = quickFit\n"
        "\tpath = quickFit-RENAMED\n"
        '[submodule "semicolon"]\n'
        "\t; path = semicolon\n",
        encoding="utf-8",
    )

    declared = _declared_submodule_paths(gitmodules)

    assert declared == {"kept", "quickFit-RENAMED"}
    assert "quickFit" not in declared
    assert "semicolon" not in declared


def test_pytest_selectors_are_read_positively_and_reject_negation() -> None:
    """A selector that names a test is not a selector that runs it.

    Pins the three sabotages that found this: inverting the
    runtime-readiness `-k`, the scientific `-m`, or the
    prepared-dependency `-m` each left the two gate-coverage tests
    passing, because they searched for the expression as a substring and
    `not <expression>` contains it.
    """
    marker = 'python -m pytest tests/test_x.py -m "requires_analysis_dependencies" -v'
    marker_negated = 'python -m pytest tests/test_x.py -m "not requires_analysis_dependencies" -v'
    selector = (
        "python -m pytest tests/test_x.py -k authoritative_setup_provides_scientific_runtime -v"
    )
    selector_negated = (
        "python -m pytest tests/test_x.py"
        ' -k "not authoritative_setup_provides_scientific_runtime" -v'
    )
    unfiltered = "python -m pytest tests/test_x.py -v"

    # `python -m pytest`'s own -m names the module, not a marker filter.
    assert _pytest_option_value(marker, "-m") == "requires_analysis_dependencies"
    assert _pytest_option_value(unfiltered, "-m") is None
    assert _pytest_option_value(selector, "-k") == "authoritative_setup_provides_scientific_runtime"

    assert _selects_positively(_pytest_option_value(marker, "-m"), "requires_analysis_dependencies")
    assert not _selects_positively(
        _pytest_option_value(marker_negated, "-m"), "requires_analysis_dependencies"
    )
    assert _selects_positively(
        _pytest_option_value(selector, "-k"), "authoritative_setup_provides_scientific_runtime"
    )
    assert not _selects_positively(
        _pytest_option_value(selector_negated, "-k"),
        "authoritative_setup_provides_scientific_runtime",
    )

    # The parenthesised negation of a compound marker expression.
    assert _selects_positively("integration and requires_root", "integration and requires_root")
    assert not _selects_positively(
        "not (integration and requires_root)", "integration and requires_root"
    )

    # No -m deselects nothing, so the marker survives; an inverted or
    # unrelated filter does not.
    assert _marker_filter_keeps(None, "requires_analysis_dependencies")
    assert _marker_filter_keeps("requires_analysis_dependencies", "requires_analysis_dependencies")
    assert not _marker_filter_keeps(
        "not requires_analysis_dependencies", "requires_analysis_dependencies"
    )
    assert not _marker_filter_keeps("requires_root", "requires_analysis_dependencies")


def test_run_all_gates_script_covers_every_requires_analysis_dependencies_test_file() -> None:
    # scripts/run_all_gates.sh exists specifically to run every gate in
    # one command, including every test the lightweight gate deselects.
    # A test file carrying a requires_analysis_dependencies test but
    # missing from this script's own real-ROOT/prepared-dependency gate
    # invocations would silently never run there - the same class of
    # gap already found and fixed four times now (three times in
    # .github/workflows/scientific-analysis.yml, most recently
    # tests/test_pre_fit.py; once in this very script, which never ran
    # test_authoritative_setup_provides_scientific_runtime at all).
    # This test catches a repeat before it reaches CI, rather than
    # relying on a human noticing again.
    repo_root = Path(__file__).resolve().parents[1]

    script_path = repo_root / "scripts" / "run_all_gates.sh"
    assert script_path.is_file(), "Missing scripts/run_all_gates.sh"
    assert script_path.stat().st_mode & 0o111, "run_all_gates.sh must be executable"

    _assert_covers_every_dependency_marked_test(
        script_path.read_text(encoding="utf-8"),
        "scripts/run_all_gates.sh",
        # appears only in this script's own echo/log lines, never in a
        # pytest command - the negative control for the extractor
        non_pytest_sentinel="[run-all-gates]",
    )


def test_ci_scientific_workflow_covers_every_requires_analysis_dependencies_test_file() -> None:
    # Same check as the one above, against the actual CI workflow file -
    # this is the one that matters for real CI coverage; the script
    # above is a local convenience wrapper for the same set of gates.
    repo_root = Path(__file__).resolve().parents[1]

    workflow_path = repo_root / ".github" / "workflows" / "scientific-analysis.yml"
    assert workflow_path.is_file(), "Missing .github/workflows/scientific-analysis.yml"

    _assert_covers_every_dependency_marked_test(
        _workflow_run_block_lines(workflow_path.read_text(encoding="utf-8")),
        ".github/workflows/scientific-analysis.yml",
        # A real command inside a run: block that is not a pytest
        # invocation - the negative control for the extractor. It has to
        # live inside a run: block, because everything outside one is now
        # discarded before the check and a sentinel from the YAML
        # metadata would be trivially absent.
        non_pytest_sentinel="set -o pipefail",
    )


def test_authoritative_analysis_launchers_are_executable() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    launchers = (
        repo_root / "scripts" / "run_anaFit_J100.sh",
        repo_root / "scripts" / "run_anaFit_J50.sh",
    )

    for launcher in launchers:
        assert launcher.is_file(), f"Missing authoritative launcher: {launcher}"
        assert (
            launcher.stat().st_mode & 0o111
        ), f"Authoritative launcher is not executable: {launcher}"


def test_gitmodules_declares_expected_analysis_dependencies() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    # Read as git config, not as text: a commented-out `path =` line
    # satisfied the old raw-text search (see
    # `_declared_submodule_paths()`), and this is the only test in the
    # suite that reads .gitmodules at all.
    declared = _declared_submodule_paths(repo_root / ".gitmodules")
    missing = [name for name in DEPENDENCY_REVISIONS if name not in declared]
    assert not missing, (
        f".gitmodules does not declare a submodule path for {missing} "
        f"(it declares {sorted(declared)})"
    )


def test_declared_submodules_have_gitlink_entries() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--stage",
            *DEPENDENCY_REVISIONS,
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )

    gitlinks = {}

    for line in completed.stdout.splitlines():
        mode, _, _, path = line.split(maxsplit=3)
        gitlinks[path] = mode

    assert gitlinks == {dependency: "160000" for dependency in DEPENDENCY_REVISIONS}


def test_pybumphunter_installer_is_non_destructive_and_reproducible() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = repo_root / "scripts" / "install_pyBumpHunter.sh"

    assert installer.is_file()
    assert installer.stat().st_mode & 0o111

    installer_text = installer.read_text(encoding="utf-8")
    active_lines = [
        line.strip()
        for line in installer_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    active_script = "\n".join(active_lines)

    assert "rm -rf" not in active_script
    assert "git pull" not in active_script
    assert "git clone" not in active_script
    assert "setup.py install" not in active_script
    assert "pip install --upgrade" not in active_script
    assert "virtualenv " not in active_script
    assert "LCG_105" not in active_script

    assert 'scientific_setup="$repo_root/scripts/setup_buildAndFit.sh"' in active_script
    assert "--system-site-packages" in active_script
    assert "--no-deps" in active_script
    assert "--no-build-isolation" in active_script
    assert '"$pybh_source"' in active_script

    assert 'if [[ -e "$pybh_environment" ]]; then' in active_script
    assert "existing_python_version" in active_script
    assert "platform.python_version()" in active_script
    assert "Existing pyBH_env uses Python" in active_script
    assert "expected" in active_script
    assert "Existing pyBH_env failed import validation" in active_script
    assert "Existing pyBumpHunter environment is valid" in active_script

    required_imports = {
        "import matplotlib",
        "import numpy",
        "import pyBumpHunter",
        "import scipy",
        "import uproot",
    }

    for required_import in required_imports:
        assert required_import in active_script

    assert '"$environment_python" "$find_bh_window" --help' in active_script


def test_install_script_is_non_destructive() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = repo_root / "install.sh"

    assert installer.is_file()
    assert installer.stat().st_mode & 0o111

    installer_text = installer.read_text(encoding="utf-8")
    active_lines = [
        line.strip()
        for line in installer_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    active_script = "\n".join(active_lines)

    assert "rm -rf" not in active_script
    assert "git clone" not in active_script
    assert "git pull" not in active_script
    assert "git checkout" not in active_script
    assert "setup.py install" not in active_script
    assert "pip install --upgrade" not in active_script

    # Call sites, not mentions: each of these is a shell function this
    # installer must really invoke, and its own definition line carries
    # its name, so searching `active_script` proved nothing. Replacing
    # every real `run_check` call with an echo left this test passing
    # until this was changed.
    invocations = _shell_invocation_lines(installer_text)

    assert "--check" in active_script
    assert "run_check" in invocations
    assert "verify_parent_gitlink" in invocations
    assert "verify_no_tracked_changes" in invocations
    assert "verify_roofit_extensions" in invocations
    assert 'mode" != "160000"' in active_script
    assert "ba94bfcbfa4f4a4e3541ade09580399e409e8514" in active_script
    assert "Installation contract check passed." in active_script
    assert "No files were modified." in active_script

    assert "--build" in active_script
    assert "run_build() {" in active_script
    assert "build_roofit_extensions() {" in active_script
    assert "build_cpp_dependency() {" in active_script
    assert "setup_scientific_environment() {" in active_script

    assert "run_check" in invocations
    assert "setup_scientific_environment" in invocations
    assert 'install_jobs_value="${INSTALL_JOBS:-4}"' in active_script
    assert "INSTALL_JOBS must be a positive integer" in active_script

    assert 'mkdir -p "$build_dir"' in active_script
    assert "cmake --build" in active_script
    assert "--parallel" in active_script

    assert "cmake --install" not in installer_text
    assert "CMAKE_INSTALL_PREFIX=/usr/local" not in installer_text

    assert "libRooFitExtensions.so" in active_script
    assert "libRooFitExtensions_rdict.pcm" in active_script
    assert "libRooFitExtensions.rootmap" in active_script
    assert "RooFitExtensionsConfig.cmake" in active_script

    assert "bin/XMLReader" in active_script
    assert "libxmlAnaWSBuilder.so" in active_script
    assert 'verify_executable_file "$build_dir/quickFit"' in active_script
    assert "libquick.so" in active_script
    assert 'verify_executable_file "$build_dir/manager"' in active_script
    assert "libworkspaceCombiner.so" in active_script

    assert "scripts/install_pyBumpHunter.sh" in active_script
    assert "Non-destructive dependency build completed successfully." in active_script

    command_dispatch = invocations.split('case "$1" in', maxsplit=1)[1]
    assert "--build)" in command_dispatch
    assert "run_build" in command_dispatch


_LIVING_DOCUMENTS = (
    "README.md",
    "doc/TIER1_SYSTEM.md",
    "doc/TIER1_ENVIRONMENT_PROVENANCE.md",
    "doc/TIER2_SYSTEM.md",
    "doc/TIER3_SYSTEM.md",
    "doc/TIER3_EXECUTION_TRACE.md",
)

_GATE_MARKERS = (
    ("scientific", '-m "integration and requires_root"'),
    ("runtime readiness", "-k authoritative_setup_provides_scientific_runtime"),
    (
        "plotting-layer",
        "tests/test_plot_post_fit.py tests/test_plot_postfit_macro.py",
    ),
    ("lightweight", "quality_check.py --mode full"),
    (
        "prepared dependency",
        'tests/test_repo_utils.py -m "requires_analysis_dependencies"',
    ),
)

_FIGURE_PATTERNS = (
    ("collected", re.compile(r"(\d+) collected\b")),
    ("passed", re.compile(r"(\d+) passed\b")),
    ("selected", re.compile(r"(\d+) selected\b")),
    ("deselected", re.compile(r"(\d+)(?:\s+[a-z-]+){0,3}\s+deselected\b")),
    ("expected failures", re.compile(r"(\d+) expected failures\b")),
    ("files unchanged", re.compile(r"(\d+) files (?:would be left )?unchanged")),
    ("seconds", re.compile(r"(\d+(?:\.\d+)?)\s?(?:seconds\b|s\b)")),
)

_LATEST_CLAIM = re.compile(r"Latest\b")
_CLAIM_END = re.compile(r"exit code \d+")
_CLAIM_BOUNDARY = re.compile(r"Latest\b|#{2,} ")

_GATE_NAMED_IN_CLAIM = (
    # Checked in order. The plotting-layer gate is documented twice,
    # once under its marker filter and once without it, and the two runs
    # legitimately report different counts and different times - so they
    # are two gates here, not one gate with two contradictory figures.
    ("plotting-layer unfiltered", re.compile(r"no `?-m`? filter|unfiltered")),
    ("runtime readiness", re.compile(r"runtime[- ]readiness")),
    ("prepared dependency", re.compile(r"prepared[- ]dependency|dependency gate")),
    ("lightweight", re.compile(r"lightweight")),
    ("scientific", re.compile(r"scientific")),
)


def _documented_latest_figures(text: str) -> dict[str, dict[str, set[str]]]:
    """Every figure a document claims is the *latest* gate result.

    Returned as `{gate: {figure kind: values}}`, where a figure kind is
    one of collected/passed/selected/deselected/expected failures/
    seconds.

    Only figures inside a "Latest ..." claim are returned, and that
    restriction is the point. These documents also record what specific
    past runs measured - `doc/TIER3_EXECUTION_TRACE.md`'s
    "Verification performed" bullets, for instance, record a gate at
    289.19s and a 172-test suite, both true when that fix was made.
    Those must not be rewritten to match today, exactly as
    `doc/ACTIVITY_LOG.md` must not. A figure introduced by the word
    "Latest" is making a different, stronger claim - that it is the
    current result - and every document making that claim about the
    same gate has to agree.

    A claim runs from "Latest" to the next "Latest" or the next
    heading, which is how these documents are laid out: a gate command,
    then the result of running it, then the next section. It is cut
    short at the "exit code N" every one of these claims ends with, so
    that prose *explaining* a figure - which may quote a superseded
    count to say why it was wrong - cannot be read back as part of the
    claim itself. Backslash continuations are removed and whitespace
    collapsed first, since every one of these commands is wrapped
    across lines and each document wraps at a different column.
    """
    flat = " ".join(text.replace("\\\n", " ").split())
    marker_positions = sorted(
        (match.start(), name)
        for name, marker in _GATE_MARKERS
        for match in re.finditer(re.escape(marker), flat)
    )

    figures: dict[str, dict[str, set[str]]] = {}
    for claim in _LATEST_CLAIM.finditer(flat):
        following = _CLAIM_BOUNDARY.search(flat, claim.end())
        block = flat[claim.start() : following.start() if following else len(flat)]
        ends = _CLAIM_END.search(block)
        if ends:
            block = block[: ends.end()]

        # A claim that names its own gate ("Latest lightweight gate:")
        # is attributed by that name, since several documents state the
        # summary figures near the top and print the command itself much
        # further down. Only the claim's header - up to its first colon -
        # is searched, because the prose after it may mention another
        # gate in passing. A generic "Latest verified result:" falls
        # back to the last gate command printed above it.
        header, _, _ = block.partition(":")
        gate = "unattributed"
        for name, pattern in _GATE_NAMED_IN_CLAIM:
            if pattern.search(header):
                gate = name
                break
        else:
            above = [name for start, name in marker_positions if start < claim.start()]
            if above:
                gate = above[-1]

        for kind, pattern in _FIGURE_PATTERNS:
            for value in pattern.findall(block):
                figures.setdefault(gate, {}).setdefault(kind, set()).add(value)
    return figures


def test_documented_gate_figures_agree_across_every_living_document() -> None:
    repo_root = find_repo_root()

    claimed: dict[str, dict[str, dict[str, set[str]]]] = {}
    for relative_path in _LIVING_DOCUMENTS:
        document = repo_root / relative_path
        assert document.is_file(), f"{relative_path} is missing"
        text = document.read_text(encoding="utf-8")
        for gate, by_kind in _documented_latest_figures(text).items():
            for kind, values in by_kind.items():
                claimed.setdefault(gate, {}).setdefault(kind, {})[relative_path] = values

    assert "unattributed" not in claimed, (
        "a document claims a latest result above every gate command this "
        f"test knows: {sorted(claimed.get('unattributed', {}))} - add that "
        "gate's command to _GATE_MARKERS so its figures are checked "
        "rather than silently ignored"
    )

    for gate in ("lightweight", "scientific"):
        assert gate in claimed, (
            f"no latest {gate} gate result was found in any living "
            "document, so this test would check almost nothing - the "
            "phrasing it matches has probably changed"
        )

    agreed: dict[str, dict[str, str]] = {}
    for gate, by_kind in sorted(claimed.items()):
        for kind, per_document in sorted(by_kind.items()):
            distinct = set().union(*per_document.values())
            assert len(distinct) == 1, (
                f"the {gate} gate's latest {kind} figure is recorded as "
                f"{sorted(distinct)} in different documents: "
                f"{ {path: sorted(v) for path, v in per_document.items()} }"
                " - at least one of them is stale"
            )
            agreed.setdefault(gate, {})[kind] = distinct.pop()

    # A gate that records all three counts has to have them add up.
    # This catches a stale figure from one document alone, with no
    # second copy to compare against and nothing re-run: the
    # plotting-layer gate was once recorded as 48 collected with 18
    # selected and 29 deselected, which is 47, because a test file had
    # gained a test and only the total was refreshed.
    for gate, figures in sorted(agreed.items()):
        if not {"collected", "passed", "deselected"} <= figures.keys():
            continue
        collected = int(figures["collected"])
        passed = int(figures["passed"])
        deselected = int(figures["deselected"])
        assert passed + deselected == collected, (
            f"the {gate} gate's latest figures cannot describe any real "
            f"run: {passed} passed + {deselected} deselected is "
            f"{passed + deselected}, but {collected} were collected"
        )


def test_documented_latest_figures_are_attributed_to_the_right_gate() -> None:
    document = """
## Gate commands

### Lightweight full gate

```bash
python scripts/quality_check.py --mode full
```

Latest verified result:

- 227 collected;
- 207 passed;
- 20 prepared-dependency tests deselected;
- 0 expected failures;
- exit code 0.

### Scientific gate

```bash
python -m pytest tests/test_analysis_workflows_integration.py \\
  -m "integration and requires_root" -v
```

Latest verified result: 1 passed, 2 deselected, 74.68 seconds, exit
code 0 - down from the 289.19 seconds an earlier run of the same 3
tests took.

## Verification performed

- Reran the scientific gate: 1 passed, 2 deselected, 289.19s, exit
  code 0.
- Reran the lightweight gate: 172 passed, 8 deselected, exit code 0.
"""

    assert _documented_latest_figures(document) == {
        "lightweight": {
            "collected": {"227"},
            "passed": {"207"},
            "deselected": {"20"},
            "expected failures": {"0"},
        },
        "scientific": {
            "passed": {"1"},
            "deselected": {"2"},
            "seconds": {"74.68"},
        },
    }
    # The 289.19 seconds and the "3 tests" in the prose after "exit
    # code 0" are explanation, not part of the claim, and the whole
    # "Verification performed" section records a past run rather than
    # the latest one. Neither may leak into the figures above.


_COLLECTION_SUMMARY = re.compile(
    r"^(?:(?P<selected>\d+)/(?P<collected>\d+) tests collected"
    r" \((?P<deselected>\d+) deselected\)"
    r"|(?P<only>\d+) tests collected)"
)


def _quality_check_test_targets(repo_root: Path) -> list[str]:
    """The test files `scripts/quality_check.py` actually runs."""
    source = (repo_root / "scripts" / "quality_check.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "test_targets" for target in node.targets
        ):
            continue
        return [
            element.value
            for element in node.value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
    raise AssertionError("scripts/quality_check.py no longer assigns test_targets")


def _collect(repo_root: Path, arguments: list[str]) -> dict[str, int]:
    """Real collected/selected/deselected counts for a pytest selection."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
            *arguments,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        completed.returncode == 0
    ), f"collection failed for {arguments}:\n{completed.stdout}\n{completed.stderr}"

    for line in reversed(completed.stdout.splitlines()):
        summary = _COLLECTION_SUMMARY.match(line.strip())
        if summary:
            if summary.group("only"):
                total = int(summary.group("only"))
                return {"collected": total, "selected": total, "deselected": 0}
            return {
                "collected": int(summary.group("collected")),
                "selected": int(summary.group("selected")),
                "deselected": int(summary.group("deselected")),
            }
    raise AssertionError(
        "no recognisable collection summary in pytest's output - the format "
        f"has probably changed:\n{completed.stdout}"
    )


def test_documented_gate_counts_match_a_real_collection() -> None:
    """The two gates that need no ROOT are counted, not just cross-checked.

    `test_documented_gate_figures_agree_across_every_living_document`
    compares the documents against each other, so it cannot catch a
    figure that is stale in every copy at once - and for the
    prepared-dependency gate there is only one copy, so it catches
    nothing there at all. That is not hypothetical: its deselected count
    sat at 19 after two tests were added to `tests/test_repo_utils.py`,
    and no check noticed. Collection is deterministic and needs no ROOT,
    so for these two gates the documented counts can simply be measured.

    Timings are deliberately not verified. The same gate has measured
    74.68s, 131.40s and 134.41s on this shared node for identical work,
    so a documented timing is an observation, not a property.
    """
    repo_root = find_repo_root()

    documented: dict[str, dict[str, str]] = {}
    for relative_path in _LIVING_DOCUMENTS:
        text = (repo_root / relative_path).read_text(encoding="utf-8")
        for gate, by_kind in _documented_latest_figures(text).items():
            for kind, values in by_kind.items():
                documented.setdefault(gate, {}).update({kind: sorted(values)[0]})

    measurable = {
        "lightweight": [
            "-m",
            "not requires_analysis_dependencies",
            *_quality_check_test_targets(repo_root),
        ],
        "prepared dependency": [
            "-m",
            "requires_analysis_dependencies",
            "tests/test_repo_utils.py",
        ],
    }

    for gate, arguments in measurable.items():
        assert gate in documented, f"no documented {gate} gate result to check"
        real = _collect(repo_root, arguments)
        claimed = documented[gate]

        for documented_kind, real_kind in (
            ("collected", "collected"),
            ("passed", "selected"),
            ("deselected", "deselected"),
        ):
            if documented_kind not in claimed:
                continue
            assert int(claimed[documented_kind]) == real[real_kind], (
                f"the documented {gate} gate figure "
                f"'{claimed[documented_kind]} {documented_kind}' does not "
                f"match a real collection, which reports "
                f"{real[real_kind]} {real_kind} "
                f"(collected {real['collected']}, selected "
                f"{real['selected']}, deselected {real['deselected']})"
            )
