# `from __future__ import annotations` is required, not cosmetic: this
# file is collected by the scientific gates under the LCG runtime's
# Python 3.9.12, where a `str | None` in a function signature is
# evaluated at definition time and raises TypeError. Without it,
# collection fails before any test runs - which is exactly how CI
# broke. See tests/test_python39_compatibility... (the policy test
# below) for the check that keeps this from recurring.
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import warnings
from collections.abc import Callable
from pathlib import Path

import pytest

from python.repo_utils import (
    build_repo_snapshot,
    effective_pytest_config_file,
    find_repo_root,
    read_repo_snapshot,
    selection_affecting_addopts,
    write_repo_snapshot,
)


def _strip_full_line_comments(text: str) -> str:
    """Drop every line whose stripped form starts with '#' (a shell or
    YAML full-line comment), so a commented-out reference to a test
    file can never satisfy a "this file is referenced" check below."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _uncommented_lines(text: str) -> str:
    """Every line with its comments removed, whole-line and trailing.

    Order matters, and this must run *before* continuations are joined.
    A trailing comment is inert text on a live command line: a
    `-m "not ..."` gate carrying `# -k <the expected selector>` after it
    satisfied a coverage check while selecting nothing. But stripping
    after the join is wrong in the other direction - a comment whose
    text happens to end in `\\` would swallow the next line, and with
    it a real command. Confirmed both ways: `setup_thing  # see docs \\`
    followed by the genuine gate command lost the gate entirely, and
    the pytest extractor returned nothing at all.

    A `\\` inside a comment is not a line continuation, so the comment
    goes first.
    """
    return "\n".join(
        _strip_inline_comment(line) for line in _strip_full_line_comments(text).splitlines()
    )


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
    return "\n".join(
        line
        for line in _outside_heredoc_bodies(_join_continuations(_uncommented_lines(text)))
        if line and not _OUTPUT_ONLY_COMMANDS.search(line)
    )


_HEREDOC_OPENER = re.compile(r"<<-?\s*'?\"?([A-Za-z_][A-Za-z0-9_]*)'?\"?")


def _outside_heredoc_bodies(lines: list[str]) -> list[str]:
    """The logical lines that are not the body of a heredoc.

    A heredoc body is data, not commands: `cat <<EOF` followed by a
    gate's own pytest command prints that command and runs nothing.
    Every spelling behaves the same way and each was measured -
    `<<EOF`, `<<'EOF'`, `<<"EOF"`, `<<-EOF`, a heredoc redirected into
    a file, and one inside a workflow `run:` block.

    This started as part of `_executable_command_lines()` alone, which
    left `_pytest_command_lines()` without it: all six spellings hid a
    gate command from the coverage checks while the installer checks
    caught them. That is the same drift that put the two filter checks
    a review round apart, so it is one rule with two callers now.
    """
    kept: list[str] = []
    terminator: str | None = None
    for line in lines:
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            continue
        opener = _HEREDOC_OPENER.search(line)
        if opener:
            terminator = opener.group(1)
            continue
        kept.append(line)
    return kept


# A shell function definition in every form bash accepts: the POSIX
# `name()` form and the `function name` keyword form, with or without
# parentheses, with the body's opening `{` or `(` on the same line or
# the next one. Function names are constrained only by shell
# metacharacters, so `deploy-gate() {` is a definition too. Each form
# admitted here was first confirmed to be valid bash whose body runs
# nothing; the earlier version of this pattern recognised only one of
# them, which left three ways to hide a gate command in plain sight.
_SHELL_FUNCTION_DEFINITION = re.compile(
    r"^\s*(?:function\s+[^\s(){};&|<>]+(?:\s*\(\s*\))?"
    r"|[^\s(){};&|<>]+\s*\(\s*\))\s*(?P<opener>[{(])?"
)
_FUNCTION_BODY_CLOSERS = {"{": "}", "(": ")"}
_QUOTED_SPAN = re.compile(r"'[^']*'|\"[^\"]*\"")


def _body_depth_change(line: str, opener: str) -> int:
    """How much one line opens or closes a shell function body.

    Quoted text is removed first, and braces are then counted only
    where the shell itself would treat them as the body's delimiters:
    as whole words. Both matter, because a brace that is not a
    delimiter must not look like one - `echo "}}"`, `echo }}` and
    `${HOME}` all leave the depth alone, where a plain character count
    would end the body early and expose every line after it as
    top-level text. Parenthesis bodies are counted by character, which
    is how the shell nests them, and `$(...)` is balanced.
    """
    visible = _QUOTED_SPAN.sub("", line)
    if opener == "(":
        return visible.count("(") - visible.count(")")
    words = re.split(r"[\s;]+", visible)
    return words.count("{") - words.count("}")


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
    _assert_no_always_false_guard(hook_commands, ".githooks/pre-commit")
    assert "scripts/quality_check.py --mode full" in hook_commands
    assert "setup_buildAndFit.sh" in hook_commands

    # Naming the marker is not enough: a `-k "not <test>"` alongside it
    # deselects the gate while the marker is still there. Confirmed by
    # sabotage - it did, and this test passed. So the line must both
    # keep the marker and not select the test away.
    hook_pytest_lines = _pytest_command_lines(hook_text).splitlines()
    integration_lines = [
        line for line in hook_pytest_lines if f"tests/{_INTEGRATION_TEST_FILE}" in line
    ]
    assert integration_lines, (
        ".githooks/pre-commit runs no pytest command naming " f"tests/{_INTEGRATION_TEST_FILE}"
    )
    scientific_test = "test_authoritative_j100_j50_workflows_match_frozen_reference"
    scientific_markers = _dependency_marked_tests(repo_root / "tests" / _INTEGRATION_TEST_FILE)[
        scientific_test
    ]
    assert _invocation_runs_test_anywhere(
        integration_lines, _INTEGRATION_TEST_FILE, scientific_test, scientific_markers, "-m"
    ), (
        ".githooks/pre-commit names the scientific gate but no invocation "
        "actually leaves test_authoritative_j100_j50_workflows_match_frozen_reference "
        "selected"
    )

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


def _pytest_marker_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """The `pytest.mark.<name>` markers applied to one function.

    Read from `decorator_list`, so it does not matter where in the
    stack the marker sits, what other decorators surround it, whether
    it is called with arguments, or whether any of them span several
    lines. `@pytest.mark.x` and `@mark.x` are both recognised.
    """
    names: set[str] = set()
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not isinstance(target, ast.Attribute):
            continue
        owner = target.value
        if (isinstance(owner, ast.Attribute) and owner.attr == "mark") or (
            isinstance(owner, ast.Name) and owner.id == "mark"
        ):
            names.add(target.attr)
    return names


def _dependency_marked_tests(test_file: Path) -> dict[str, set[str]]:
    """Every requires_analysis_dependencies-marked test in one file, each
    with the full set of markers it carries.

    The markers are read from the file rather than restated in this
    test, so a gate selector is always checked against the test's real
    markers. Restating them is how the map below drifted from the file
    once already.
    """
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    marked: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            markers = _pytest_marker_names(node)
            if "requires_analysis_dependencies" in markers:
                marked[node.name] = markers
    return marked


def _dependency_marked_test_names(test_file: Path) -> list[str]:
    """Names of every requires_analysis_dependencies-marked test in one file.

    Parsed, not scanned. The line-based version this replaced looked for
    the marker and then expected either another `@pytest.mark.` line or
    the `def`, so it silently dropped a marked test in three shapes,
    each confirmed against a synthetic file:

    - any other decorator in between, such as `@mock.patch(...)`;
    - `async def`, which it never recognised;
    - a *multi-line* `@pytest.mark.parametrize(...)` below the marker,
      whose continuation lines are neither a decorator nor a `def` -
      the likeliest of the three here, since this suite parametrizes
      widely.

    A dropped test keeps
    `_assert_covers_every_dependency_marked_test()`'s selector-map
    equality true, so nothing would force a gate selector for it and it
    would never run anywhere.
    """
    return list(_dependency_marked_tests(test_file))


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


def _pytest_arguments(line: str) -> str:
    """The part of a command line that pytest itself parses.

    Only the text after the `pytest` token: `python -m pytest` carries
    an `-m` of its own for the module name, and reading that as the
    marker filter would make every marker check compare against the
    string "pytest".
    """
    token = _PYTEST_TOKEN.search(line)
    return line[token.end() :] if token else line


def _pytest_option_values(line: str, option: str) -> list[str]:
    """Every value passed to `option` on one pytest command line, unquoted.

    Reading only the first occurrence was enough while every option of
    interest appeared at most once. `--deselect` is repeatable, and one
    line can carry several, so all of them are returned. Both
    `--option value` and `--option=value` are read, and the option has
    to start a word, so `-m` inside `--maxfail` is not one.
    """
    pattern = rf"(?<!\S){re.escape(option)}(?:\s+|=)(\"[^\"]*\"|'[^']*'|\S+)"
    return [match.group(1).strip("\"'") for match in re.finditer(pattern, _pytest_arguments(line))]


def _pytest_option_value(line: str, option: str) -> str | None:
    """The value `option` actually has, or None when it is absent.

    The *last* occurrence, because `-k` and `-m` use argparse's `store`
    action: a repeated option overwrites, so the last one is the filter
    pytest applies. Reading the first was wrong, and silently so -
    `-m "requires_analysis_dependencies" -m requires_root` left the
    coverage checks passing while the plotting gate dropped a marked
    test and still exited 0. Measured.

    `--deselect` is an `append` action, where every occurrence counts;
    `_deselects_test()` reads them all through
    `_pytest_option_values()` for that reason.
    """
    values = _pytest_option_values(line, option)
    return values[-1] if values else None


# Letters that a single-dash pytest option can carry without affecting
# which tests are selected: -v, -q, -s, -x, -l and any bundle of them.
# The real gate lines use only -v (plus -k/-m), confirmed by reading
# every pytest command in all four gate sources.
_SELECTION_NEUTRAL_SHORT_LETTERS = frozenset("vqsxl")


def _unreadable_short_option(arguments: str) -> str | None:
    """A single-dash option this reader cannot interpret, if any.

    pytest accepts a short option's value attached (`-knothing`) and
    bundled behind other flags (`-vk nothing`), and either form makes
    the option readers above see nothing - which they would otherwise
    report as "no filter", the opposite of the truth. Both were
    measured: `-vk <one test name>` took the plotting gate from 16
    dependency-marked tests to 1, exit code 0, with every coverage
    check passing.

    So rather than enumerate the ways a bundle can hide a filter, only
    the forms this reader can actually interpret are accepted: a bare
    `-k`/`-m` with its value as the next word, `-k=`/`-m=`, and bundles
    made entirely of selection-neutral letters. Anything else is
    unreadable, and unreadable counts as unproven. A new short option
    in a gate therefore fails here until it is considered, which is the
    intended cost.
    """
    for word in arguments.split():
        if not word.startswith("-") or word.startswith("--") or word == "-":
            continue
        if word in ("-k", "-m") or word[:3] in ("-k=", "-m="):
            continue
        if set(word[1:].split("=", 1)[0]) <= _SELECTION_NEUTRAL_SHORT_LETTERS:
            continue
        return word
    return None


# Collect but never run. Nothing executes and pytest still exits 0, so
# this is the one veto that leaves no trace at all in the gate's
# result.
_COLLECT_ONLY = re.compile(r"(?<!\S)(?:--collect-only|--co)(?!\S)")


# Options that consume the word after them, so that word is a value
# and not a test path. Without this, `--deselect tests/x.py::y` would
# be read as the invocation *selecting* x.py::y.
_VALUE_TAKING_OPTIONS = (
    "-k",
    "-m",
    "-p",
    "-n",
    "-o",
    "--deselect",
    "--ignore",
    "--ignore-glob",
    "--maxfail",
    "--rootdir",
    "--junitxml",
    "--override-ini",
)


def _pytest_positional_arguments(line: str) -> list[str]:
    """The words a pytest command line passes as test paths."""
    words = [word.strip("\"'") for word in _pytest_arguments(line).split()]
    positional: list[str] = []
    skip = False
    for word in words:
        if skip:
            skip = False
            continue
        if word.startswith("-"):
            skip = word in _VALUE_TAKING_OPTIONS
            continue
        positional.append(word)
    return positional


def _file_references(line: str, test_file: str) -> list[str]:
    """Every positional argument on this line that refers to `test_file`."""
    target = f"tests/{test_file}"
    return [
        argument
        for argument in _pytest_positional_arguments(line)
        if argument == target or argument.startswith(f"{target}::")
    ]


def _selects_whole_file(line: str, test_file: str, test_name: str) -> bool:
    """True when this line reaches `test_name` at all.

    A pytest argument can name a single test rather than a file -
    `tests/test_pre_fit.py::test_one` - and then only that test runs
    from it. The coverage checks pick their lines by looking for the
    filename, and a node id contains the filename, so a gate narrowed
    this way looked fully covered: naming one node id took
    `tests/test_pre_fit.py` from two dependency-marked tests to one and
    both coverage tests still passed. Measured. This is the positional
    spelling of the "node selectors" the `--deselect` check already
    rejects.

    Requiring a real positional reference also means a line that
    mentions the file *only* in an option value - `--deselect
    tests/test_pre_fit.py` - is correctly not treated as running it.
    """
    references = _file_references(line, test_file)
    if not references:
        return False
    if any("::" not in reference for reference in references):
        return True
    return any(test_name in reference.split("::")[1:] for reference in references)


def _deselects_test(line: str, test_file: str, test_name: str) -> bool:
    """True when a `--deselect` on this line removes the mapped test.

    `--deselect` is a third filter, independent of both `-k` and `-m`,
    and its whole purpose is to remove a named test. Checking only the
    two expression filters missed it: one `--deselect` took the
    plotting gate from 18 dependency-marked tests to 17, and pointing
    it at a file took it to 16, with pytest still exiting 0. Measured.

    Path matching is deliberately loose - any path ending in the test's
    own file, or the tests directory itself - so an unfamiliar spelling
    causes a false failure rather than a false pass.
    """
    for value in _pytest_option_values(line, "--deselect"):
        path, _, node = value.partition("::")
        path = path.rstrip("/")
        names = [part for part in node.split("::") if part]
        targets_file = path in ("", "tests", f"tests/{test_file}") or path.endswith(f"/{test_file}")
        if targets_file and (not names or names[-1] == test_name):
            return True
    return False


def _expression_selects(expression: str, is_true: Callable[[str], bool]) -> bool:
    """Evaluate one pytest `-k`/`-m` expression against a single test.

    pytest's filters are boolean expressions, and `-k` and `-m` are
    combined with AND, so the only sound way to answer "does this
    invocation still run that test" is to evaluate them the way pytest
    does. Every approximation tried here has been wrong in a different
    direction:

    - substring membership accepted `-k "not <name>"`, which runs the
      opposite tests;
    - rejecting any `not` accepted `-k "<name> and nonexistent"`, which
      contains the name, carries no negation, and selects *nothing*.
      Confirmed against real pytest: it collected 0 of 3 tests while the
      check reported the gate covered. The same trick works on `-m`,
      by appending `and nonexistent_marker`.

    `is_true` decides one bare term: for `-m`, whether the test carries
    that marker; for `-k`, whether the term appears in its name, which
    is pytest's own substring rule.

    An expression this cannot parse, or one using any construct beyond
    `and`/`or`/`not`/parentheses, returns False - unproven counts as not
    selected, so the coverage check fails loudly rather than passing on
    something it did not understand.
    """

    def evaluate(node: ast.expr) -> bool:
        if isinstance(node, ast.BoolOp):
            results = [evaluate(value) for value in node.values]
            return all(results) if isinstance(node.op, ast.And) else any(results)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not evaluate(node.operand)
        if isinstance(node, ast.Name):
            return is_true(node.id)
        raise ValueError(f"unsupported term in a pytest expression: {ast.dump(node)}")

    try:
        return evaluate(ast.parse(expression, mode="eval").body)
    except (SyntaxError, ValueError):
        return False


def _filters_keep_test(line: str, test_file: str, test_name: str, markers: set[str]) -> bool:
    """True when nothing on this pytest line stops the test from running.

    Every mechanism pytest offers for removing a test has to be judged
    here, not just the ones this check happened to know about first.
    Each of these was found by sabotage, after the previous round fixed
    the two expression filters and stopped there:

    - `-k` and `-m`, evaluated as expressions, because pytest combines
      them with AND and either alone can empty the gate;
    - `--deselect`, a third filter that removes a named test or a whole
      file regardless of both expressions;
    - `--collect-only`, which collects everything and runs none of it,
      while still exiting 0.

    An absent option filters nothing. A short option this reader cannot
    interpret counts as not proven rather than absent - including
    plugin disabling, since `-p no:python` collects nothing at all and
    `-p` is not a selection-neutral flag. A rule of its own was written
    for that first and then removed: it never fired, because
    `_unreadable_short_option()` already covered it, and two rules over
    the same ground is what let these checks drift apart before.
    """
    arguments = _pytest_arguments(line)
    if _COLLECT_ONLY.search(arguments):
        return False
    if _unreadable_short_option(arguments) is not None:
        return False
    if not _selects_whole_file(line, test_file, test_name):
        return False
    if _deselects_test(line, test_file, test_name):
        return False
    for option, is_true in (
        ("-k", lambda term: term in test_name),
        ("-m", lambda term: term in markers),
    ):
        value = _pytest_option_value(line, option)
        if value is not None and not _expression_selects(value, is_true):
            return False
    return True


# A command wrapped in an always-false guard still appears in the
# executable lines, so "this file runs X" is not proved by finding X
# there. Confirmed by sabotage: wrapping .githooks/pre-commit's
# lightweight gate in `if false; then ... fi` left its policy test
# passing. A general reachability analysis of shell is out of scope, so
# the literal always-false guards are rejected outright instead.
_ALWAYS_FALSE_GUARD = re.compile(r"\b(?:if|while|until)\s+(?:false\b|!\s*true\b)")

# One word of an `rm` command that turns it into a recursive delete:
# any bundle of short flags containing `r`/`R` (`-r`, `-R`, `-rf`,
# `-fr`), or the long spelling. Matched with fullmatch against a whole
# word, so `--no-preserve-root` - which contains `r` but is not itself
# recursive - is not one, and neither is any operand.
_RECURSIVE_RM_FLAG = re.compile(r"-[A-Za-z]*[rR][A-Za-z]*|--recursive")

# Where one command's arguments stop and the next command begins, so a
# later command's flags are never attributed to `rm`.
_ARGUMENT_LIST_END = re.compile(r"[;&|<>\n]")


# A workflow step or job can be disabled by a condition while every
# character of its command stays on the page - the YAML equivalent of
# `if false; then ... fi`, which is rejected in shell above. Confirmed
# by sabotage: `if: false` on the scientific gate step left all three
# CI policy tests passing.
#
# Any condition is rejected, not only a literal false. A computed one
# (`${{ github.event_name == 'never' }}`) cannot be decided here, and
# evaluating GitHub's expression language is as out of scope as shell
# reachability analysis. No workflow in this repository uses `if:` at
# all, so a blanket rejection costs nothing today and fails loudly if
# one is ever added - at which point this check has to be taught to
# judge it rather than quietly widened.
_YAML_CONDITION = re.compile(r"^\s*(?:-\s+)?if:\s*(.+?)\s*$", re.MULTILINE)

# pytest reads this environment variable and applies whatever it
# contains to every invocation, so one line anywhere in a gate source
# can filter every gate in it. Confirmed: `PYTEST_ADDOPTS="-k
# nothing_matches_this"` took a 5-test file to 0 selected.
_PYTEST_ADDOPTS_ASSIGNMENT = re.compile(r"\bPYTEST_ADDOPTS\b")


def _yaml_conditions(text: str) -> list[str]:
    """Every `if:` condition in a workflow file."""
    return [match.group(1) for match in _YAML_CONDITION.finditer(text)]


def _installer_views(installer_text: str, description: str) -> tuple[str, str, str]:
    """The three views of an installer these policy tests assert against.

    `script` has comments removed whole-line *and* trailing, so no
    assertion can be satisfied by commented-out text. `commands` is
    only the lines that run something, for claims about what the
    installer does; `invocations` drops function *definition* lines too,
    for claims about what it calls. Echo lines survive in `script`
    alone, because several assertions are about messages the installer
    prints.

    An always-false guard is rejected here, once, for both installers.
    The previous version of these tests kept only whole-line comments
    and never checked for a guard, so three sabotages passed: replacing
    both real `cmake --build` calls with `true # cmake --build`, with
    `echo "cmake --build"`, and guarding `run_build()`'s whole body -
    each valid shell, each building nothing.
    """
    commands = _executable_command_lines(installer_text)
    _assert_no_always_false_guard(commands, description)
    return (
        _uncommented_lines(installer_text),
        commands,
        _shell_invocation_lines(installer_text),
    )


def _recursive_delete(text: str) -> str | None:
    """The first recursive `rm` command in `text`, or None.

    `"rm -rf" not in text` is satisfied by `rm -fr`, `rm -r -f` and
    `rm --recursive` - confirmed by sabotage on both installers, whose
    tests advertise that they are non-destructive.

    Only the words `rm` is actually passed are examined, and of those
    only the ones that are options. The regex this replaced read the
    flags positionally and allowed no dash at all, so it counted the
    *operand* as a flag: `rm report.txt`, `rm results.json` and
    `rm -f error.log` were all reported as recursive deletes. That is a
    false failure rather than a false pass - the two installer tests
    below would reject an ordinary single-file cleanup - which is why
    this one is made precise instead of deliberately over-inclusive.
    Reading words also catches options after the operand
    (`rm build -rf`), which `rm` itself accepts and the positional
    regex missed in both spellings.
    """
    for command in re.finditer(r"\brm\b", text):
        arguments = _ARGUMENT_LIST_END.split(text[command.end() :], 1)[0]
        for word in arguments.split():
            if _RECURSIVE_RM_FLAG.fullmatch(word.strip("\"'")):
                return f"rm{arguments}".strip()
    return None


def _invocation_runs_test(
    line: str,
    test_file: str,
    test_name: str,
    markers: set[str],
    designated_option: str,
) -> bool:
    """True when one pytest command line really runs the mapped test.

    Two separate requirements, and both have been the hole here at
    different times:

    - `designated_option` - `-k` for the runtime-readiness gate, `-m`
      for the scientific one - must be present, so the gate selects the
      test deliberately rather than merely failing to exclude it;
    - both filters must actually leave the test selected, evaluated
      against its real name and markers.

    Checking only one option let the other empty the gate: the
    readiness line could add `-m "not requires_analysis_dependencies"`,
    the scientific line `-k "not authoritative_j100_j50_..."`.
    Confirmed by sabotage against both `scripts/run_all_gates.sh` and
    the CI workflow. Checking the *expression* by substring then let an
    unsatisfiable extra term through - see `_expression_selects()`.
    """
    if _pytest_option_value(line, designated_option) is None:
        return False
    return _filters_keep_test(line, test_file, test_name, markers)


def _assert_no_always_false_guard(commands: str, source_description: str) -> None:
    guard = _ALWAYS_FALSE_GUARD.search(commands)
    assert guard is None, (
        f"{source_description} guards a command with {guard.group(0)!r}, which "
        "disables it while leaving its text in place - so every "
        '"this file runs X" assertion here would still pass'
    )


def _invocation_runs_test_anywhere(
    lines: list[str],
    test_file: str,
    test_name: str,
    markers: set[str],
    designated_option: str,
) -> bool:
    return any(
        _invocation_runs_test(line, test_file, test_name, markers, designated_option)
        for line in lines
    )


def _defers_annotation_evaluation(path: Path) -> bool:
    """True when `from __future__ import annotations` is in effect."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def _annotation_has_pep604_union(annotation: ast.AST | None) -> bool:
    return annotation is not None and any(
        isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr) for sub in ast.walk(annotation)
    )


