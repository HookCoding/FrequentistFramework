# Copilot code review instructions

## What this repository is

An ATLAS statistical-fit framework for dijet/TLA bump hunts. It wraps three C++ sub-frameworks
behind Python drivers that template XML workspace cards, run a fit, and extract post-fit
histograms, fit parameters and p-values.

It is a large, old codebase carrying years of accumulated defects, some minor and some serious.
Those defects are known. They are not what this review is for.

## The scope rule — read this before anything else

**Review only what this pull request changes. Report only defects the changed lines introduce.**

The question being answered by this review is not *what is wrong with this repository?* It is
**did this change break something that worked, or add something that is wrong?**

A defect is in scope only if it would disappear by reverting the diff. If the same defect exists
in the base branch, it is out of scope — however severe, however obvious, and however close to the
changed lines it sits.

### The cut-off commit

**Anything introduced at or before commit `30b8164` is out of scope, regardless of how serious it
is.**

`30b816420be23890910326961603a232d35dd94c`, "uploaded run2 dijet tla mjj with tile gap veto",
is the last commit of the repository as it stood before this work began. Everything from the
next commit onwards is the work under review.

This is a hard boundary, not a guideline to weigh against severity. A defect that predates
`30b8164` is out of scope if it is cosmetic, and it is equally out of scope if it silently corrupts
every physics number the framework produces. Its age is the only fact that matters. If you are
unsure when a line was introduced, check with `git log -S` or `git blame`; if you cannot establish
that the change under review introduced it, do not report it.

**Out of scope, without exception:**

- Any defect introduced at or before `30b8164`, or otherwise present in the base branch. This
  includes incorrect hardcoded values (luminosities, centre-of-mass energies, paths, thresholds,
  magic indices), long-standing wrong labels, fragile parsing, missing error handling, and dead or
  unreachable code.
- A pre-existing defect that the change makes more visible, more reachable, or more frequently
  executed without altering it. If the diff points a new caller at old broken code, the old code
  is still out of scope; only the new call site is reviewable, and only for what it does wrong
  itself.
- Anything found by reading files the pull request does not touch.
- Anything in `xmlAnaWSBuilder/`, `quickFit/`, `workspaceCombiner/` or `pyBumpHunter/`. These are
  upstream projects cloned at pinned SHAs, not this repository's code.
- Improvements. A changed line that is correct but could be better is not a finding. Do not suggest
  refactors, extractions, renames, added abstractions or defensive code for situations that do not
  arise.
- Style, naming, formatting, spelling, grammar, capitalisation, docstrings and type hints,
  including on changed lines.

Reporting a pre-existing defect is not a bonus finding. It is a false positive against the question
this review exists to answer, and it costs the reviewer the attention that a real regression needs.

If the diff contains nothing that meets the bar, say so and report nothing. An empty review is a
valid and useful result.

## Ranking what is in scope

Among findings that the change does introduce, rank by one question:

**Could this let an analysis run to completion and produce a result that is now unphysical?**

What this code emits is a physics number that reaches a plot, a talk or a paper. A change that makes
the pipeline fail loudly costs an afternoon. A change that makes it succeed with a silently wrong
number reaches a publication.

**Highest — a newly wrong number, reported first.** The change lets the fit finish and return
something that is not what it claims to be: a failure the new code swallows, a fallback it takes
without announcing, a gate it evaluates on the wrong input, a substitution that corrupts a card, a
new binning or masking path that alters chi2 or BumpHunter inputs.

**High — a right number newly presented as the wrong thing.** The change plots the rejected fit
instead of the accepted one, attaches a new label to the wrong quantity, or writes a result under a
name that does not match it. The fit being correct is not a mitigation; nobody reads the fit, they
read the plot.

**High — a new documentation claim the code does not keep.** The diff adds a sentence to a README,
`CLAUDE.md`, `KNOWN_ISSUES.md` or a comment asserting a guarantee, a check or a behaviour that the
code does not implement. A false recorded claim is worse than silence, because it stops the next
person looking.

**Low — the change fails closed.** A new crash, traceback, refusal or hang. Report it, and say
plainly that it fails closed, so its severity is not mistaken for the classes above.

## Writing a finding

- Name the behaviour before the change and the behaviour after it. If you cannot say what worked at
  `30b8164` and what does not now, the finding is out of scope.
- State concretely what wrong output it produces: which input, which displayed quantity, which file.
- Say whether it fails open (finishes with a wrong result) or fails closed (stops).
- Check sibling call sites **within the diff** before writing. There are six shell drivers under
  `scripts/`, two of them near-duplicates (`run_anaFit_run2.sh`, `run_anaFit_run2_J50.sh`), and
  several Python entry points share helpers. If the change touches one and the same mistake is in
  another changed file, name both.
- If you are inferring behaviour rather than reading it — an exit code you did not check, a
  histogram bin you did not open — say so rather than asserting it.

## Conventions here that are not defects

Changed lines that follow these are correct:

- Shell drivers carry large blocks of commented-out configuration. That history is kept
  deliberately; do not suggest deleting it.
- `install.sh` and `setup.sh` must be **sourced**, not executed; they `cd` and export. Do not
  suggest execution, shebangs or `set -e` in them.
- `sigwidth == -999` is a sentinel for Z′-sample mode.
- The number of background parameters is parsed from the background card's filename
  (`..._sevenPar.template` → 7). Fragile, known, pre-existing.
- `.gitignore` deliberately swallows `*.txt`, `*.pdf`, `*.png` and `run/`.
- Defects already recorded in `KNOWN_ISSUES.md` are known and out of scope. Check there before
  reporting anything.

## What the existing checks prove

`tests/repro.py` is a reproducibility lock over the two Run 2 fits. Its `check` subcommand compares
recorded fit results, chi2 values and post-fit bin contents against a baseline — and it compares
**plot filenames only, never plot contents**. A passing check is therefore not evidence against a
regression in what a plot displays.
