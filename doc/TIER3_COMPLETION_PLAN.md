# Tier 3 Completion Plan

## 0. What this document is

This document is the **authoritative execution plan** for Tier 3 —
structural refactoring of the authoritative J100/J50 analysis pipeline —
on the `tier-3-claude` branch of this repository.

It covers the **complete pipeline invoked by the launcher scripts**, from
`scripts/run_anaFit_J100.sh`/`run_anaFit_J50.sh` through to the production
of diagnostic plots: `python/run_anaFit.py` (the coordinator being split
into modules, Chunks 1–8), `plot_edm.py` (Chunk 9), `python/plotPostFit.py`
(Chunk 10), and `plot_postfit.cpp` (Chunk 11). No other file is in scope —
see Section 3.

It is written from a from-scratch analysis of this branch's own state and
was **not** written by consulting, importing, or adapting any other
branch's Tier 3 design, audit findings, module boundaries, or prose. Other
branches or forks of this repository may contain independent Tier 3
attempts with different module names or extraction choices; that is
expected and is not evidence that this plan is wrong or needs to match
them. Do not open, diff against, or otherwise consult another branch's
Tier 3 artifacts while executing this plan.

**Delivery model**: this plan is delivered as a sequence of small, focused
pull requests, each independently reviewable and mergeable to the
repository's main branch. Section 5 defines the two-part PR pattern every
chunk follows and the templates/checklists a reviewer uses to decide
whether to approve a given PR. Section 6 breaks the work into chunks and
applies that pattern to each. **Read Section 5 before opening any PR** —
it defines the review contract every chunk depends on.

If you are an LLM or engineer picking up Tier 3 work, **read this document
in full before touching any file**, then follow it exactly. It is written
to be followed mechanically, item by item, with no scope judgment calls
left open, and to be reviewable one small PR at a time.

### Document hierarchy (who wins when documents disagree)

1. **This document** — the current Tier 3 backlog, PR structure, and
   guardrails.
2. `doc/TIER1_SYSTEM.md`, `doc/TIER1_ENVIRONMENT_PROVENANCE.md`,
   `doc/TIER2_SYSTEM.md` — non-negotiable scientific, environment, and
   development-quality contracts established before Tier 3 began. Nothing
   in Tier 3 work may weaken these.
3. `doc/ACTIVITY_LOG.md` — the chronological evidence record. Authoritative
   for **what has actually happened**, in date order. Never authoritative
   for what *should* happen next — that is this document's job. Every
   merged PR appends one new entry here (Section 5's PR template doubles
   as the activity-log entry — see Section 5).
4. `Claude science raw output.md` (repository root) — informal background
   material that originally proposed the Tier 1–4 structure, including the
   description of Tier 3 as "assisted structural refactoring" using an
   IDE's extract-function and rename-symbol tooling, and Tier 1's
   "characterization ('golden-master') tests... freeze the outputs...
   assert every future run reproduces them" guidance, which is exactly the
   methodology Section 5 applies at the level of individual functions
   rather than the whole pipeline. Non-authoritative context only; do not
   cite it as justification for a scope decision.

If any instruction below conflicts with a Tier 1 or Tier 2 contract, the
Tier 1/2 contract wins and the conflict must be raised rather than
silently resolved.

---

## 1. Non-negotiable guardrails

These apply to every single change made under this plan, no exceptions.

1. **No scientific change.** Frozen references
   (`tests/references/analysis_reference.json`), tolerances, fit
   configuration, canonical inputs, histogram paths, fit ranges, dependency
   revisions, and the schema-version-2 manifest contract must not change as
   a side effect of refactoring. The Tier 1 gates (Section 7) are the proof
   that a change did not move the science — not an assertion in prose.
2. **The activity log is append-only.**
   - Every merged PR adds a **new dated, titled section** at the end of
     `doc/ACTIVITY_LOG.md`, using Section 5's PR-description content.
   - **Never** edit, reorder, shorten, or delete an existing section. If
     later work contradicts or supersedes an earlier statement, write a
     new entry that says so explicitly. The old entry stays exactly as
     written.
   - Results are **only ever added**, never removed: do not delete old
     verification output, old test counts, or old known-limitations text
     to make the log read more cleanly.
3. **Tests before code — structurally enforced by the two-PR pattern.**
   No production file targeted by a chunk may be modified until the
   characterization tests for that chunk's target function(s) have been
   (a) written against the **current, unmodified** code, (b) reviewed and
   explicitly confirmed by a human to pass and to faithfully capture real
   behavior (not just "does not raise"), and (c) merged to the main
   branch as their own PR. See Section 5, "The two-PR pattern." An
   extraction PR opened before its characterization PR is merged is out
   of process and must not be opened.