def _signature_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef):
    """Every annotation in a signature, all of which are evaluated when
    the `def` executes: positional-only, regular and keyword-only
    arguments, `*args`, `**kwargs`, and the return annotation."""
    arguments = node.args
    for argument in (
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        arguments.vararg,
        arguments.kwarg,
    ):
        if argument is not None and argument.annotation is not None:
            yield argument.annotation
    if node.returns is not None:
        yield node.returns


def _evaluated_pep604_unions(path: Path) -> list[tuple[int, str]]:
    """Every `X | Y` annotation this file evaluates rather than defers.

    Confirmed slot by slot against the real LCG Python 3.9.12: a union
    raises `TypeError` in a positional-only, regular, keyword-only,
    `*args`, `**kwargs` or return annotation, and in a module-level or
    class-level annotated assignment. It does *not* raise in an
    annotation on a local variable inside a function body, which is
    never evaluated - so those are excluded, which is why this file's
    own `quote: str | None = None` locals were always safe.

    Nested `def`s and classes defined inside a function are still
    reported. Their annotations are evaluated when the enclosing scope
    runs rather than at import, so the break is later rather than
    absent; flagging them is the conservative direction for a check
    whose whole purpose is to keep the scientific gates loadable.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []

    def _target_name(node: ast.AnnAssign) -> str:
        target = node.target
        return target.id if isinstance(target, ast.Name) else "<annotated assignment>"

    def _visit(node: ast.AST, inside_function_body: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(
                    _annotation_has_pep604_union(annotation)
                    for annotation in _signature_annotations(child)
                ):
                    found.append((child.lineno, child.name))
                _visit(child, True)
            elif isinstance(child, ast.ClassDef):
                # A class body executes wherever it appears, so its
                # annotated assignments are evaluated there.
                _visit(child, False)
            elif isinstance(child, ast.AnnAssign):
                if not inside_function_body and _annotation_has_pep604_union(child.annotation):
                    found.append((child.lineno, _target_name(child)))
            else:
                _visit(child, inside_function_body)

    _visit(tree, False)
    return found


def _outside_function_bodies(lines: list[str]) -> list[str]:
    """The logical lines that are not inside a shell function body.

    A command inside a function that nothing calls never runs, while
    its text sits in the file exactly as if it did. Confirmed by
    sabotage: moving the whole plotting gate into a `never_called() {
    ... }` wrapper is valid shell, runs nothing, leaves `failures` at
    zero so the script reports "All gates passed", and left both
    coverage tests passing.

    The installer checks already dropped function *definition* lines
    for the same reason; this drops the whole body. Deciding which
    functions are really called is a call-graph problem and out of
    scope, exactly as shell reachability was for `if false`, so the
    rule is that a gate command has to sit at top level. The real gate
    sources satisfy it: `run_gate` is a function, but every pytest
    command is passed to it as an *argument* from top level, not
    written inside its body.

    Every form bash accepts is recognised, not just the one this rule
    was first written against: the `function name` keyword form, a
    hyphenated name, a parenthesis body, and a body whose opening
    brace sits on the following line. Depth is counted by
    `_body_depth_change()`, so a brace that is not a delimiter cannot
    end a body early and expose the rest of it as top-level text.
    """
    kept: list[str] = []
    opener = ""
    depth = 0
    awaiting_body = False
    for line in lines:
        if opener:
            depth += _body_depth_change(line, opener)
            if depth <= 0:
                opener, depth = "", 0
            continue
        if awaiting_body:
            awaiting_body = False
            openers = [char for char in _FUNCTION_BODY_CLOSERS if char in line]
            if not openers:
                kept.append(line)
                continue
            opener = min(openers, key=line.index)
            depth = _body_depth_change(line, opener)
            if depth <= 0:
                opener, depth = "", 0
            continue
        match = _SHELL_FUNCTION_DEFINITION.match(line)
        if match is None:
            kept.append(line)
            continue
        if match.group("opener") is None:
            awaiting_body = True
            continue
        opener = match.group("opener")
        depth = _body_depth_change(line, opener)
        if depth <= 0:
            opener, depth = "", 0
    return kept


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

    Lines inside a shell function body are dropped too, because a
    command in a function nothing calls never runs - see
    `_outside_function_bodies()`; so are heredoc bodies, because a
    heredoc body is printed rather than run - see
    `_outside_heredoc_bodies()`.
    """
    return "\n".join(
        line
        for line in _outside_function_bodies(
            _outside_heredoc_bodies(_join_continuations(_uncommented_lines(text)))
        )
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
# Which pytest option each of that file's marked tests is expected to
# be selected *with*. Only the option, not the expression: the test's
# real name and markers are read from the file by
# `_dependency_marked_tests()` and the invocation's filters are
# evaluated against them, so there is nothing here to drift out of step
# with the test itself.
_INTEGRATION_TEST_DESIGNATED_OPTIONS = {
    # the dedicated runtime-readiness invocation selects this one by name
    "test_authoritative_setup_provides_scientific_runtime": "-k",
    # the scientific gate selects this one by marker
    "test_authoritative_j100_j50_workflows_match_frozen_reference": "-m",
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

    # A gate wrapped in `if false; then ... fi` still contributes its
    # pytest command to the lines above, so every assertion here would
    # pass while the gate never ran. The hook's own check has rejected
    # that since it was found there; these two never did. Confirmed by
    # sabotage: wrapping run_all_gates.sh's whole scientific gate in a
    # multiline `if false` left both of these tests passing.
    _assert_no_always_false_guard(_executable_command_lines(raw_text), source_description)

    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root / "tests"

    integration_test_file = tests_dir / _INTEGRATION_TEST_FILE
    integration_marked_tests = _dependency_marked_tests(integration_test_file)
    assert set(integration_marked_tests) == set(_INTEGRATION_TEST_DESIGNATED_OPTIONS), (
        f"{_INTEGRATION_TEST_FILE}'s requires_analysis_dependencies tests changed "
        f"({sorted(integration_marked_tests)}) without updating this test's own "
        "per-test selector map"
    )
    command_lines = command_text.splitlines()
    missing_integration_selectors = [
        test_name
        for test_name, designated_option in _INTEGRATION_TEST_DESIGNATED_OPTIONS.items()
        if not _invocation_runs_test_anywhere(
            [line for line in command_lines if f"tests/{_INTEGRATION_TEST_FILE}" in line],
            _INTEGRATION_TEST_FILE,
            test_name,
            integration_marked_tests[test_name],
            designated_option,
        )
    ]
    assert not missing_integration_selectors, (
        f"{source_description} is missing a dedicated selector for these "
        f"{_INTEGRATION_TEST_FILE} tests: {missing_integration_selectors}"
    )

    # Naming the file is not enough, and neither is naming it alongside
    # a marker filter that keeps the marker. This assertion promises
    # that every dependency-marked test runs, so every one of them is
    # checked individually against the invocations that name its file.
    # Two sabotages got past the weaker versions of this:
    #
    # - `-m "not requires_analysis_dependencies"`, which left every
    #   filename present while deselecting all of them;
    # - a single `-k <one test name>` added to the plotting gate, which
    #   took it from 48 marked tests to 1 while every file was still
    #   named and the marker filter still kept the marker. Measured.
    #
    # Files are enumerated by the deliberately over-inclusive text scan
    # and their tests by the AST. If a flagged file has no marked test
    # the AST can see, the file-level check still applies, so the
    # over-inclusive net is not lost.
    marked_files = _tests_dir_files_marked_requires_analysis_dependencies(tests_dir)
    uncovered: list[str] = []
    for name in marked_files:
        if name == _INTEGRATION_TEST_FILE:
            continue
        lines_naming_file = [line for line in command_lines if f"tests/{name}" in line]
        marked_tests = _dependency_marked_tests(tests_dir / name)
        if not marked_tests:
            # No test name here, so a `-k` on such a line cannot be
            # shown to keep anything and is treated as deselecting -
            # which is what the empty name below means. Only the marker
            # filter can be judged. No file is in this state today;
            # this is the over-inclusive net, kept deliberately.
            if not any(
                _filters_keep_test(line, name, "", {"requires_analysis_dependencies"})
                for line in lines_naming_file
            ):
                uncovered.append(name)
            continue
        uncovered.extend(
            f"{name}::{test_name}"
            for test_name, markers in sorted(marked_tests.items())
            if not any(
                _filters_keep_test(line, name, test_name, markers) for line in lines_naming_file
            )
        )
    assert not uncovered, (
        f"{source_description} names these files but does not actually run these "
        f"requires_analysis_dependencies tests: {uncovered}"
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


def test_pytest_filters_are_evaluated_against_the_real_test() -> None:
    """A selector that names a test is not a selector that runs it.

    Pins every sabotage that has found this check wrong, in both
    directions:

    - inverting the runtime-readiness `-k`, the scientific `-m`, or the
      prepared-dependency `-m`, each of which left the gate-coverage
      tests passing while running the opposite tests, because the check
      searched for the expression as a substring and `not <expression>`
      contains it;
    - adding an unsatisfiable term - `-k "<name> and nonexistent"`, or
      `-m "integration and requires_root and nonexistent_marker"` -
      which contains the expected text, carries no negation, and
      selects nothing. Confirmed against real pytest: 0 of 3 tests
      collected, while the check reported the gate covered.

    The second kind is why these filters are now evaluated rather than
    matched. Approximating pytest's boolean language was wrong twice,
    each time in a way the previous fix did not cover.
    """
    readiness = "test_authoritative_setup_provides_scientific_runtime"
    readiness_markers = {"integration", "requires_analysis_dependencies"}
    scientific = "test_authoritative_j100_j50_workflows_match_frozen_reference"
    scientific_markers = {"integration", "requires_root", "requires_analysis_dependencies"}

    # `python -m pytest`'s own -m names the module, not a marker filter.
    marker = 'python -m pytest tests/test_x.py -m "requires_analysis_dependencies" -v'
    unfiltered = "python -m pytest tests/test_x.py -v"
    assert _pytest_option_value(marker, "-m") == "requires_analysis_dependencies"
    assert _pytest_option_value(unfiltered, "-m") is None

    # Plain terms, evaluated against the test's real markers and name.
    assert _expression_selects("requires_analysis_dependencies", lambda t: t in scientific_markers)
    assert not _expression_selects("requires_root", lambda t: t in readiness_markers)
    assert _expression_selects("authoritative_j100_j50", lambda t: t in scientific)

    # Negation, including the parenthesised negation of a compound
    # expression, which no simple `not`-rejecting rule handles.
    assert not _expression_selects(
        "not requires_analysis_dependencies", lambda t: t in scientific_markers
    )
    assert _expression_selects("integration and requires_root", lambda t: t in scientific_markers)
    assert not _expression_selects(
        "not (integration and requires_root)", lambda t: t in scientific_markers
    )
    # `not` on an unrelated term does not disqualify a real selection -
    # the blanket "any `not` is fatal" rule got this wrong and was
    # documented as deliberately conservative. Evaluating gets it right.
    assert _expression_selects(
        "requires_analysis_dependencies and not slow", lambda t: t in scientific_markers
    )

    # An extra term that nothing satisfies, in both options.
    assert not _expression_selects(f"{scientific} and nonexistent", lambda t: t in scientific)
    assert not _expression_selects(
        "integration and requires_root and nonexistent_marker",
        lambda t: t in scientific_markers,
    )
    # `or` keeps it selected, which is not something to reject.
    assert _expression_selects(
        "nonexistent_marker or requires_root", lambda t: t in scientific_markers
    )

    # Anything unparseable, or beyond and/or/not, is not proof of
    # selection.
    assert not _expression_selects("requires_root and", lambda t: True)
    assert not _expression_selects("requires_root == 1", lambda t: True)

    # Both filters are always judged, whichever one the gate selects
    # with: an absent option filters nothing, and either option alone
    # can empty the gate.
    readiness_line = f"python -m pytest tests/{_INTEGRATION_TEST_FILE} -k {readiness} -v"
    assert _invocation_runs_test(
        readiness_line, _INTEGRATION_TEST_FILE, readiness, readiness_markers, "-k"
    )
    assert not _invocation_runs_test(
        f'{readiness_line} -m "not requires_analysis_dependencies"',
        _INTEGRATION_TEST_FILE,
        readiness,
        readiness_markers,
        "-k",
    )
    assert not _invocation_runs_test(
        f"{readiness_line} -m nonexistent_marker",
        _INTEGRATION_TEST_FILE,
        readiness,
        readiness_markers,
        "-k",
    )
    # The designated option must be present at all: the gate has to
    # select the test deliberately, not merely fail to exclude it.
    assert not _invocation_runs_test(
        f"python -m pytest tests/{_INTEGRATION_TEST_FILE} -v",
        _INTEGRATION_TEST_FILE,
        readiness,
        readiness_markers,
        "-k",
    )

    scientific_line = (
        f'python -m pytest tests/{_INTEGRATION_TEST_FILE} -m "integration and requires_root" -v'
    )
    assert _invocation_runs_test(
        scientific_line, _INTEGRATION_TEST_FILE, scientific, scientific_markers, "-m"
    )
    assert not _invocation_runs_test(
        f'{scientific_line} -k "not {scientific}"',
        _INTEGRATION_TEST_FILE,
        scientific,
        scientific_markers,
        "-m",
    )
    assert not _invocation_runs_test(
        f"{scientific_line} -k {readiness}",
        _INTEGRATION_TEST_FILE,
        scientific,
        scientific_markers,
        "-m",
    )


def test_a_named_command_is_not_a_command_that_runs() -> None:
    """Three more ways text can be present while the thing never runs.

    Each pins a sabotage that passed before the check it guards was
    changed:

    - a `-k "not <test>"` beside a correct `-m` marker filter, which
      deselected `.githooks/pre-commit`'s scientific gate;
    - an always-false guard, which disabled that hook's lightweight
      gate while leaving its text in the executable lines;
    - a recursive delete spelled `rm -fr`, `rm -r -f` or
      `rm --recursive`, none of which the old `"rm -rf" not in text`
      check saw, in tests that advertise the installers as
      non-destructive;
    - the opposite failure in that same check once it became a regex:
      `rm report.txt` was read as recursive, because the pattern
      allowed zero dashes and so matched the operand.
    """
    marker = "integration and requires_root"
    test_name = "test_authoritative_j100_j50_workflows_match_frozen_reference"
    markers = {"integration", "requires_root", "requires_analysis_dependencies"}
    base = f'python -m pytest tests/test_analysis_workflows_integration.py -m "{marker}"'

    assert _invocation_runs_test(base, _INTEGRATION_TEST_FILE, test_name, markers, "-m")
    assert _invocation_runs_test(
        f'{base} -k "{test_name}"', _INTEGRATION_TEST_FILE, test_name, markers, "-m"
    )
    assert not _invocation_runs_test(
        f'{base} -k "not {test_name}"', _INTEGRATION_TEST_FILE, test_name, markers, "-m"
    )
    assert not _invocation_runs_test(
        f'{base} -k "some_other_test"', _INTEGRATION_TEST_FILE, test_name, markers, "-m"
    )
    assert not _invocation_runs_test(
        'python -m pytest tests/test_analysis_workflows_integration.py -m "not ' f'({marker})"',
        _INTEGRATION_TEST_FILE,
        test_name,
        markers,
        "-m",
    )

    for guard in ("if false; then run_gate; fi", "if false && ! run_gate; then", "while false"):
        with pytest.raises(AssertionError):
            _assert_no_always_false_guard(guard, "a test fixture")
    _assert_no_always_false_guard("if ! run_gate; then\nfi", "a test fixture")

    for destructive in (
        "rm -rf build",
        "rm -fr build",
        "rm -r -f build",
        "rm --recursive build",
        "rm -R build",
        # options after the operand, which rm itself accepts
        "rm build -rf",
    ):
        assert _recursive_delete(destructive), destructive
    # A non-recursive delete of one file is not what these tests forbid.
    # The first five benign cases are the false positives the earlier
    # positional regex produced: it allowed zero dashes, so the operand
    # itself was read as a flag whenever it contained an `r`.
    for benign in (
        # an extensionless operand, which is a bare word of letters and
        # so is only distinguishable from a flag bundle by the dash
        "rm report",
        "rm report.txt",
        "rm results.json",
        "rm -f error.log",
        "rm -- report.txt",
        'rm -f "$log"',
        "rm /tmp/one-file",
        # not itself recursive, despite containing `r`
        "rm --no-preserve-root -f foo",
        # a later command's flags do not belong to rm
        "rm foo.txt && tar -rf archive.tar x",
    ):
        assert not _recursive_delete(benign), benign


def test_every_evaluated_annotation_slot_is_inspected(tmp_path: Path) -> None:
    """The 3.9 check must cover every slot that really raises there.

    Each case below was run under the real LCG Python 3.9.12 before this
    test was written: all six raise `TypeError: unsupported operand
    type(s) for |`, and the function-local one does not. An earlier
    version of `_evaluated_pep604_unions()` inspected only regular and
    keyword-only arguments and the return annotation, so it missed five
    of the six and reported no offender.
    """
    raises_on_python_39 = {
        "posonly": "def f(x: str | None, /):\n    pass\n",
        "vararg": "def f(*args: str | None):\n    pass\n",
        "kwarg": "def f(**kw: str | None):\n    pass\n",
        "module_annotation": "X: str | None = None\n",
        "class_annotation": "class C:\n    X: str | None = None\n",
        "regular_and_return": "def f(x: str | None) -> str | None:\n    return x\n",
    }
    safe_on_python_39 = {
        # never evaluated, so it cannot raise - this file's own locals
        # rely on that
        "function_local": "def f():\n    x: str | None = None\n    return x\n",
        "typing_optional": (
            "from typing import Optional\ndef f(x: Optional[str]) -> Optional[str]:\n"
            "    return x\n"
        ),
        "no_annotations": "def f(x):\n    return x\n",
    }

    for name, source in raises_on_python_39.items():
        path = tmp_path / f"{name}.py"
        path.write_text(source, encoding="utf-8")
        assert _evaluated_pep604_unions(path), f"{name} evaluates a union but was not reported"

    for name, source in safe_on_python_39.items():
        path = tmp_path / f"{name}.py"
        path.write_text(source, encoding="utf-8")
        assert not _evaluated_pep604_unions(path), f"{name} is safe on 3.9 but was reported"

    # Deferring evaluation makes any of them safe, which is the fix the
    # policy test recommends.
    deferred = tmp_path / "deferred.py"
    deferred.write_text(
        "from __future__ import annotations\n" + raises_on_python_39["posonly"], encoding="utf-8"
    )
    assert _evaluated_pep604_unions(deferred)
    assert _defers_annotation_evaluation(deferred)


def test_a_trailing_comment_is_not_part_of_the_command() -> None:
    """`#` after a real command hides inert text on a live line.

    Pins the sabotage: a runtime-readiness gate rewritten to
    `-m "not requires_analysis_dependencies" -v # -k <selector>` kept
    the expected selector visible to the coverage check while selecting
    nothing at all.
    """
    line = (
        "python -m pytest tests/test_analysis_workflows_integration.py "
        '-m "not requires_analysis_dependencies" -v '
        "# -k authoritative_setup_provides_scientific_runtime"
    )
    commands = _pytest_command_lines(line)
    assert "-k" not in commands
    assert _pytest_option_value(commands, "-k") is None
    assert not _invocation_runs_test(
        commands,
        _INTEGRATION_TEST_FILE,
        "test_authoritative_setup_provides_scientific_runtime",
        {"integration", "requires_analysis_dependencies"},
        "-k",
    )

    # A `#` inside quotes, or with no leading whitespace, is data - not a
    # comment - and must survive both extractors.
    kept = _executable_command_lines(
        'grep "#define FOO" file.c\nrun_thing --opt="a#b"\nreal_command  # disabled\n'
    )
    assert '"#define FOO"' in kept
    assert '--opt="a#b"' in kept
    assert "real_command" in kept
    assert "disabled" not in kept

    # Comments must be removed *before* continuations are joined. A `\\`
    # inside a comment is not a line continuation, and stripping after
    # the join let such a comment swallow the following line - losing a
    # real command, which is the opposite failure and just as wrong.
    swallowing = "setup_thing  # see docs \\\npython scripts/quality_check.py --mode full\n"
    assert "scripts/quality_check.py --mode full" in _executable_command_lines(swallowing)
    assert "see docs" not in _executable_command_lines(swallowing)

    swallowing_pytest = (
        "run_gate x  # note \\\n"
        'python -m pytest tests/test_pre_fit.py -m "requires_analysis_dependencies"\n'
    )
    assert "tests/test_pre_fit.py" in _pytest_command_lines(swallowing_pytest)


# Legacy Python-2-era modules that a Python 3 AST cannot parse at all,
# so no check here can inspect them. None is registered with any gate,
# none is on the J100/J50 path, and Tier 3 explicitly scopes them out.
# They are named rather than skipped silently: a *new* unparseable file
# has to fail the check below, not vanish from it. A legacy file that
# is later fixed simply starts being checked, which is why the
# assertion is a subset test rather than an equality.
_UNPARSEABLE_LEGACY_MODULES = frozenset(
    {
        "python/PlotResiduals.py",
        "python/PlotToyLimitsDistribution.py",
        "python/PreFitWS.py",
        "python/createCoverageGraph.py",
        "python/createToleranceGraph.py",
        "python/getChi2Distribution.py",
        "python/plotChi2Ndof.py",
        "python/plotChi2Ndof2D.py",
        "python/plotFalseExclusion.py",
        "python/plotFalseExclusionCandles.py",
        "python/plotLimits.py",
        "python/rebin.py",
        "python/signal_injection.py",
        "python/simple_analysis.py",
        "scripts/run_anaFit_zprime.py",
        "scripts/run_stitch_swiftResults.py",
        "scripts/run_swiftFit.py",
        "scripts/stitch_swiftResults.py",
    }
)


def test_files_loaded_by_the_scientific_gates_are_importable_on_python_39() -> None:
    """The scientific gates run under the LCG runtime's Python 3.9.12.

    A `str | None` in a *function signature* is evaluated when the `def`
    executes, so on 3.9 it raises `TypeError: unsupported operand
    type(s) for |` and collection dies before a single test runs. The
    development venv is 3.12, so nothing local notices.

    This is exactly how CI broke: `tests/test_repo_utils.py` gained
    three such signatures while being the only one of the ten
    scientific test files without `from __future__ import annotations`,
    and the failure surfaced two steps into the hosted workflow rather
    than in any local gate.

    Deliberately narrow: it checks this one incompatibility, not 3.9
    compatibility in general. Syntax that 3.9 cannot even parse (a
    `match` statement, say) is accepted by the 3.12 parser used here and
    would not be caught - only running the files under 3.9 proves that,
    which the lightweight gate cannot do without CVMFS.
    """
    repo_root = Path(__file__).resolve().parents[1]
    tests_dir = repo_root / "tests"

    # Every file with a dependency-marked test is run under the
    # scientific runtime, so this set maintains itself as tests are
    # added. The registered source modules are imported by those tests
    # and by the production scripts that run under the same interpreter.
    scientific_files = [
        tests_dir / name
        for name in _tests_dir_files_marked_requires_analysis_dependencies(tests_dir)
    ]
    assert scientific_files, "found no requires_analysis_dependencies test files at all"

    # Every Python source in the repository, not only the modules
    # registered with the lightweight gate. Registration is by hand, so
    # a new module on the hot path would otherwise escape this check
    # until someone remembered to add it - the same "nothing runs it"
    # gap that `test_every_test_file_is_registered_with_a_gate()`
    # closes for test files. Measured before widening: there are no
    # offenders among the parseable files, so this costs nothing today.
    scientific_files += sorted(repo_root.glob("python/*.py"))
    scientific_files += sorted(repo_root.glob("scripts/*.py"))

    offenders: dict[str, list[tuple[int, str]]] = {}
    unparseable: set[str] = set()
    for path in scientific_files:
        name = str(path.relative_to(repo_root))
        with warnings.catch_warnings():
            # Parsing the legacy modules warns about invalid escape
            # sequences: SyntaxWarning on 3.12, DeprecationWarning on
            # the LCG 3.9.12, so both are silenced.
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            try:
                unions = _evaluated_pep604_unions(path)
            except SyntaxError:
                unparseable.add(name)
                continue
        if unions and not _defers_annotation_evaluation(path):
            offenders[name] = unions

    unexpected = sorted(unparseable - _UNPARSEABLE_LEGACY_MODULES)
    assert not unexpected, (
        "these files cannot be parsed, so nothing here can check them for the 3.9 "
        "incompatibility - fix them, or add them to _UNPARSEABLE_LEGACY_MODULES with "
        f"a reason: {unexpected}"
    )
    assert not offenders, (
        "these files run under the LCG Python 3.9.12 and evaluate an `X | Y` "
        "annotation at import time, which raises TypeError there - add "
        "`from __future__ import annotations` or use typing.Optional: "
        f"{offenders}"
    )


def test_marked_tests_are_found_whatever_decorators_surround_them(tmp_path: Path) -> None:
    """Marker detection must not depend on decorator layout.

    The first three shapes always worked; the last three were dropped
    by the line-based scanner this replaced, each confirmed against a
    synthetic file. The `@mock.patch` case was then confirmed
    end-to-end: added to
    `tests/test_analysis_workflows_integration.py`, it left both
    gate-coverage tests passing under the old scanner - a silent
    all-clear for a test that no gate would ever run - and fails them
    under this one.
    """
    shapes = {
        "bare": "@pytest.mark.requires_analysis_dependencies\ndef test_x():\n    pass\n",
        "called": "@pytest.mark.requires_analysis_dependencies()\ndef test_x():\n    pass\n",
        "stacked_marks": (
            "@pytest.mark.requires_analysis_dependencies\n"
            "@pytest.mark.requires_root\ndef test_x():\n    pass\n"
        ),
        "other_decorator_between": (
            "@pytest.mark.requires_analysis_dependencies\n"
            '@mock.patch("python.run_fit.something")\ndef test_x(mocked):\n    pass\n'
        ),
        "async_def": (
            "@pytest.mark.requires_analysis_dependencies\nasync def test_x():\n    pass\n"
        ),
        "multiline_decorator_below": (
            "@pytest.mark.requires_analysis_dependencies\n"
            '@pytest.mark.parametrize(\n    "value", [1, 2]\n)\n'
            "def test_x(value):\n    pass\n"
        ),
        "marker_below_a_multiline_decorator": (
            '@pytest.mark.parametrize(\n    "value", [1, 2]\n)\n'
            "@pytest.mark.requires_analysis_dependencies\ndef test_x(value):\n    pass\n"
        ),
    }
    for name, source in shapes.items():
        path = tmp_path / f"test_{name}.py"
        path.write_text(f"import pytest\nfrom unittest import mock\n\n\n{source}", encoding="utf-8")
        assert _dependency_marked_test_names(path) == ["test_x"], f"{name} was not detected"

    # A different marker, or none, must not be reported.
    for name, source in {
        "other_marker": "@pytest.mark.requires_root\ndef test_x():\n    pass\n",
        "unmarked": "def test_x():\n    pass\n",
        "marker_named_in_a_string": (
            'DOC = "requires_analysis_dependencies"\ndef test_x():\n    pass\n'
        ),
    }.items():
        path = tmp_path / f"test_{name}.py"
        path.write_text(f"import pytest\n\n\n{source}", encoding="utf-8")
        assert _dependency_marked_test_names(path) == [], f"{name} was wrongly detected"


def test_a_second_filter_cannot_quietly_deselect_a_mapped_test() -> None:
    """The same rule, driven by the real map and the real markers.

    `-m` and `-k` are independent filters combined with AND, so proving
    that one selects a test says nothing about whether the other vetoes
    it. Both attacks below carry exactly the selector the map demands
    and still run nothing; both passed the coverage checks until
    `_invocation_runs_test()` judged both options. Confirmed against
    `scripts/run_all_gates.sh` and
    `.github/workflows/scientific-analysis.yml`.

    Where the test above exercises the expression evaluator directly,
    this one goes through the map and the markers read from the
    integration file, so a change to either is exercised here too.
    """
    repo_root = Path(__file__).resolve().parents[1]
    marked = _dependency_marked_tests(repo_root / "tests" / _INTEGRATION_TEST_FILE)
    readiness = "test_authoritative_setup_provides_scientific_runtime"
    scientific = "test_authoritative_j100_j50_workflows_match_frozen_reference"
    assert _INTEGRATION_TEST_DESIGNATED_OPTIONS[readiness] == "-k"
    assert _INTEGRATION_TEST_DESIGNATED_OPTIONS[scientific] == "-m"

    def runs(line: str, test_name: str) -> bool:
        return _invocation_runs_test(
            line,
            _INTEGRATION_TEST_FILE,
            test_name,
            marked[test_name],
            _INTEGRATION_TEST_DESIGNATED_OPTIONS[test_name],
        )

    base = f"python -m pytest tests/{_INTEGRATION_TEST_FILE}"
    readiness_line = f"{base} -k authoritative_setup_provides_scientific_runtime -v"
    scientific_line = f'{base} -m "integration and requires_root" -v'

    # The real invocations, which must keep passing.
    assert runs(readiness_line, readiness)
    assert runs(scientific_line, scientific)

    # A second filter that deselects the test, beside a correct one.
    assert not runs(
        f"{base} -k authoritative_setup_provides_scientific_runtime "
        '-m "not requires_analysis_dependencies" -v',
        readiness,
    )
    assert not runs(
        f'{base} -m "integration and requires_root" -k "not {scientific}" -v',
        scientific,
    )

    # An unsatisfiable extra term on either option, which contains the
    # expected text and selects nothing.
    assert not runs(
        f'{base} -k "authoritative_setup_provides_scientific_runtime and nonexistent" -v',
        readiness,
    )
    assert not runs(
        f'{base} -m "integration and requires_root and nonexistent_marker" -v',
        scientific,
    )

    # A second filter that keeps the test is fine, and so is none at all.
    assert runs(
        f"{base} -k authoritative_setup_provides_scientific_runtime "
        '-m "requires_analysis_dependencies" -v',
        readiness,
    )
    assert runs(f'{scientific_line[:-3]} -k "{scientific}" -v', scientific)

    # The designated option must be there: selecting the test by marker
    # is not the readiness gate's contract, and vice versa.
    assert not runs(f'{base} -m "requires_analysis_dependencies" -v', readiness)
    assert not runs(f"{base} -k {scientific} -v", scientific)


def test_gate_coverage_rejects_a_disabled_or_narrowed_gate() -> None:
    """Two sabotages of the real gate script that the coverage checker
    used to accept, both measured before this test existed.

    - The whole scientific gate wrapped in a multiline
      `if false; then ... fi`. Valid shell, gate never runs, every
      pytest command still present - and both gate-coverage tests
      passed. The pre-commit hook's own check had rejected this since
      it was found there; these two had never applied it.
    - A single `-k <one test name>` added to the plotting gate. It took
      that gate from 48 dependency-marked tests to 1, while every
      filename was still named and the marker filter still kept the
      marker, and both tests passed.

    Both are applied to the real script rather than a synthetic one, so
    this keeps testing the shipping gate. Each edit asserts its own
    anchor matched, so a restructured script fails loudly here instead
    of quietly testing nothing.
    """
    repo_root = Path(__file__).resolve().parents[1]
    script = (repo_root / "scripts" / "run_all_gates.sh").read_text(encoding="utf-8")
    sentinel = "[run-all-gates]"

    # Control: the real script must pass, or neither sabotage below
    # proves anything.
    _assert_covers_every_dependency_marked_test(
        script, "scripts/run_all_gates.sh", non_pytest_sentinel=sentinel
    )

    gate_4 = '    run_gate "scientific gate (J100/J50 authoritative workflows)"'
    gate_5 = '    echo "[run-all-gates] Gate 5/5'
    assert script.count(gate_4) == 1 and script.count(gate_5) == 1
    guarded = script.replace(gate_4, f"    if false; then\n{gate_4}", 1).replace(
        gate_5, f"    fi\n{gate_5}", 1
    )
    with pytest.raises(AssertionError, match="if false"):
        _assert_covers_every_dependency_marked_test(
            guarded, "a guarded gate script", non_pytest_sentinel=sentinel
        )

    one_test = "test_fit_raises_indexerror_for_npars_above_seven_with_default_ranges"
    plotting_filter = (
        "          tests/test_pre_fit.py \\\n" '          -m "requires_analysis_dependencies" -v'
    )
    assert script.count(plotting_filter) == 1
    narrowed = script.replace(
        plotting_filter,
        plotting_filter.replace(" -v", f' \\\n          -k "{one_test}" -v'),
        1,
    )
    with pytest.raises(AssertionError, match="does not actually run these"):
        _assert_covers_every_dependency_marked_test(
            narrowed, "a narrowed gate script", non_pytest_sentinel=sentinel
        )

    # The same gate emptied by the two vetoes that are not expression
    # filters at all. Both were measured against real pytest: the
    # --deselect drops one marked test, --collect-only runs none of
    # them, and both leave pytest exiting 0.
    for veto in (
        f"--deselect tests/test_pre_fit.py::{one_test}",
        "--deselect tests/test_pre_fit.py",
        "--collect-only",
    ):
        vetoed = script.replace(plotting_filter, plotting_filter.replace(" -v", f" {veto} -v"), 1)
        assert vetoed != script
        with pytest.raises(AssertionError, match="does not actually run these"):
            _assert_covers_every_dependency_marked_test(
                vetoed, f"a gate script with {veto}", non_pytest_sentinel=sentinel
            )

    # The gate narrowed by naming a node id instead of the file. The
    # file's name is still right there, which is how the coverage
    # checks pick their lines, so this one is invisible to a filename
    # search by construction.
    node_id = script.replace(
        "          tests/test_pre_fit.py \\\n",
        f"          tests/test_pre_fit.py::{one_test} \\\n",
        1,
    )
    assert node_id != script
    with pytest.raises(AssertionError, match="does not actually run these"):
        _assert_covers_every_dependency_marked_test(
            node_id, "a gate script naming one node id", non_pytest_sentinel=sentinel
        )


def test_a_command_inside_an_uncalled_function_is_not_a_command_that_runs() -> None:
    """A gate hidden in a shell function nothing calls.

    Valid shell, runs nothing, and `failures` stays at zero so the
    script still reports "All gates passed". Confirmed against the real
    `scripts/run_all_gates.sh`: wrapping the whole plotting gate in
    `never_called() { ... }` left both coverage tests passing.

    Synthetic here on purpose, so the rule is pinned independently of
    what the gate script happens to contain.
    """
    hidden = """
        never_called() {
            python -m pytest tests/test_pre_fit.py -m "requires_analysis_dependencies" -v
        }
    """
    assert _pytest_command_lines(hidden) == ""

    called_from_top_level = """
        run_gate() {
            "$@"
        }
        run_gate "a description" python -m pytest tests/test_pre_fit.py -m "marker" -v
    """
    kept = _pytest_command_lines(called_from_top_level)
    assert "tests/test_pre_fit.py" in kept, kept

    # Balanced braces in ordinary lines do not confuse the depth count.
    balanced = """
        echo "${HOME}"
        python -m pytest tests/test_pre_fit.py -m "marker" -v
    """
    assert "tests/test_pre_fit.py" in _pytest_command_lines(balanced)

    # A function that ends before the real gate does not swallow it.
    after_a_function = """
        helper() {
            echo hello
        }
        python -m pytest tests/test_pre_fit.py -m "marker" -v
    """
    assert "tests/test_pre_fit.py" in _pytest_command_lines(after_a_function)

    # Every other way bash lets a function be written. The rule above
    # first recognised only `name() {`, so each of these hid the same
    # gate command in plain sight: measured before the fix, the keyword
    # form, a hyphenated name, a parenthesis body and an unbalanced
    # brace in the body were all counted as coverage. Each one was run
    # under `bash -n` and then executed first, to confirm it really is
    # valid shell whose body never runs.
    hidden_forms = {
        "function keyword, no parentheses": """
            function never_called {
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
        "function keyword with parentheses": """
            function never_called() {
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
        "hyphenated function name": """
            never-called() {
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
        "parenthesis body": """
            never_called() (
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            )
        """,
        "opening brace on the next line": """
            never_called()
            {
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
        "whole body on the definition line": """
            never_called() { python -m pytest tests/test_pre_fit.py -m "marker" -v; }
        """,
        "quoted brace inside the body": """
            never_called() {
                echo "}}"
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
        "unquoted brace word inside the body": """
            never_called() {
                echo }}
                python -m pytest tests/test_pre_fit.py -m "marker" -v
            }
        """,
    }
    for description, source in hidden_forms.items():
        assert _pytest_command_lines(source) == "", description

    # ...and the same shapes at top level still read as real commands,
    # so the wider rule cannot silently hide a gate that does run.
    visible_forms = {
        "brace word in a string": """
            echo "}}"
            python -m pytest tests/test_pre_fit.py -m "marker" -v
        """,
        "after a parenthesis-bodied function": """
            helper() (
                echo hello
            )
            python -m pytest tests/test_pre_fit.py -m "marker" -v
        """,
        "after a keyword-form function": """
            function helper {
                echo hello
            }
            python -m pytest tests/test_pre_fit.py -m "marker" -v
        """,
        "after a one-line function": """
            helper() { echo hello; }
            python -m pytest tests/test_pre_fit.py -m "marker" -v
        """,
        "command substitution in the command": """
            python -m pytest "$(dirname tests/x)/test_pre_fit.py" -m "marker" -v
        """,
    }
    for description, source in visible_forms.items():
        assert "test_pre_fit.py" in _pytest_command_lines(source), description


def test_a_command_printed_by_a_heredoc_is_not_a_command_that_runs() -> None:
    """A gate command inside a heredoc body.

    A heredoc body is data: `cat <<EOF` followed by the plotting gate's
    own pytest command prints that command and runs nothing, so the
    script reports no failure. Measured - `bash` on a heredoc holding
    `echo BODY_RAN` prints the text rather than running it.

    `_executable_command_lines()` has dropped heredoc bodies since the
    installer checks were written, but `_pytest_command_lines()` never
    did, so all six spellings below satisfied the gate-coverage
    assertions while the installer assertions caught them. One rule
    with two callers now, for the same reason the two pytest filter
    checks were merged: two copies drifted a review round apart.
    """
    command = 'python -m pytest tests/test_pre_fit.py -m "marker" -v'
    printed = {
        "plain": "cat <<EOF\n%s\nEOF\n" % command,
        "quoted terminator": "cat <<'EOF'\n%s\nEOF\n" % command,
        "double-quoted terminator": 'cat <<"EOF"\n%s\nEOF\n' % command,
        "tab-stripping <<-": "cat <<-EOF\n\t%s\n\tEOF\n" % command,
        "redirected into a file": "cat > usage.txt <<EOF\n%s\nEOF\n" % command,
        "inside a workflow run block": (
            "    - name: a step\n      run: |\n        cat <<EOF\n"
            "        %s\n        EOF\n" % command
        ),
    }
    for description, source in printed.items():
        assert _pytest_command_lines(source) == "", description
        assert "test_pre_fit.py" not in _executable_command_lines(source), description

    # The heredoc ends where its terminator says it does, so a real
    # gate command after one is still read as a command.
    after = "cat <<EOF\nusage text\nEOF\n%s\n" % command
    assert "test_pre_fit.py" in _pytest_command_lines(after)

    # A terminator that never arrives swallows the rest of the file,
    # which is what the shell does too.
    unterminated = "cat <<EOF\nusage text\n%s\n" % command
    assert _pytest_command_lines(unterminated) == ""


def test_every_way_pytest_can_drop_a_test_is_judged() -> None:
    """`-k` and `-m` are not the only ways to remove a test.

    The previous round fixed those two and stopped there, on the stated
    premise that pytest combines them with AND. That premise was
    incomplete. Each case below was measured against real pytest before
    being pinned here:

    - `--deselect <node id>` took the plotting gate from 18
      dependency-marked tests to 17, and `--deselect <file>` took it to
      16, with both expression filters still perfectly correct;
    - `--collect-only` (and its `--co` alias) collects everything and
      runs none of it, exiting 0 - the only veto that leaves no trace
      in the gate's own result;
    - a short option this reader cannot interpret - the value glued on
      (`-knothing`) or the option bundled behind another flag
      (`-vk nothing`) - counts as unproven rather than absent. Absent
      means "filters nothing", which would be exactly the wrong
      answer. `-vk <one test name>` took the plotting gate from 16
      dependency-marked tests to 1 at exit code 0;
    - a repeated `-m` or `-k`, where argparse stores and so the *last*
      one is the filter pytest applies. Reading the first passed the
      coverage checks while the gate silently dropped a marked test.
    """
    test_file = "test_pre_fit.py"
    test_name = "test_fit_returns_expected_shape_and_is_deterministic_for_real_fixture"
    markers = {"requires_analysis_dependencies", "requires_root"}
    base = f'python -m pytest tests/{test_file} -m "requires_analysis_dependencies"'

    def keeps(extra: str = "") -> bool:
        return _filters_keep_test(f"{base} {extra}".strip(), test_file, test_name, markers)

    assert keeps()
    assert keeps("-v")

    # --deselect, in every spelling that reaches this test
    assert not keeps(f"--deselect tests/{test_file}::{test_name}")
    assert not keeps(f"--deselect=tests/{test_file}::{test_name}")
    assert not keeps(f"--deselect tests/{test_file}")
    assert not keeps("--deselect tests/")
    # a repeated option: the second one is the one that bites, so
    # reading only the first value is not enough
    assert not keeps(f"--deselect tests/other.py --deselect tests/{test_file}")
    # someone else's test being deselected does not deselect this one
    assert keeps("--deselect tests/test_create_binning.py::test_other")
    assert keeps(f"--deselect tests/{test_file}::test_a_different_test")

    # collect-only, both spellings
    assert not keeps("--collect-only")
    assert not keeps("--co")
    # not to be confused with an option that merely starts the same way
    assert keeps("--color=yes")

    # A node id in place of the file: only the named test runs from it.
    # This is the positional spelling of a node selector, and it was
    # missed when the --deselect spelling was fixed - naming one node id
    # took this file from two marked tests to one and both coverage
    # tests still passed.
    node = f"python -m pytest tests/{test_file}::{test_name}"
    assert _filters_keep_test(node, test_file, test_name, markers)
    assert not _filters_keep_test(
        f"python -m pytest tests/{test_file}::a_different_test",
        test_file,
        test_name,
        markers,
    )
    # A class-qualified node id still names the test.
    assert _filters_keep_test(
        f"python -m pytest tests/{test_file}::SomeClass::{test_name}",
        test_file,
        test_name,
        markers,
    )
    # Naming the file bare alongside a node id keeps the whole file.
    assert _filters_keep_test(
        f"python -m pytest tests/{test_file}::a_different_test tests/{test_file}",
        test_file,
        test_name,
        markers,
    )
    # The file mentioned only inside an option value is not the file
    # being run - which is why option values are skipped before the
    # positional arguments are read. `--ignore` is the case that
    # isolates that skipping: the `--deselect` spelling is caught by
    # the deselect check as well, so it does not prove this on its own.
    assert not _filters_keep_test(
        f"python -m pytest tests/other.py --ignore tests/{test_file}",
        test_file,
        test_name,
        markers,
    )
    assert not _filters_keep_test(
        f"python -m pytest tests/other.py --deselect tests/{test_file}",
        test_file,
        test_name,
        markers,
    )

    # A short option this reader cannot interpret is not proof of
    # anything. Both forms were measured: `-vk <one test name>` took
    # the plotting gate from 16 marked tests to 1, at exit code 0.
    assert not keeps("-knothing")
    assert not keeps("-mnothing")
    assert not keeps("-vk nothing_matches_this")
    assert not keeps(f"-vk {test_name}")
    assert not keeps("-vm requires_root")
    # Selection-neutral flags, alone and bundled, are fine.
    assert keeps("-v")
    assert keeps("-vv")
    assert keeps("-vx")
    assert keeps("-q -s")
    # the same options written so they can be read are judged normally
    assert keeps(f"-k {test_name}")
    assert not keeps("-k nothing_matches_this")
    assert keeps("-k=" + test_name)

    # A repeated filter: argparse stores, so the LAST one is what
    # pytest applies. Reading the first passed this check while the
    # gate dropped a marked test and still exited 0.
    assert not keeps("-m nothing_matches_this")
    # a real marker that this test does not carry
    assert not keeps("-m integration")
    assert not keeps(f"-k {test_name} -k nothing_matches_this")
    # and the last one being correct is still correct
    assert keeps("-m nothing_matches_this -m requires_analysis_dependencies")

    # Disabling the plugin that collects Python tests stops collection
    # outright: `-p no:python` collects nothing.
    assert not keeps("-p no:python")
    assert not keeps("-p=no:python")
    assert not keeps("-p no:cacheprovider")


def test_the_installer_views_reject_text_that_never_runs() -> None:
    """`_installer_views()`, pinned on synthetic scripts.

    The two installer tests below read the repository's own installers,
    which are clean, so they pass whether or not the hardening works -
    the same vacuity as the workflow detectors above. These cases prove
    it independently.
    """
    real = 'run_build() {\n    cmake --build "$dir" --parallel 4\n}\nrun_build\n'
    script, commands, invocations = _installer_views(real, "a real installer")
    assert "cmake --build" in commands
    assert "run_build" in invocations

    # The command replaced by a trailing comment, then by an echo.
    for inert in (
        "run_build() {\n    true # cmake --build --parallel\n}\nrun_build\n",
        'run_build() {\n    echo "cmake --build --parallel"\n}\nrun_build\n',
    ):
        script, commands, invocations = _installer_views(inert, "an inert installer")
        assert "cmake --build" not in commands, commands
        # and it is not hiding in the comment-stripped view either
        assert "cmake --build" not in script or "echo" in script

    # A guarded body is rejected outright, for either installer.
    with pytest.raises(AssertionError, match="if false"):
        _installer_views(
            'run_build() {\n    if false; then\n    cmake --build "$dir"\n    fi\n}\n',
            "a guarded installer",
        )


def test_the_disabling_detectors_actually_detect(tmp_path: Path) -> None:
    """The detectors used by the test below, exercised on real examples.

    That test reads the repository's own files, which are clean - so it
    passes whether or not the detectors work. Neutering
    `_yaml_conditions()` left it green, which is the same vacuity these
    policy tests exist to prevent. These cases are synthetic on
    purpose, so the detectors are pinned independently of whatever the
    workflows happen to contain today.
    """
    # Every way a workflow can carry a condition, including the two
    # spellings that are not a plain literal.
    assert _yaml_conditions("      - name: a step\n        if: false\n") == ["false"]
    assert _yaml_conditions("        if: ${{ false }}\n") == ["${{ false }}"]
    assert _yaml_conditions("        if: github.event_name == 'push'\n") == [
        "github.event_name == 'push'"
    ]
    assert _yaml_conditions("    if: always()\n") == ["always()"]
    # A step with no condition, and the word appearing in text that is
    # not a condition key.
    assert _yaml_conditions("      - name: a step\n        run: echo if: false\n") == []
    assert _yaml_conditions("          # if: false\n") == []

    # The environment override, in both the shell and the YAML spelling.
    assert _PYTEST_ADDOPTS_ASSIGNMENT.search('export PYTEST_ADDOPTS="-k nothing"')
    assert _PYTEST_ADDOPTS_ASSIGNMENT.search("          PYTEST_ADDOPTS: -k nothing")
    assert not _PYTEST_ADDOPTS_ASSIGNMENT.search("python -m pytest -k something")

    # The config override, via the function the gate runner shares.
    # Every form pytest accepts, because the first version read one
    # physical line and stripped the outer quotes, so it missed the
    # array, the multiline string and an attached short-option value.
    # The array spelling was the dangerous one: with
    # `addopts = ["--collect-only"]` the full gate printed
    # "223/243 tests collected" and "All checks passed!" having
    # executed nothing.
    section = '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    assert selection_affecting_addopts(section) == []
    assert selection_affecting_addopts(section + 'addopts = "-ra --color=yes"\n') == []
    assert selection_affecting_addopts(section + 'addopts = "--strict-markers"\n') == []
    assert selection_affecting_addopts(section + 'addopts = "-p no:cacheprovider -x"\n') == []
    assert selection_affecting_addopts(section + 'addopts = "-k nothing"\n') == ["-k"]
    # the value attached to the short option, which pytest accepts
    assert selection_affecting_addopts(section + 'addopts = "-knothing"\n') == ["-k"]
    assert selection_affecting_addopts(section + "addopts = '''-ra -mfoo'''\n") == ["-m"]
    # the array form, on one line and split across lines
    assert selection_affecting_addopts(section + 'addopts = ["--collect-only"]\n') == [
        "--collect-only"
    ]
    assert selection_affecting_addopts(section + 'addopts = ["-k", "nothing"]\n') == ["-k"]
    assert selection_affecting_addopts(
        section + 'addopts = [\n  "-ra",\n  "--deselect",\n  "tests/x.py",\n]\n'
    ) == ["--deselect"]
    # the multiline string form
    assert selection_affecting_addopts(section + 'addopts = """\n-ra\n--collect-only\n"""\n') == [
        "--collect-only"
    ]
    # A prefix of a selecting option, refused deliberately even though
    # pytest is stricter than this: `--col`, `--desel` and `--ign` were
    # measured to exit 4 with "unrecognized arguments", so an
    # abbreviation is loud, not silent. Refusing it costs nothing and
    # does not depend on that staying true.
    assert selection_affecting_addopts(section + 'addopts = "--co"\n') == ["--collect-only"]
    assert selection_affecting_addopts(section + 'addopts = "--col"\n') == ["--collect-only"]
    assert selection_affecting_addopts(section + 'addopts = "--ignore-glob=tests/*"\n') == [
        "--ignore-glob"
    ]
    # A different tool's addopts is not pytest's.
    assert selection_affecting_addopts('[tool.other]\naddopts = "-k nothing"\n') == []


def test_pytest_reads_its_configuration_from_pyproject_and_nothing_else(
    tmp_path: Path,
) -> None:
    """Checking pyproject.toml only proves anything if pytest reads it.

    Measured with pytest 9.1.1: a `pytest.ini` takes precedence over
    pyproject.toml and pytest then ignores it completely, printing
    "configfile: pytest.ini (WARNING: ignoring pytest config in
    pyproject.toml!)". A `pytest.ini` that copies this repository's
    testpaths, pythonpath and markers across and adds
    `addopts = --collect-only` made the real lightweight gate print
    "224/244 tests collected" and exit 0, having executed nothing,
    while the addopts check read a perfectly clean pyproject.toml. A
    bare `pytest.ini` is caught anyway - it takes pythonpath with it,
    so collection fails loudly - but the copied one was silent.

    So the rule is which file pytest would read, not what one chosen
    file says.
    """
    assert effective_pytest_config_file(find_repo_root()) == "pyproject.toml"

    table = '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    (tmp_path / "pyproject.toml").write_text(table, encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "pyproject.toml"

    # Both spellings of the file that outranks it, including the empty
    # one: pytest honours it whether or not it configures anything.
    for name in ("pytest.ini", ".pytest.ini"):
        override = tmp_path / name
        override.write_text("", encoding="utf-8")
        assert effective_pytest_config_file(tmp_path) == name
        override.unlink()
    assert effective_pytest_config_file(tmp_path) == "pyproject.toml"

    # The two lower-precedence files, which only count when they carry
    # pytest's own section - and only when pyproject.toml does not.
    (tmp_path / "tox.ini").write_text("[flake8]\nmax-line-length = 100\n", encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "pyproject.toml"
    (tmp_path / "tox.ini").write_text("[pytest]\naddopts = -ra\n", encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "pyproject.toml"
    (tmp_path / "pyproject.toml").write_text("[tool.other]\nx = 1\n", encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "tox.ini"
    (tmp_path / "tox.ini").unlink()
    (tmp_path / "setup.cfg").write_text("[tool:pytest]\naddopts = -ra\n", encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "setup.cfg"

    # A file that cannot be parsed is not a file that can be shown to
    # be harmless, so it counts rather than being skipped.
    (tmp_path / "setup.cfg").write_text("this is not ini at all\n", encoding="utf-8")
    assert effective_pytest_config_file(tmp_path) == "setup.cfg"

    # No configuration at all is not a pass either: pyproject.toml's
    # table is where testpaths, pythonpath and the markers live.
    for name in ("pyproject.toml", "setup.cfg"):
        (tmp_path / name).unlink()
    assert effective_pytest_config_file(tmp_path) is None


def _called_function_names(function: ast.FunctionDef) -> list[str]:
    """The plain function names one function body calls, in order."""
    names = []
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.append(node.func.id)
    return names


def test_the_lightweight_gate_applies_its_own_pytest_config_refusal() -> None:
    """The refusal has to be wired in, and wired in before pytest.

    Checked because the rule and its wiring are separate things:
    deleting the `_ensure_pytest_config_runs_tests(repo_root)` line
    from `_run_fast_checks()` left the whole of this file passing, so
    every test above proved the rule works while nothing proved the
    gate uses it. Ordering matters for the same reason the refusal
    exists at all - a check applied after pytest has already reported
    a pass proves nothing about that pass.

    Read from the source with `ast`, not by searching its text: an
    `_ensure_pytest_config_runs_tests` inside a comment, a docstring or
    a string would satisfy a text search while calling nothing.
    """
    gate = find_repo_root() / "scripts" / "quality_check.py"
    module = ast.parse(gate.read_text(encoding="utf-8"))
    functions = {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}

    assert "_ensure_pytest_config_runs_tests" in functions, (
        "scripts/quality_check.py no longer defines the pytest-configuration refusal "
        "that tests/test_repo_utils.py checks the other side of"
    )

    called = _called_function_names(functions["_run_fast_checks"])
    assert "_ensure_pytest_config_runs_tests" in called, (
        "scripts/quality_check.py's _run_fast_checks() does not call "
        "_ensure_pytest_config_runs_tests(), so pytest's own configuration is never "
        "checked and addopts can empty every gate while the gate reports a pass"
    )
    assert called.index("_ensure_pytest_config_runs_tests") < called.index("run_command"), (
        "_run_fast_checks() starts pytest before checking pytest's configuration; the "
        "refusal has to come first or the run it is meant to prevent has already happened"
    )


# Test files the lightweight gate deliberately does not run, each named
# with the gate that does. The exemption has to point at a real gate
# invocation - checked below - so this cannot become a place to park a
# file nothing runs.
_TEST_FILES_RUN_BY_ANOTHER_GATE = {
    "test_analysis_workflows_integration.py": "the scientific gates in scripts/run_all_gates.sh",
}


def test_every_test_file_is_registered_with_a_gate() -> None:
    """A test file nothing runs is a test file that proves nothing.

    `scripts/quality_check.py` lists its targets by hand, so a new file
    under `tests/` is not run, linted or formatted until someone adds
    it. Nothing noticed. Confirmed by measurement: a new
    `tests/test_zz_unregistered_probe.py` whose only test was
    `assert False` left the whole lightweight gate green, and every
    policy test in this file passing.

    That is the same class as the gate-coverage checks above - a file
    that looks like it runs and does not - one level further out: those
    check that a registered file's tests are selected, this checks that
    the file reaches a gate at all.
    """
    repo_root = Path(__file__).resolve().parents[1]
    registered = {Path(target).name for target in _quality_check_test_targets(repo_root)}
    on_disk = {path.name for path in (repo_root / "tests").glob("test_*.py")}

    missing_registration = sorted(on_disk - registered - set(_TEST_FILES_RUN_BY_ANOTHER_GATE))
    assert not missing_registration, (
        "these test files are not in scripts/quality_check.py's test_targets, so the "
        "lightweight gate does not run, lint or format them, and no other gate claims "
        f"them either: {missing_registration}"
    )

    stale_registration = sorted(registered - on_disk)
    assert (
        not stale_registration
    ), f"scripts/quality_check.py registers test files that do not exist: {stale_registration}"

    # An exemption is only honest if some other gate really names the
    # file. Read from the gate script with the same positional-argument
    # reader the coverage checks use, so a filename appearing only in
    # an option value or a comment does not count.
    gate_script = (repo_root / "scripts" / "run_all_gates.sh").read_text(encoding="utf-8")
    gate_lines = _pytest_command_lines(gate_script).splitlines()
    for name, gate_description in _TEST_FILES_RUN_BY_ANOTHER_GATE.items():
        assert name in on_disk, f"{name} is exempted from registration but does not exist"
        assert any(_file_references(line, name) for line in gate_lines), (
            f"{name} is exempted from the lightweight gate on the grounds that "
            f"{gate_description} runs it, but no pytest command there names it"
        )


def test_no_gate_source_can_be_disabled_or_globally_filtered() -> None:
    """Three ways to switch off every gate at once, none of which the
    per-command coverage checks can see.

    They all leave the pytest commands themselves untouched, which is
    exactly why the checks that read those commands miss them. Each was
    found by sabotage and measured:

    - a workflow step condition (`if: false`), the YAML twin of the
      shell `if false; then ... fi` already rejected above - it left
      all three CI policy tests passing with the whole scientific gate
      step skipped;
    - `PYTEST_ADDOPTS`, which pytest applies to every invocation, so
      one line in a gate source filters every gate in it (a 5-test
      file went to 0 selected);
    - pytest's `addopts` config, which applies repository-wide -
      `-k nothing_matches_this` empties a gate even though the gate
      passes its own `-m`, because the two options are independent and
      both apply. (An `addopts` `-m` is overridden by a command-line
      `-m`, so that one spelling cannot empty these gates; the option
      is rejected anyway rather than relying on every gate continuing
      to name its own marker filter.)
    """
    repo_root = Path(__file__).resolve().parents[1]

    workflows = sorted((repo_root / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflow files found to check"
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        conditions = _yaml_conditions(text)
        assert not conditions, (
            f"{workflow.name} makes a step or job conditional ({conditions}), which can "
            "disable a gate while leaving every command in place - see _YAML_CONDITION"
        )
        assert not _PYTEST_ADDOPTS_ASSIGNMENT.search(text), (
            f"{workflow.name} mentions PYTEST_ADDOPTS, which pytest applies to every "
            "invocation and can deselect every gate in this workflow"
        )

    for source in (
        repo_root / "scripts" / "run_all_gates.sh",
        repo_root / ".githooks" / "pre-commit",
    ):
        text = source.read_text(encoding="utf-8")
        assert not _PYTEST_ADDOPTS_ASSIGNMENT.search(text), (
            f"{source.name} mentions PYTEST_ADDOPTS, which pytest applies to every "
            "invocation and can deselect every gate it runs"
        )

    # The same function `scripts/quality_check.py` applies before it
    # starts pytest - one rule, two callers. The gate has to refuse
    # first, because a test cannot catch a configuration that stops
    # tests from running: `addopts = "--collect-only"` makes this very
    # file collect and not run, so this assertion would never execute.
    offending = selection_affecting_addopts(
        (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert not offending, (
        f"pyproject.toml's pytest addopts sets {offending}, which applies to every "
        "pytest invocation in this repository and can empty every gate"
    )


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
    # Comments are stripped whole-line *and* trailing, so no assertion
    # below can be satisfied by commented-out text. The previous
    # version dropped only whole-line comments: replacing both real
    # `cmake --build` invocations with `true # cmake --build --parallel`
    # is valid shell, builds nothing, and left both of these tests
    # passing. Echo lines are kept, because several assertions here are
    # about messages this script prints; the ones that are about
    # commands it runs go through `commands` below.
    active_script, commands, invocations = _installer_views(
        installer_text, str(installer.relative_to(repo_root))
    )

    recursive = _recursive_delete(active_script)
    assert not recursive, f"this installer recursively deletes something: {recursive!r}"
    assert "git pull" not in active_script
    assert "git clone" not in active_script
    assert "setup.py install" not in active_script
    assert "pip install --upgrade" not in active_script
    assert "virtualenv " not in active_script
    assert "LCG_105" not in active_script

    assert 'scientific_setup="$repo_root/scripts/setup_buildAndFit.sh"' in active_script
    assert "--system-site-packages" in commands
    assert "--no-deps" in commands
    assert "--no-build-isolation" in commands
    assert '"$pybh_source"' in active_script

    assert 'if [[ -e "$pybh_environment" ]]; then' in active_script
    assert "existing_python_version" in active_script
    assert "platform.python_version()" in active_script
    assert "Existing pyBH_env uses Python" in active_script
    assert "; expected " in active_script
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

    assert '"$environment_python" "$find_bh_window" --help' in commands


def test_install_script_is_non_destructive() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = repo_root / "install.sh"

    assert installer.is_file()
    assert installer.stat().st_mode & 0o111

    installer_text = installer.read_text(encoding="utf-8")
    # Comments are stripped whole-line *and* trailing, so no assertion
    # below can be satisfied by commented-out text. The previous
    # version dropped only whole-line comments: replacing both real
    # `cmake --build` invocations with `true # cmake --build --parallel`
    # is valid shell, builds nothing, and left both of these tests
    # passing. Echo lines are kept, because several assertions here are
    # about messages this script prints; the ones that are about
    # commands it runs go through `commands` below.
    active_script, commands, invocations = _installer_views(
        installer_text, str(installer.relative_to(repo_root))
    )

    recursive = _recursive_delete(active_script)
    assert not recursive, f"this installer recursively deletes something: {recursive!r}"
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

    assert 'mkdir -p "$build_dir"' in commands
    assert "cmake --build" in commands
    assert "--parallel" in commands

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

    # Both modes must be *dispatched*, not merely mentioned. `--check`
    # also appears in the usage heredoc, so asserting it against the
    # whole script passed even after the dispatch arm was renamed
    # `--no-check)` - confirmed by sabotage.
    command_dispatch = invocations.split('case "$1" in', maxsplit=1)[1]
    assert "--check)" in command_dispatch
    assert "run_check" in command_dispatch
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


def _quality_check_targets(repo_root: Path, name: str) -> list[str]:
    """One of `scripts/quality_check.py`'s registered target lists."""
    source = (repo_root / "scripts" / "quality_check.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        return [
            element.value
            for element in node.value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
    raise AssertionError(f"scripts/quality_check.py no longer assigns {name}")


def _quality_check_test_targets(repo_root: Path) -> list[str]:
    """The test files `scripts/quality_check.py` actually runs."""
    return _quality_check_targets(repo_root, "test_targets")


def _quality_check_python_targets(repo_root: Path) -> list[str]:
    """The source files `scripts/quality_check.py` lints and formats."""
    return _quality_check_targets(repo_root, "python_targets")


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