4. **Every function created or materially modified requires new, focused
   tests**, covering: its normal successful path; at least one meaningful
   invalid-input or failure path (where applicable); its return value and
   any externally visible side effect. Moving a function is not exempt —
   its existing tests move with it (Section 5's Test Relocation Rule) and
   any newly-introduced function gets new tests under guardrail 3.
5. **No broad automated cleanup.** Never run
   `python -m ruff check .`, `python -m black .`, `python -m black --check .`,
   or an equivalent whole-repository formatting pass over `.cpp` files.
   Use `python scripts/quality_check.py --mode full`, and add every new
   source and test file to its explicit `python_targets`/`test_targets`
   lists as part of the same PR that creates the file.
6. **Explicit git staging only.** No `git add .`, no `git commit -a`. Stage
   only the paths that belong to the change being made.
7. **One PR = one step of one chunk.** Never combine a characterization
   step and an extraction step in the same PR, and never combine two
   chunks' work in the same PR. A PR that grows beyond one target
   function-group's one step should be split, not merged into one large
   review.
8. **Every PR must be checked against this document** before it is opened
   for review. Section 8 gives the exact checklist. If any answer is "no,"
   the PR is not ready.
9. **Do not describe a chunk as complete in `doc/TIER3_SYSTEM.md` or in an
   activity-log entry unless the corresponding tests and gates have
   actually been run and have actually passed**, with output captured in
   the same entry.
10. **Do not consult another branch's Tier 3 work while executing this
    plan.** If you discover another branch already contains Tier 3 work,
    do not open it, diff it, or use it as a reference — finish this plan's
    chunks from this document alone, and flag the discovery to the user.
11. **Prefer relocating or reusing an existing import/function over
    writing new logic.** A module-level `import` may be moved to
    function-local scope where it reduces a new module's test dependencies
    (Section 4's import-placement table) — that is a reorganization of an
    existing statement, not new code. No chunk may add an import of
    anything not already imported somewhere in the target file today, and
    no chunk may add a runtime dependency not already present in
    `requirements-dev-lock.txt` or the existing CVMFS/LCG scientific
    environment (Python chunks), or a new external library beyond what
    `plot_postfit.cpp`/ROOT already links today (C++ chunk). This
    refactor's purpose is readability and changeability of existing code,
    not new capability.

---

## 2. Verified current state (baseline for this plan)

This baseline was directly re-confirmed by reading the actual files on
this branch (2026-09-02), at commit `5cb6a32` (`tier-3-claude`):

- `python/run_anaFit.py` is **901 lines**, a single module mixing command
  execution, BumpHunter integration, provenance collection, manifest
  writing, XML templating, fit execution, coordination, and CLI parsing
  (full function inventory in Section 4).
- `scripts/run_anaFit_J100.sh` (and the J50 equivalent), after a
  successful `run_anaFit.py` invocation and unless `ANAFIT_SKIP_PLOTS=1`,
  runs two more plotting steps in sequence:
  ```bash
  python "$repo_dir/python/plotPostFit.py" -i "${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root" -o "${folder}/postFit.pdf"
  root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"
  ```
  `python/run_anaFit.py`'s own `build_fit_extract()` (moving to `run_fit.py`
  under Chunk 6) additionally shells out to `plot_edm.py` (repository
  root) after every quickFit invocation: `execute("python plot_edm.py %s
  %s" % (logfile, edmplot))`. These three files — `plot_edm.py`,
  `python/plotPostFit.py`, `plot_postfit.cpp` — are the "production of the
  plots" this plan's scope extends to.
- `plot_edm.py` (76 lines, repository root) has **one** function,
  `plot_minuit_continuous(filename, outname)`, which parses a quickFit log
  for Minuit convergence trace lines, then builds and saves a matplotlib
  figure — two responsibilities in one function, plus a `__main__` CLI
  wrapper.
- `python/plotPostFit.py` (79 lines) has **zero functions** — the entire
  file is top-level script code (argparse → open ROOT file → style
  histograms → build a ratio plot → draw a two-pad canvas → save). This is
  the starkest case in this plan of code that needs splitting into
  functions to be readable or independently testable at all.
- `plot_postfit.cpp` (288 lines, repository root, a ROOT macro invoked via
  `root -l -q`) has **one** function, `plot_postfit(char const* in_dir,
  char const* pars_str)`, doing: file-path construction and opening;
  histogram retrieval with null checks; BumpHunter JSON parsing via an
  inline regex lambda; chi²/p-value/nbkg extraction; and a three-panel
  plotting loop with per-panel styling and label text. No existing test
  harness covers ROOT macros in this repository — `test.cpp`,
  `scripts/test2.cpp`, `scripts/test3.cpp` are ad hoc scratch/debug scripts
  referencing hardcoded EOS paths, not a reusable test pattern; Chunk 11
  introduces the first one.
- Fixture data already committed and usable for characterization,
  confirmed present under `run/fits/J100/run_481_3000_sixPar/`:
  `PostFit_anaFit_sixPar_bkgOnly.root`, `FitParameters_anaFit_sixPar_bkgOnly.root`,
  `quickFitLog_anaFit_sixPar_bkgOnly.log`, `analysis_results.json`. No
  `BHresults.json` is present for this canonical run (background-only,
  unmasked — consistent with the established Tier 1 baseline), so
  characterization of `plot_postfit.cpp`/`plotPostFit.py` against this
  fixture exercises the no-BumpHunter path; that is expected and correct,
  not a gap to fix.
- `doc/ACTIVITY_LOG.md` on this branch records complete, verified Tier 1
  and Tier 2 history ending 2026-09-01 (merge of `github-actions-analysis`
  into `tier-2-m365`) and **contains no Tier 3 entries** — Tier 3 has not
  previously been started on this branch.
- No `doc/TIER3_SYSTEM.md` exists yet; Chunk 12 creates it.
- `tests/test_run_anaFit.py` (1,399 lines, 39 test functions) already
  covers most of `run_anaFit.py`'s current functions — see Chunk-by-chunk
  Test Relocation Rule application in Section 6. `plot_edm.py`,
  `plotPostFit.py`, and `plot_postfit.cpp` have **no existing tests at
  all** — every test for them, at both the characterization and
  extraction stage, is new.
- `scripts/quality_check.py` maintains explicit `python_targets`/
  `test_targets` lists; `python/run_anaFit.py` and `plot_edm.py`/
  `python/plotPostFit.py` are currently **absent** from `python_targets`
  (not ruff/black-checked today).
- The established gates (all currently passing per the 2026-09-01
  activity-log entry):
  - `python scripts/quality_check.py --mode full`
  - `python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v`
  - `python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v`

Treat this section as ground truth for "what exists before Tier 3 starts."
If a later chunk's own re-check finds this section inaccurate, record the
correction in a new activity-log entry rather than editing this section.

---

## 3. Scope of Tier 3

### In scope

- Splitting `python/run_anaFit.py` into focused, single-responsibility
  modules (Chunks 1–8), with `run_anaFit.py` reduced to a thin coordinator
  plus CLI entry point.
- Splitting `plot_edm.py` into a parse function and a plot function
  (Chunk 9).
- Splitting `python/plotPostFit.py` from zero functions into a set of
  named functions plus a `main()` (Chunk 10).
- Splitting `plot_postfit.cpp`'s single function into smaller free
  functions with a stable public entry point (Chunk 11).
- Writing characterization tests against each target's **unmodified**
  behavior first, human-verified and merged, before any extraction
  (Section 5).
- Adding the new tests guardrail 4 requires for any newly-introduced
  function.
- Registering every new source and test file in `scripts/quality_check.py`.
- Creating `doc/TIER3_SYSTEM.md` (Chunk 12).

### Out of scope

- CLs processing, signal-analysis changes, different fit models, inputs,
  histograms, ranges, or tolerances.
- Tier 4 orchestration (Hamilton, Snakemake, or any DAG/workflow engine).
- Repository-wide Ruff/Black formatting, or any repository-wide C++
  reformatting.
- Unrelated installer, CI, or dependency changes.
- Any structural extraction of files other than the four named in Section
  0 — not `python/analysis_reference.py`, `python/repo_utils.py`,
  `python/run_injections_anaFit.py`'s own internals, nor any other script
  under `python/` (signal injection, limit-setting, toy studies, and the
  many other scripts there remain untouched — they are not part of the
  background-only J100/J50 canonical path this plan follows).
- Changing the ROOT/C++ build system, adding a new C++ test framework, or
  introducing any C++ library beyond what `plot_postfit.cpp` already links
  (ROOT itself and the repository's existing `atlasstyle-00-04-02` macros).
- Fixing pre-existing, unrelated issues noticed along the way (e.g. the six
  legacy invalid-escape-sequence `SyntaxWarning` messages) — note them in
  the activity log if seen again, do not fix them unless a chunk says to.

---

## 4. Target architecture

### 4.1 `python/run_anaFit.py` → 7 modules + coordinator

| New module | Responsibility | Functions moving from `run_anaFit.py` |
|---|---|---|
| `run_execution.py` | Generic subprocess execution and the "command succeeded and produced its required outputs" contract. No ROOT dependency. | `execute`, `execute_required` |
| `run_manifest.py` | Writing the schema-version-2 `analysis_results.json` manifest atomically. | `write_analysis_results` |
| `run_provenance.py` | Repository/path resolution, file hashing, Git revision lookup, scientific runtime collection, and assembling the full provenance payload. | `get_repository_root`, `resolve_analysis_path`, `calculate_file_sha256`, `build_file_provenance`, `get_git_revision`, `collect_scientific_runtime`, `build_analysis_provenance` |
| `run_masking.py` | BumpHunter invocation and result validation, plus a single shared masking-decision predicate. | `load_bumphunter_results`, `run_bumphunter`, and a **new** `should_mask(p_value, threshold)` helper (Chunk 4) |
| `run_templates.py` | Materializing the per-run XML templates (top/category/signal/background files), including the prefit-driven parameter-range substitution. Named for what it produces — XML *template* files, not the RooFit `.root` workspace (built later, in `run_fit.py`). | `replaceinfile`, plus the template-copy/substitute/prefit block currently inlined in `run_anaFit()` |
| `run_fit.py` | Running XMLReader + quickFit and extracting post-fit/parameter outputs for one fit invocation (masked or unmasked). | `build_fit_extract` |
| `run_cli.py` | Argument parsing and signal-name normalization for the command-line entry point. | `main`'s argparse setup and the signal-name default logic currently inlined in `main()` |

`run_anaFit.py` keeps only `run_anaFit()`, a thin `main(args)`, and the
`if __name__ == "__main__":` guard. No extracted module may import from
`run_anaFit.py`.

### 4.2 Import mechanics (non-negotiable, Python chunks)

`run_anaFit.py` is invoked in production by the launcher scripts as a
direct executable by absolute path, after `cd`-ing to the repository root.
No `PYTHONPATH` is ever set. Python auto-prepends the invoked script's
**own** directory (`python/`) to `sys.path[0]` when a `.py` file is run
this way — confirmed directly: `import python.repo_utils` only succeeds
when the repository root is separately on `sys.path` (as under pytest, via
`pyproject.toml`'s `pythonpath = ["."]`); a bare `import repo_utils` does
not, under the same conditions.

Therefore:
- Every import between the seven new `run_anaFit.py` modules, and every
  import `run_anaFit.py` makes of them, **must use the flat sibling style**
  (`from run_execution import execute`) — never `from python.run_execution
  import execute`. `plot_edm.py` (repository root) and `plotPostFit.py`
  (`python/`) are each invoked standalone (`execute("python plot_edm.py
  ...")`, `python "$repo_dir/python/plotPostFit.py" ...`), not imported by
  another module, so this constraint applies only to their own internal
  function organization, not to any cross-module import.
- Test files importing a module directly (not through `run_anaFit.py`) may
  use the dotted `from python.run_execution import ...` namespace-package
  style already established by `tests/test_repo_utils.py` — **only** for a
  module that does not do a module-level `import ROOT` (or similar).
- Per-module import placement:

  | Module | ROOT-touching? | Import placement |
  |---|---|---|
  | `run_execution.py` | No | top-level |
  | `run_manifest.py` | No | top-level |
  | `run_masking.py` | No | top-level |
  | `run_provenance.py` | Only `collect_scientific_runtime` | `import ROOT` deferred inside that one function; everything else top-level |
  | `run_templates.py` | Only the prefit branch | `from PreFit import PreFitter` deferred inside the `doprefit` handling |
  | `run_fit.py` | The whole function | `import ROOT`, `from ExtractPostfitFromWS import PostfitExtractor`, `from ExtractFitParameters import FitParameterExtractor` deferred inside `build_fit_extract`, placed immediately before the first `ROOT.TFile(...)` use |
  | `run_cli.py` | No | top-level |
  | `plot_edm.py` (Chunk 9) | No | top-level (already ROOT-free — matplotlib only) |
  | `plotPostFit.py` (Chunk 10) | Yes (whole file) | top-level (this file is already ROOT-only end to end; there is no non-ROOT subset worth isolating) |

  This is a reorganization of where existing import statements live, not a
  new dependency and not a behavior change. Payoff: most new Python test
  files need zero `ROOT`/sibling-module stubbing and can use the plain
  dotted-import style; only tests exercising `collect_scientific_runtime`,
  the `doprefit` branch, or `build_fit_extract` stub `sys.modules[...]`
  around that one call.

### 4.3 Plotting-layer decomposition (Chunks 9–11)

| File | New/renamed functions | Notes |
|---|---|---|
| `plot_edm.py` | `parse_minuit_edm_log(filename) -> (cumulative_x, edm_values, star_indices)` (**new**); `plot_minuit_edm_trace(cumulative_x, edm_values, star_indices, outname) -> None` (**new**); `plot_minuit_continuous(filename, outname)` (existing, becomes a thin orchestrator calling the two above) | Separates log parsing (pure, trivially unit-testable) from matplotlib rendering. |
| `python/plotPostFit.py` | `parse_args(argv=None) -> argparse.Namespace` (**new**); `load_postfit_histograms(input_file) -> PostfitHistograms` (**new**, a small namedtuple of `postfit`/`data`/`chi2`); `build_ratio_histogram(data, postfit) -> TH1` (**new**); `draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist) -> TCanvas` (**new**); `main(argv=None) -> None` (**new**, orchestrates the above, then `canvas.SaveAs(...)`); `if __name__ == "__main__": main()` (**new**) | Currently zero functions exist; this chunk introduces the file's first `main()`/`__main__` guard, which is itself the textbook motivating case for this refactor. |
| `plot_postfit.cpp` | `BumpHunterInfo read_bumphunter_results(std::string const& bh_log_name)` (**new** struct + free function, replaces the inline lambda + loose locals); `PostfitHistograms load_postfit_histograms(TFile*, TFile*, TFile*, TFile*)` (**new** struct + free function); `void draw_residual_panel(TCanvas*, TH1D* first, TH1D* second, bool bump_hunter, BumpHunterInfo const&, char const* pars_str, char const* out_file_name)` (**new**, the loop body parameterized so the existing loop calls it 3×); `void plot_postfit(char const* in_dir, char const* pars_str)` (**existing signature preserved exactly** — the shell launcher invokes this by name, do not rename or reorder its parameters) | First C++ decomposition; Chunk 11 also introduces the first ROOT-macro test in this repository. |

---

## 5. The PR-chunk delivery model

Every chunk in Section 6 is delivered as **two pull requests**, opened and
merged in order, never combined:

### PR A — Characterization (tests only, zero production-code changes)

Adds tests that pin down the **current, unmodified** behavior of the
chunk's target function(s) — for a file with existing functions, this
usually means calling them exactly as they exist today (in-place, not yet
extracted); for `plotPostFit.py` (no functions yet) and `plot_postfit.cpp`
(no test harness yet) it means an end-to-end characterization: run the
current script/macro against a fixture input, assert on its real,
observable output (file created, non-empty, or a specific extracted
value), exactly the "freeze the outputs... assert every future run
reproduces them" pattern already established for Tier 1.

**PR A must not touch the target production file at all** (touching a
*test* file, or a *new* test file, is the entire content of PR A). This is
what makes "tests are written and human-verified... before files are
modified" a structural property of the process, not a checklist item that
could be skipped.

**Required human-verification checkpoint before PR A is merged**: a human
reviewer (not the LLM authoring the PR) must:
1. Run the new tests locally against the target file at PR A's base commit
   (i.e. before any Tier 3 change to that file) and confirm they pass.
2. Read each new test and confirm it asserts something meaningful about a
   real input, output, or side effect of the target function(s) — not
   merely that the call "does not raise."
3. Record this explicitly as a PR review comment, using this exact form so
   it is machine-greppable in PR history:
   > `Verified: N characterization tests pass against unmodified <file> at
   > <short-sha>, and each asserts a real input/output/side-effect of
   > <function name(s)>.`

PR A may only be merged after that comment is posted. PR B (below) may
only be opened after PR A shows merged on the default branch.

**PR A description template** (this content, filled in, is also what gets
appended to `doc/ACTIVITY_LOG.md` in the same PR):

```markdown
## Chunk <N>.A — Characterization tests for <target file/function(s)>

### Objective
Pin down the current, unmodified behavior of <function(s)> in <file>
before any extraction, per doc/TIER3_COMPLETION_PLAN.md Chunk <N>.

### Target functions — inputs and outputs (as they exist today)
| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| ... | ... | ... | ... |

### Tests added
- `test_x` — exercises <input>, asserts <output/side-effect>.
- (one row per new test function)

### What this PR does NOT do
No production file is modified. <file> is unchanged byte-for-byte in this
diff — confirm with `git diff --stat` in the PR description.

### Verification performed
- `python -m pytest <new_test_file> -v` → result, all passing.
- `git diff --stat` → only the new test file(s) appear.

### Reviewer checklist (Section 8, Characterization variant)
- [ ] Base commit for these tests is named and matches the file's current state.
- [ ] Every new test asserts a real output/side-effect, not just "no exception."
- [ ] `git diff --stat` shows no production file touched.
- [ ] Tests pass locally when run by the reviewer, not only reported by the author.
- [ ] Human-verification comment (exact form above) posted before merge.
```

### PR B — Extraction

Moves the now-characterized function(s) into their target module (or, for
`plotPostFit.py`/`plot_postfit.cpp`, restructures the file in place),
relocating PR A's tests per the **Test Relocation Rule** below, and adds
any further tests guardrail 4 requires for newly-introduced functions
(e.g. `should_mask()`, `prepare_run_templates()`, `parse_args()`).

**Test Relocation Rule**: move each test from PR A's file into its final
home **verbatim except for the import statement** — do not alter fixture
setup, assertions, or expected values while moving. Delete the old copy in
the same commit that deletes the corresponding function definition from
the source file. Any test that exercises the moved function only *through*
a higher-level entry point (e.g. a coordinator-level or end-to-end test)
stays where it is — it is testing integration, not the moved unit, and
does not relocate.

**PR B description template**:

```markdown
## Chunk <N>.B — Extract <target> into <new module/function(s)>

### Objective
Move <function(s)>, characterized and human-verified in PR A (#<PR-A-number>,
merged at <sha>), into <new module/file structure>, per
doc/TIER3_COMPLETION_PLAN.md Chunk <N>.

### What changed
- `<new file>` created, containing <functions>, moved <verbatim / with the
  one documented exception: ...>.
- `<old file>` updated: <function(s)> removed, replaced with a call to
  `<new module>.<function>`.
- Tests relocated from PR A's `<test file>` to `<final test file>`
  (import path only changed; assertions unchanged — confirm with a diff).
- New tests added for newly-introduced functions: <list>.
- `scripts/quality_check.py` updated: `<new file>`/`<new test file>` added
  to `python_targets`/`test_targets`.

### Confirm: no scientific behavior changed
State explicitly, or (Chunks 4 and 5 only) describe precisely what real
control-flow changed and why it's safe, backed by the mandatory
integration-gate rerun for those two chunks.

### Verification performed
- Focused test command + result (relocated + new tests).
- `python scripts/quality_check.py --mode full` → result.
- Integration-gate rerun, if this chunk requires it (Chunks 4, 5) → result.
- `git diff --check` → result.

### Reviewer checklist (Section 8, Extraction variant)
- [ ] PR A is merged and linked; this PR's tests are the relocated ones, not newly invented.
- [ ] Diffed test files show only import-line changes for relocated tests.
- [ ] Production code actually calls the new function (grep, don't assume).
- [ ] No extracted module imports from the coordinator/original file.
- [ ] All required gates in Section 7 ran and passed, output captured.
- [ ] Activity-log entry appended (this PR body content), not a rewrite of any existing section.
```

### Why two PRs, not one

A single PR mixing "add tests" and "move code" forces a reviewer to
simultaneously judge whether the tests are trustworthy *and* whether the
move preserved behavior, using the same tests as evidence for both — which
is circular if the tests themselves were written after the code moved. The
split makes each PR small, each with one honest question a reviewer can
answer independently: PR A — "do these tests actually describe what the
code does today?"; PR B — "does the moved code still pass the tests we
already agreed describe it?"

---

## 6. Chunks

Work through these **in order**; within a chunk, PR A before PR B. Do not
start the next chunk's PR A until the current chunk's PR B is merged.

### Chunk 0 — Pre-flight baseline confirmation (single PR, no code change)

**Objective**: Prove the branch is in the fully-passing state Section 2
claims before any Tier 3 PR is opened.

**PR content**: no code change. Run every gate in Section 7 with nothing
staged; record exact pass/fail counts as a new `doc/ACTIVITY_LOG.md` entry
("Tier-3 pre-flight baseline"), opened and merged as its own tiny PR so
the baseline is itself reviewable and citable by every later chunk.

**Acceptance check**: all three gates in Section 7 exit 0. If any does
not, stop — fix or explicitly scope out the failure before Chunk 1, and
record that decision in the activity log.

---

### Chunk 1 — `run_execution.py`

**Target functions** (unmodified, in `python/run_anaFit.py` today):

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `execute(cmd)` | `cmd: str` | `int` (subprocess return code) | runs `cmd` via `subprocess.call(shell=True)`; prints `"EXECUTE: {cmd}"` |
| `execute_required(cmd, description, expected_outputs=())` | `cmd: str`, `description: str`, `expected_outputs: Sequence[str]` | `bool` | deletes any pre-existing `expected_outputs` before running; prints diagnostics on failure |

**Rationale**: no dependency on anything else in `run_anaFit.py` (no ROOT,
no provenance, no XML handling) and used by nearly every later chunk —
extracting first gives every later chunk a stable, already-tested import.

**PR A — characterization**: write/relocate-source
`test_execute_required_accepts_success_with_expected_output`,
`test_execute_required_rejects_stale_expected_output`,
`test_execute_required_rejects_nonzero_command_status`,
`test_execute_required_rejects_missing_expected_output` — these already
exist in `tests/test_run_anaFit.py`; for this chunk, PR A is "confirm they
already characterize `execute`/`execute_required`'s current behavior and
get the required human-verification comment on the *existing* tests" (no
new test file yet — the move happens in PR B). If review finds a gap
(e.g. `execute()` itself has no direct test), add it here, against the
unmodified file, before PR B.

**PR B — extraction**:
- Create `python/run_execution.py` containing `execute()` and
  `execute_required()`, moved verbatim.
- Update `run_anaFit.py` to `from run_execution import execute,
  execute_required` — flat sibling style (Section 4.2). Never `from
  python.run_execution import ...` here.
- **Blocking step, required for this PR's own acceptance check to pass**:
  `tests/test_run_anaFit.py` loads `run_anaFit.py` via
  `importlib.util.spec_from_file_location(...)` + `exec_module(...)`,
  which does **not** put `python/` on `sys.path` (no `conftest.py` exists
  under `tests/`; pytest's `pythonpath = ["."]` only adds the repository
  root). The moment `run_anaFit.py` contains a real `from run_execution
  import ...` line, `exec_module` raises `ModuleNotFoundError` unless
  fixed first. Update the module-loading helper to prepend `python/`'s own
  directory to `sys.path` before `exec_module`, e.g.
  `monkeypatch.syspath_prepend(str(module_path.parent))`, mirroring what
  the interpreter does automatically in production. Do this before adding
  the new import.
- Apply the Test Relocation Rule for the four tests above into a new
  `tests/test_run_execution.py`. `run_execution.py` never touches `ROOT`
  or any sibling module, so this file may use the plain `from
  python.run_execution import execute, execute_required` style — no
  stubbing needed.
- Register both new files in `scripts/quality_check.py`.

**Acceptance check**:
```bash
python -m pytest tests/test_run_execution.py tests/test_run_anaFit.py -v
grep -n "^def execute\b\|^def execute_required\b" python/run_anaFit.py   # must return nothing
python scripts/quality_check.py --mode full
```

---

### Chunk 2 — `run_manifest.py`

**Target function**:

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `write_analysis_results(folder, p_chi2, masked, provenance)` | `folder: str`, `p_chi2: float`, `masked: bool`, `provenance: dict` | `str` (path to the written manifest) | atomically writes `<folder>/analysis_results.json` (schema v2) via a temp file + `os.replace` |

**Rationale**: a pure "assemble payload, write atomically" function, no
dependency on fit-execution or provenance logic beyond receiving
already-computed values — a low-risk second extraction.

**PR A**: confirm the existing
`test_write_analysis_results_writes_success_manifest`,
`test_write_analysis_results_records_masked_fit`,
`test_write_analysis_results_atomically_replaces_existing_manifest`
characterize current behavior (same human-verification process as Chunk
1's PR A); add any missing case against the unmodified file first.

**PR B**:
- Create `python/run_manifest.py` containing `write_analysis_results()`,
  moved verbatim.
- Update `run_anaFit.py`'s import (flat sibling style).
- Apply the Test Relocation Rule for the three tests above into a new
  `tests/test_run_manifest.py`.
- Register both new files.

**Acceptance check**:
```bash
python -m pytest tests/test_run_manifest.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
```

---

### Chunk 3 — `run_provenance.py`

**Target functions**:

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `get_repository_root()` | none | `Path` | raises `RuntimeError` if no `.git` found |
| `resolve_analysis_path(path, repository_root=None)` | `path: str`, optional `repository_root` | `Path` | raises `FileNotFoundError` if missing |
| `calculate_file_sha256(path)` | `path` | `str` (hex digest) | reads the file in chunks |
| `build_file_provenance(path, repository_root=None)` | as above | `dict {"path", "sha256"}` | — |
| `get_git_revision(repository_path)` | `repository_path` | `str` (40-hex SHA) | runs `git rev-parse HEAD` + `git status --porcelain`; warns (does not fail) on a dirty tree |
| `collect_scientific_runtime()` | none | `dict {"python_version","python_executable","root_version"}` | requires `ROOT` importable |
| `build_analysis_provenance(datafile, datahist, topfile, categoryfile, backgroundfile, signalfile, rangelow, rangehigh, dosignal, dolimit, doprefit, maskthreshold)` | as listed | full provenance `dict` | calls all of the above |

**Rationale**: repository discovery → path resolution → hashing → Git
revision → runtime collection → payload assembly is one coherent pipeline,
consumed by the coordinator as a single call. Largest extraction by line
count, lowest risk — every function is a pure read of the filesystem, Git,
or the ROOT runtime.

**PR A**: confirm the existing tests
(`test_calculate_file_sha256_*`, `test_get_git_revision_*`,
`test_collect_scientific_runtime_*`, `test_get_repository_root_*`,
`test_resolve_analysis_path_*`, `test_build_file_provenance_*`,
`test_build_analysis_provenance_*`) characterize current behavior; add any
gap against the unmodified file first, with the required human-
verification comment.

**PR B**:
- Create `python/run_provenance.py` containing all seven functions, moved
  verbatim and preserving call order/error handling exactly, **with one
  narrow, justified exception**: `get_repository_root()` should call
  `python/repo_utils.py`'s existing `find_repo_root()` (flat import: `from
  repo_utils import find_repo_root`) for the base-path computation, then
  layer the existing `.git`-existence check and `RuntimeError` on top
  locally. Both functions compute the identical
  `Path(__file__).resolve().parents[1])` expression independently today —
  same inputs, same output, since both files live directly under
  `python/` — so this removes a real duplication while touching zero
  lines in `repo_utils.py` and preserving `get_repository_root()`'s exact
  signature, return value, and exception behavior. Do not apply this
  reuse treatment anywhere else in this chunk.
- Apply the import-placement table (Section 4.2): `collect_scientific_runtime`'s
  `import ROOT` moves inside that one function; everything else stays
  top-level and plainly importable.
- Update `run_anaFit.py`'s import to pull `build_analysis_provenance`
  (flat sibling style).
- Apply the Test Relocation Rule into a new `tests/test_run_provenance.py`.
  Because only `collect_scientific_runtime` touches `ROOT`, only its tests
  need `sys.modules["ROOT"]` stubbing; every other relocated test can
  import the module plainly (`from python.run_provenance import ...`) —
  realize this simplification, don't just permit it.
- Register both new files.

**Acceptance check**:
```bash
python -m pytest tests/test_run_provenance.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
```

---

### Chunk 4 — `run_masking.py` (extract shared masking-threshold predicate — no operator or behavior change)

**Target functions**:

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `load_bumphunter_results(results_file)` | `results_file: str` | `dict {"BlindRange","MaskMin","MaskMax"}` | raises `ValueError` on malformed input |
| `run_bumphunter(postfitfile, folder)` | `postfitfile: str`, `folder: str` | same shape as above | deletes stale `BHresults.json`; runs the BumpHunter subprocess; raises `RuntimeError` on failure |
| `should_mask(p_value, threshold)` (**new**) | `p_value: float`, `threshold: float` | `bool` | none (pure) |

**Rationale**: `run_anaFit()` decides whether to mask using `if
pval_global > maskthreshold`, and separately whether the masked refit is
accepted using `if pval_masked > maskthreshold`. Both call sites already
use the exact same `>` comparison — **there is no mismatch between them
today**; what's missing is a shared name. The same business rule ("a
p-value at or below the mask threshold requires masking/refit") is written
out twice, independently, with no single place that states it — precisely
what extract-function refactors exist for, because duplicated conditions
are exactly what silently drifts unnoticed later.

**PR A**: confirm the existing `load_bumphunter_results`/`run_bumphunter`
tests (`test_load_bumphunter_results_accepts_valid_payload`,
`test_load_bumphunter_results_rejects_malformed_json`,
`test_load_bumphunter_results_rejects_missing_keys`,
`test_load_bumphunter_results_rejects_invalid_mask_limits`,
`test_run_bumphunter_removes_stale_output_and_loads_fresh_results`,
`test_run_bumphunter_propagates_command_failure`,
`test_run_bumphunter_rejects_success_without_fresh_output`,
`test_run_bumphunter_rejects_invalid_fresh_output`) characterize current
behavior. `should_mask()` does not exist yet, so it has no
characterization step — its tests are written fresh in PR B under
guardrail 4, since there is no "original behavior" to pin down beyond the
two inline `>` comparisons already covered by the coordinator-level tests
that stay in `tests/test_run_anaFit.py` per the Test Relocation Rule's
point on integration tests.

**PR B**:
- Create `python/run_masking.py` containing `load_bumphunter_results()`
  and `run_bumphunter()`, moved verbatim.
- Add `should_mask(p_value, threshold)` returning `p_value <= threshold` —
  i.e. `True` exactly when the coordinator's existing `if pval_global >
  maskthreshold` branch would **not** be taken, matching the coordinator's
  current `>` convention precisely. Do not silently change the convention
  without also changing both coordinator call sites and documenting why.
- Replace both inline comparisons in `run_anaFit()` with calls to
  `should_mask()`, inverted as needed to preserve the exact existing
  control flow.
- Apply the Test Relocation Rule for the eight relocated tests into a new
  `tests/test_run_masking.py`.
- **New test required**: `test_should_mask_matches_coordinator_convention_at_exact_threshold`,
  asserting `should_mask(threshold, threshold)` returns the value that
  makes the coordinator take its masking branch (`should_mask(0.01, 0.01)
  is True`), plus one clearly-below and one clearly-above case.
- Register both new files.

**Acceptance check**:
```bash
grep -n "maskthreshold" python/run_anaFit.py    # both remaining comparisons must call should_mask()
python -m pytest tests/test_run_masking.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v
```
The integration-gate run is **mandatory** in this PR B (not optional):
this chunk changes a real branch condition inside the coordinator, and the
real J100/J50 rerun is the only proof the rewritten condition still
produces the unmasked accept path both canonical workflows currently take.

---

### Chunk 5 — `run_templates.py`

**Target functions**:

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `replaceinfile(f, old_new_list)` | `f: str`, `old_new_list: list[tuple[str,str]]` | `None` | rewrites `f` in place, applying each `re.sub` in order |
| `prepare_run_templates(...)` (**new**, replacing the ~150-line inline block) | `folder`, `topfile`, `categoryfile`, `backgroundfile`, `signalfile`, `signame`, `wsfile`, `sigmean`, `sigwidth`, `datafile`, `datahist`, `rangelow`, `rangehigh`, `doprefit`, `systdict` — finalize the exact set while reading the current block; record the final signature in `doc/TIER3_SYSTEM.md` (Chunk 12) | at minimum the resolved `tmptopfile`, any updated `nbkg`, and any `poi`/`signame` derived values the coordinator needs next — exact shape recorded once decided | copies/edits XML template files on disk; runs `PreFitter` when `doprefit` is set |

**Rationale**: the block inside `run_anaFit()` that copies the top/
category/signal/background XML templates, performs placeholder
substitution, and — when `doprefit` is set — parses parameter ranges and
runs `PreFitter` to seed initial values, is one coherent responsibility.
It is the single largest and most tangled block in `run_anaFit()` (~150 of
901 lines) and the primary reason the coordinator is hard to read. It
produces XML *template* files, not the RooFit `.root` workspace itself
(built later by `run_fit.py`) — hence `run_templates.py`, chosen to avoid
inviting confusion between the two.

**PR A — characterization, no unit tests exist today**: this block has
**no existing direct tests** — only indirect coverage through the full
J100/J50 integration gate. PR A therefore writes the **first** direct
tests against the current inline block, calling into `run_anaFit()`
end-to-end with controlled inputs (matching the coordinator-level testing
style already used in `tests/test_run_anaFit.py`) and asserting on the
generated XML files' contents — this is a genuine characterization step,
not a formality, since it is the first time this logic gets pinned down at
all. Minimum coverage:
- template files copied and placeholders substituted correctly for a
  representative non-prefit, non-signal case (assert on resulting file
  contents);
- the `doprefit=True` path invokes parameter-range parsing and seeds the
  background file with fitted initial values (controlled test double for
  `PreFitter`, per `doc/TIER1_SYSTEM.md`'s ROOT-facing-tools policy);
- a signal-file case with `systdict` populated correctly substitutes the
  systematic-uncertainty placeholders;
- a **regression test for a real, verified quirk** in the current code:
  the `nPars` detection is `if "three" in backgroundfile: nPars = 3` as a
  standalone `if`, followed by a **separate** `elif` chain covering
  `"four"` through `"ten"` — not one unified `if/elif` ladder. A
  background-file name matching both `"three"` and `"four"` currently
  resolves to `nPars = 4`, not `3`. This is existing behavior, confirmed
  by reading the source; PR A's test pins it down exactly as-is so PR B
  cannot accidentally "clean it up" into a single chain, which would
  silently change behavior for any filename matching two of these
  substrings.
- `replaceinfile()`'s own characterization (it has no direct test either):
  assert it applies a list of `(old, new)` regex substitutions to a file
  in place.

Human-verification checkpoint applies as in Section 5, with extra weight
here since these are first-ever tests for this logic, not a relocation.

**PR B**:
- Create `python/run_templates.py` containing `replaceinfile()` moved
  verbatim. Decompose the templating/prefit block internally into at
  least two private helpers, called from one public entry point (moving it
  intact as one 150-line function would only relocate the tangle, not fix
  it):
  - `_stage_xml_templates(...)` — the template copy and
    placeholder-substitution logic;
  - `_seed_prefit_parameters(...)` — the `doprefit` branch: regex-parsing
    `[PARn,lo,hi]` ranges, running `PreFitter`, substituting fitted seed
    values back in. **Copy the `nPars` if/elif structure exactly as-is**
    (see PR A's regression test above) — do not unify it.
- Apply the import-placement rule: `from PreFit import PreFitter` moves
  inside `_seed_prefit_parameters`'s `doprefit` handling.
- Update `run_anaFit()` to call the new public entry point.
- Move PR A's tests into `tests/test_run_templates.py` per the Test
  Relocation Rule, scoping ROOT/PreFitter stubbing only to the
  `_seed_prefit_parameters` calls (the rest of the module needs none, per
  Section 4.2).
- Register both new files.

**Acceptance check**:
```bash
python -m pytest tests/test_run_templates.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v
```
The integration-gate run is **mandatory**: this is the riskiest single
extraction in the plan (real template-generation logic, not an
already-isolated pure function), and only the real J100/J50 rerun proves
the generated XML is byte-for-byte equivalent in the ways that matter to
the fit.

---

### Chunk 6 — `run_fit.py`

**Target function**:

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `build_fit_extract(topfile, datafile, datahist, rangelow, rangehigh, wsfile, fitresultfile, poi=None, maskrange=None)` | as listed | `(pval: float, postfitfile: str, parameterfile: str)` | runs XMLReader + quickFit subprocesses; writes ROOT files; may generate a resolution-binning file; shells out to `plot_edm.py` (Chunk 9) |

**Rationale**: the second half of the coordinator (XMLReader → quickFit →
`PostfitExtractor`/`FitParameterExtractor`), already called twice
(unmasked, masked refit) with no logic difference other than arguments —
already function-shaped, just needs to move.

**PR A**: confirm the two existing failure-path tests
(`test_build_fit_extract_stops_after_xmlreader_failure`,
`test_build_fit_extract_stops_after_quickfit_failure`) characterize
current behavior. These only cover failure paths (Section 2's baseline);
PR A adds the missing successful-path characterization against the
**unmodified** function first:
- a successful unmasked call returning the expected `(pval, postfitfile,
  parameterfile)` shape, using controlled test doubles for
  `PostfitExtractor`, `FitParameterExtractor`, and the
  `ROOT.TFile`/histogram lookup used for `datafirstbin`;
- a successful masked call (`maskrange` provided), asserting the mask
  range reaches the quickFit command and the correct normalized-p-value
  source (`Run3TLA_bkgonly_rebinned` vs. `Run3TLA_rebinned`) is selected.

**PR B**:
- Create `python/run_fit.py` containing `build_fit_extract()`, moved
  verbatim. It needs **both** `execute` and `execute_required` from
  `run_execution.py` (`execute` for the `plot_edm.py` diagnostic call and
  the conditional `createBinning.py` call; `execute_required` for
  XMLReader and quickFit) — `from run_execution import execute,
  execute_required`, flat sibling style.
- Apply the import-placement rule: defer `import ROOT`, `from
  ExtractPostfitFromWS import PostfitExtractor`, `from
  ExtractFitParameters import FitParameterExtractor` inside
  `build_fit_extract` itself, immediately before the first
  `ROOT.TFile(...)` line (after both `execute_required` calls succeed).
  Confirm once relocated that the two failure-path tests need **no**
  `ROOT`/sibling-module stubbing at all (they return before reaching the
  deferred import) — if they still need stubbing, the import was placed
  too early.
- Update `run_anaFit.py`'s import (flat sibling style).
- Apply the Test Relocation Rule for the two existing tests plus PR A's
  two new ones into `tests/test_run_fit.py`.
- Register both new files.

**Acceptance check**:
```bash
python -m pytest tests/test_run_fit.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
```

---

### Chunk 7 — `run_cli.py`

**Target functions** (both new — extracted from inline logic in `main()`):

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `build_arg_parser()` | none | `argparse.ArgumentParser` | none |
| `normalize_signal_name(sigmean, sigwidth, signame)` | `sigmean`, `sigwidth`, `signame` (possibly `None`) | `str` | none (pure) |

**Rationale**: `main()`'s argument parsing and signal-name default logic
are presentation/entry-point concerns, separable from `run_anaFit()`'s
scientific orchestration. Last extraction; leaves `run_anaFit.py` as close
to a pure coordinator as this plan gets.

**PR A**: this logic has no existing dedicated test (only indirect
coverage via `test_main_propagates_analysis_status`). Characterize the
**current inline logic in `main()`** first, calling `main()`/re-deriving
its argument-parsing behavior against the unmodified file:
- default-name construction for a normal width, an integer-valued float
  width (`7.0` — assert whatever `str(7.0)` currently produces in the
  naming string is preserved, since it's easy to accidentally "clean up"
  this during extraction by switching to `%g`-style formatting that turns
  `7.0` into `7`), and the `sigwidth == -999` Zprime-naming branch;
- a representative full set of CLI flags (mirroring an actual invocation
  from `scripts/run_anaFit_J100.sh`) parses into the expected values.

**PR B**:
- Create `python/run_cli.py` containing `build_arg_parser()` (covering
  exactly the arguments `main()` currently registers) and
  `normalize_signal_name()` (the exact default-naming logic, behavior
  preserved per PR A's `7.0` regression test).
- Update `run_anaFit.py`'s `main()` to call `run_cli.build_arg_parser()`
  and `run_cli.normalize_signal_name()` instead of containing this logic
  inline, then call `run_anaFit()` exactly as before.
- Move PR A's tests into `tests/test_run_cli.py`.
- Apply the Test Relocation Rule to `test_main_propagates_analysis_status`
  only if it turns out to test parsing behavior directly — if it only
  tests status propagation through `main()` end-to-end, it stays in
  `tests/test_run_anaFit.py`.
- Register both new files.

**Acceptance check**:
```bash
python -m pytest tests/test_run_cli.py tests/test_run_anaFit.py -v
python scripts/quality_check.py --mode full
```

---

### Chunk 8 — Coordinator slimming and dependency-direction verification (single PR, verification only)

**Objective**: With Chunks 1–7 merged, confirm `run_anaFit()` now reads as
an orchestration of calls into the seven new modules, not a container for
their logic. This is a checkpoint, not a new extraction — **no new target
function exists here, so guardrail 3's two-PR/characterization-first
pattern does not apply**; there is nothing new to characterize before
modifying, only a verification pass over work already characterized and
extracted in Chunks 1–7. Deliver as a single PR.

**PR content**:
- Re-read `run_anaFit.py` top to bottom. It should contain only: imports,
  `run_anaFit()`, `main()`, and the `if __name__ == "__main__":` guard. If
  any extracted logic was copied rather than moved, remove the duplicate.
  If `run_anaFit()` still directly contains logic belonging to one of the
  seven modules, finish moving it and update that chunk's tests
  accordingly — do not leave partial extractions.
- Register `python/run_anaFit.py` itself with the Tier 2 quality gate: it
  is currently **absent** from `scripts/quality_check.py`'s
  `python_targets` (not ruff/black-checked today, even though its test
  file is checked). At ~60–100 lines it is now small enough. Add its path
  and run `python scripts/quality_check.py --mode full`, fixing any
  remaining findings in the coordinator itself.

**Acceptance check**:
```bash
wc -l python/run_anaFit.py     # record the resulting line count in the activity log
python -c "
import ast, pathlib
tree = ast.parse(pathlib.Path('python/run_anaFit.py').read_text())
names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
print(sorted(names))
"
# must print only {'run_anaFit', 'main'}
grep -rn "^from run_anaFit import\|^import run_anaFit" python/run_execution.py python/run_manifest.py python/run_provenance.py python/run_masking.py python/run_templates.py python/run_fit.py python/run_cli.py
# must return nothing
grep -n "python/run_anaFit.py" scripts/quality_check.py    # must show it present in python_targets
python -m pytest tests/ -m "not requires_analysis_dependencies and not (integration and requires_root)" -v
# total collected+passed test count must be >= Section 2's baseline plus every new test added across Chunks 1-7
python scripts/quality_check.py --mode full
python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v
```

---

### Chunk 9 — `plot_edm.py`

**Target function** (single function today, being split into two):

| Function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `plot_minuit_continuous(filename, outname)` (existing) | `filename: str` (quickFit log path), `outname: str` | `None` | reads `filename`; prints "Error: The file was not found." and `sys.exit(1)` if missing; prints "No matching data found." and returns early if the log has no Minuit trace lines; otherwise builds and saves a matplotlib figure to `outname` |

**Target decomposition**:

| New function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `parse_minuit_edm_log(filename)` (**new**) | `filename: str` | `(cumulative_x: list[int], edm_values: list[float], star_indices: list[int])` | reads `filename`; preserve the exact current missing-file behavior (decide whether it stays `sys.exit(1)` inside the parse function or is converted to raising `FileNotFoundError` with the CLI wrapper doing the `sys.exit` — record the decision and its rationale in `doc/TIER3_SYSTEM.md`) |
| `plot_minuit_edm_trace(cumulative_x, edm_values, star_indices, outname)` (**new**) | as listed | `None` | builds and saves the matplotlib figure to `outname`; preserves the "No matching data found." early-return when `cumulative_x` is empty |
| `plot_minuit_continuous(filename, outname)` (unchanged signature) | as before | `None` | becomes a thin orchestrator: parse, then plot |

**Rationale**: separates log parsing (pure — trivially unit-testable with
a small fixture log file, no matplotlib needed) from rendering (needs
matplotlib; testable only for "does it run and produce a file," which is
still worth asserting).

**PR A — characterization**: `plot_edm.py` has no existing tests. Write
tests against the current, single `plot_minuit_continuous(filename,
outname)` function, using a small fixture log file with representative
Minuit trace lines (the existing committed
`run/fits/J100/run_481_3000_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`
is a real, already-available fixture):
- a log with matching trace lines produces a non-empty output file;
- a log with no matching trace lines does not raise and does not create
  an output file (matches "No matching data found." + early return);
- a missing input file exits with status 1 (matches current
  `sys.exit(1)` behavior) — capture via `pytest.raises(SystemExit)` or
  subprocess invocation, whichever matches how the test needs to observe
  the current top-level script's behavior (the file has `if __name__ ==
  "__main__":` guard logic too — characterize that entry point directly if
  it's simplest).

**PR B**:
- Add `parse_minuit_edm_log()` and `plot_minuit_edm_trace()` to
  `plot_edm.py`, rewriting `plot_minuit_continuous()` to call both in
  sequence, preserving every current behavior PR A pinned down exactly.
- Relocate PR A's tests, updating only what the split requires (e.g.
  splitting one end-to-end assertion into a parse-level assertion plus a
  plot-level assertion where that's clearer) — do not silently drop
  coverage; if a test's assertion moves to a different function, say so
  explicitly in the PR description, don't just delete and re-add.
- **New tests required** for the two newly-introduced functions
  individually (guardrail 4): `parse_minuit_edm_log()` against the fixture
  log, asserting the exact parsed tuple contents (not just "returns
  something"); `plot_minuit_edm_trace()` given pre-parsed data, asserting
  it produces a non-empty output file.
- Register `plot_edm.py` and its new test file in
  `scripts/quality_check.py`.

**Acceptance check**:
```bash
python -m pytest tests/test_plot_edm.py -v
python scripts/quality_check.py --mode full
```
No integration-gate rerun is required for this chunk — `plot_edm.py`'s
output is a diagnostic plot, already outside the scientific-acceptance
artifact contract per the existing `ANAFIT_SKIP_PLOTS` policy recorded in
`doc/ACTIVITY_LOG.md`'s 2026-08-20 "Plotting separated from scientific
acceptance" entry.

---

### Chunk 10 — `python/plotPostFit.py`

**Current state**: zero functions — the entire 79-line file is top-level
script code. **PR A's characterization must therefore run the current
script end-to-end**, since there is nothing importable to call directly
yet.

**Target decomposition**:

| New function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `parse_args(argv=None)` (**new**) | `argv: list[str] \| None` | `argparse.Namespace` (`inputFile`, `output`) | none |
| `load_postfit_histograms(input_file)` (**new**) | `input_file: str` | a small `PostfitHistograms` namedtuple/dataclass (`postfit`, `data`, `chi2`) with styling already applied (marker/line style currently applied inline — decide whether styling stays in this function or moves to a separate `style_postfit_histograms()`; record the decision) | opens `input_file` via `ROOT.TFile.Open` |
| `build_ratio_histogram(data, postfit)` (**new**) | ROOT histograms | a styled ratio `TH1` | none beyond building the object |
| `draw_postfit_canvas(data, postfit, chi2_hist, ratio_hist)` (**new**) | as listed | a `TCanvas` (not yet saved) | builds the two-pad canvas, legend, χ²/ndof text, draws everything |
| `main(argv=None)` (**new**) | `argv` | `None` | orchestrates the above, then `canvas.SaveAs(output)` and closes the input file |
| `if __name__ == "__main__": main()` (**new**) | — | — | — |

**PR A — characterization (subprocess-level, since no functions exist
yet)**: run the current script as a subprocess against the already-
committed fixture
`run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root`,
writing to a `tmp_path` output, and assert:
- the process exits 0;
- the output PDF is created and non-empty.

Do not attempt byte-identical PDF comparison — ROOT's PDF output is not
guaranteed bit-reproducible across environments/fonts, and Tier 1 already
established (2026-08-20 activity-log entry, "Plotting separated from
scientific acceptance") that PDF artifacts are excluded from strict
scientific comparison. The meaningful, stable invariant to characterize is
"runs successfully against a real fixture and produces a real, non-empty
plot" — record this explicitly as the chosen characterization strategy so
a future reader does not expect stronger guarantees than this PR provides.

**PR B**:
- Introduce the six functions/guard in the table above, preserving every
  behavior PR A's subprocess-level test observed.
- Keep PR A's subprocess-level test (it becomes an end-to-end regression
  test of `main()`, still valuable after the split — do not delete it).
- **New tests required** (guardrail 4) for each newly-introduced function
  individually, using controlled ROOT test doubles per
  `doc/TIER1_SYSTEM.md`'s policy where full ROOT graphics aren't needed
  for the assertion (e.g. `parse_args()` needs no ROOT at all and should
  be tested with zero stubbing; `build_ratio_histogram()` can be tested
  against small real `ROOT.TH1D` fixture objects built in-test, without
  needing a full input file).
- Register `python/plotPostFit.py` and its new test file in
  `scripts/quality_check.py`.

**Acceptance check**:
```bash
python -m pytest tests/test_plot_post_fit.py -v
python scripts/quality_check.py --mode full
```

---

### Chunk 11 — `plot_postfit.cpp`

**Current state**: one function, `plot_postfit(char const* in_dir, char
const* pars_str)`, invoked by the shell launchers as `root -l -q
"plot_postfit.cpp(\"$folder\", \"$pars\")"`. **This public entry point's
name and parameter order must not change** — the launcher calls it
positionally by that exact signature.

**No existing test harness for ROOT macros exists in this repository**
(Section 2) — Chunk 11 introduces the first one, kept consistent with the
rest of this plan's tooling: a small ROOT test macro, invoked via `root -l
-b -q` from a `pytest` wrapper (`subprocess.run([...])`), so it still
reports through the same `pytest`-based gates as everything else rather
than inventing a second, separate CI mechanism.

**Target decomposition**:

| New function | Inputs | Outputs | Side effects |
|---|---|---|---|
| `BumpHunterInfo read_bumphunter_results(std::string const& bh_log_name)` (**new** struct + function) | `bh_log_name: std::string` | `BumpHunterInfo { float global_pval, significance, mask_min, mask_max; bool available; }` | reads and regex-parses the file; `available=false` (not an exception) when the file is absent, matching current `bump_hunter = false` fallback |
| `PostfitHistograms load_postfit_histograms(TFile* native, TFile* masked, TFile* native_params, TFile* masked_params)` (**new** struct + function) | four `TFile*` (any may be null) | `PostfitHistograms` struct of the ten `TH1D*` fields currently declared inline | none beyond `Get<TH1D>` calls; preserves the current "exit(1) if native histograms missing" check — decide whether that check stays in the caller or moves into this function, record the decision |
| `void draw_residual_panel(TCanvas* can, TH1D* first, TH1D* second, bool bump_hunter, BumpHunterInfo const& bh, char const* pars_str, char const* out_file_name)` (**new**) | as listed | `void` | draws one panel and calls `can->Print(out_file_name)`; the existing loop over three histogram pairs calls this once per pair instead of repeating the body inline |
| `void plot_postfit(char const* in_dir, char const* pars_str)` (unchanged signature) | as today | `void` | becomes the orchestrator: build paths, open files, call the three functions above |

**PR A — characterization**: since there's no unit-callable structure yet,
characterize the **whole macro's current output** against the already-
committed J100 fixture directory
(`run/fits/J100/run_481_3000_sixPar/`, which has no `BHresults.json`,
exercising the current no-BumpHunter fallback path):
- add a pytest wrapper (e.g. `tests/test_plot_postfit_macro.py`) that runs
  `root -l -b -q 'plot_postfit.cpp("<fixture_dir>", "six")'` via
  `subprocess.run` into a `tmp_path` copy of the fixture directory (never
  write into the tracked fixture itself), and asserts: the process exits
  0; `post_fit.pdf` is created and non-empty in the output directory.
- this test is the C++-macro equivalent of Chunk 10's subprocess-level
  characterization, for the same reason (no pre-existing function
  boundary to characterize more precisely yet, and PDF bytes are not a
  meaningful comparison target per the same Tier 1 policy cited in Chunk
  10).

**PR B**:
- Introduce the `BumpHunterInfo`/`PostfitHistograms` structs and the three
  new free functions in the table above, rewriting `plot_postfit()` to
  call them, preserving every behavior PR A's macro-level test observed
  and preserving the public entry point's exact signature.
- Keep PR A's macro-level test (becomes an end-to-end regression test,
  still valuable — do not delete it).
- **New tests required** (guardrail 4) for the newly-introduced,
  independently-testable pieces — most importantly
  `read_bumphunter_results()`, since it needs no `TCanvas`/graphics at
  all: add a second ROOT test macro (e.g.
  `tests/root_macros/test_read_bumphunter_results.cpp`, invoked the same
  `root -l -b -q` way) that calls it against a small fixture
  `BHresults.json` (write one as a new, tracked test fixture — this
  repository's existing J100 canonical run has none, since it's
  unmasked) and asserts each `BumpHunterInfo` field against known values,
  plus a missing-file case asserting `available == false`.
  `load_postfit_histograms()` is harder to test in isolation without a
  real `TFile`, so cover it via the existing macro-level end-to-end test
  rather than inventing a synthetic ROOT-file-construction fixture just
  for this chunk — record this as a deliberate, explained scope boundary
  in `doc/TIER3_SYSTEM.md` (Chunk 12), not a silent gap.
- No `scripts/quality_check.py` registration applies here (it only covers
  Python files); instead confirm `plot_postfit.cpp` still compiles/runs
  under `root -l -q` with no new external library linked, per guardrail
  11.

**Acceptance check**:
```bash
python -m pytest tests/test_plot_postfit_macro.py tests/test_read_bumphunter_results.py -v
```
(the second file is the thin Python/pytest wrapper invoking the new ROOT
test macro via `subprocess.run`, matching the wrapper pattern used for the
macro-level test)

---

### Chunk 12 — `doc/TIER3_SYSTEM.md` and final documentation (single PR)

**Objective**: once Chunks 0–11 are all merged, write `doc/TIER3_SYSTEM.md`,
modeled on the existing structure of `doc/TIER1_SYSTEM.md` and
`doc/TIER2_SYSTEM.md` (purpose/audience/status, module map, test-file map,
gate commands, scope boundaries, known limitations). It must describe only
verified behavior — every claim cites the specific test function(s) or
gate run that proves it.

**Required contents at minimum**:
- the module tables from Sections 4.1 and 4.3, updated with the actual
  final function signatures where they were decided during Chunks 5, 9,
  10, 11 (the several "record the decision" points flagged in those
  chunks must all be resolved and documented here — this is where they
  land);
- the mapping from each module/file to its test file(s), including the
  two new ROOT-macro test files from Chunk 11;
- the unchanged Tier 1/2 gate commands, plus confirmation they still cover
  every extracted module;
- a "Known Limitations" section naming anything this plan deliberately
  left out of scope (Section 3), including the explicit
  `load_postfit_histograms()` (C++) testing gap noted in Chunk 11, so a
  future reader does not mistake an intentional boundary for an oversight.

**Acceptance check**: manual review — re-read the finished document
against the actual module and test files it describes, confirming every
claim has a citation. Then:
```bash
grep -nE '[[:blank:]]+$' doc/TIER3_SYSTEM.md   # must return nothing
git diff --check
```

---

## 7. Gates to run

Use exactly these commands. Do not invent alternative invocations.

```bash
# After every PR's focused tests
python -m pytest <this chunk's test file(s)> tests/test_run_anaFit.py -v

# After every coherent commit
python scripts/quality_check.py --mode full

# Mandatory in Chunks 4, 5, and 8 specifically (any PR that touches a real
# branch condition or template-generation logic, not just moves an
# already-isolated pure function) — and always before Chunk 12
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v

# After any chunk touching dependency-facing code paths, if in doubt
python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v

# Before any PR is marked ready for review
git status -sb
git diff --check
git diff --stat
```

Record every exit code in the PR description and the resulting
activity-log entry. A PR is not ready for review if any required gate
above was skipped or failed.

---

## 8. Per-PR compliance checklist

Two variants — use whichever matches the PR being opened. Run this
against **this document** before requesting review. If any answer is
"no," the PR is not ready.

**Characterization PR (A) checklist**:
```text
1. Which chunk does this PR belong to, and is it PR A? (name it explicitly)
2. Does `git diff --stat` show ONLY new test file(s) — zero production files touched?
3. Does every new/confirmed test assert a real input/output/side-effect,
   not merely "does not raise"?
4. Were the tests run by a human reviewer locally against the unmodified
   target file, not only reported as passing by the PR's author?
5. Is the required human-verification comment (Section 5's exact form)
   posted before merge?
6. Were only the explicit, intended files staged (no `git add .`)?
7. Has a new dated section been appended to doc/ACTIVITY_LOG.md (not a
   rewrite of any existing section)?
```

**Extraction PR (B) checklist**:
```text
1. Which chunk does this PR belong to, and is it PR B? (name it explicitly)
2. Is PR A for this chunk merged, and linked in this PR's description?
3. Does the change avoid touching scientific constants, references,
   tolerances, dependency revisions, or canonical workflow arguments?
4. Is every relocated test's diff limited to its import line — assertions
   and fixture setup unchanged?
5. Is every newly-introduced function (not merely moved) covered by a new
   focused test (success path + at least one failure/invalid path, where
   applicable)?
6. Does the production code actually call the new/moved function (grep
   for it — do not assume)?
7. Were only the explicit, intended files staged (no `git add .`)?
8. Did the relevant gates in Section 7 run and pass, with output captured?
9. Does `git diff --check` pass over the full range of the change?
10. Has a new dated section been appended to doc/ACTIVITY_LOG.md?
11. Does the activity-log entry name which chunk is now resolved, and
    leave unresolved chunks explicitly listed as still open?
12. Did this PR avoid consulting or reusing any other branch's Tier 3 work?
```

---

## 9. Completion definition for this plan

Tier 3 is complete only when:

- Every chunk in Section 6 (0 through 12) has both its PRs (or single PR,
  for Chunks 0, 8, 12) merged, each with a corresponding activity-log
  entry recording passing gate output.
- `run_anaFit.py` contains only `run_anaFit()`, `main()`, and the
  `__main__` guard (Chunk 8's acceptance check).
- No extracted Python module imports from `run_anaFit.py`.
- `plot_edm.py`, `python/plotPostFit.py`, and `plot_postfit.cpp` each
  match their Section 4.3 target decomposition, with `plot_postfit.cpp`'s
  public `plot_postfit(char const*, char const*)` entry point unchanged.
- `git diff --check` passes with zero errors over the full Tier 3 change
  range.
- No untracked repository-root artifacts remain from test execution.
- `doc/TIER3_SYSTEM.md` exists and describes only verified behavior, with
  every claim backed by a named passing test or gate.
- All gates in Section 7 pass on the final commit, with exit codes
  recorded in the activity log.
- The frozen J100/J50 references, tolerances, and canonical scientific
  configuration in `tests/references/analysis_reference.json` are
  unchanged from their values at the start of this plan (Section 2).

Do not declare Tier 3 complete in any document unless every bullet above
is independently verifiable from the activity log and the repository's
merged PR history at the time the claim is made.

---

## 10. Scope boundary

Nothing in this plan authorizes CLs implementation, signal-analysis
changes, new physics models, new canonical inputs, changed fit ranges or
tolerances, Tier 4 orchestration, repository-wide style cleanup, or
decomposition of any file beyond the four named in Section 0. It also does
not authorize consulting, merging in, or reproducing any other branch's
independent Tier 3 work — this plan is meant to stand on its own. Any
proposal to cross these boundaries requires a separate plan and explicit
review.
