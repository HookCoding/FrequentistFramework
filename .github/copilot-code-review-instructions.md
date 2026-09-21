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

### Defects already recorded in `KNOWN_ISSUES.md`

**If the defect is described anywhere in `KNOWN_ISSUES.md`, do not report it.** No judgement, no
exceptions: presence in that file is the whole test. It is the second hard boundary after the
cut-off commit, and it is checked the same way — before writing a finding, not after.

`KNOWN_ISSUES.md` is this repository's disclosure log, not a to-do list. An entry means the defect
has been found, investigated and written up, and someone has already decided what to do about it.
Every numbered entry's `###` heading ends in one of two states, and **both are out of scope**:

- **`Fixed <date>`** — repaired. The code in the diff is very likely the repair.
- **`open; recorded, not fixed`** — a deliberate decision to leave it. This repository's rule is
  that recording an issue is the obligation and fixing it is a choice, so an open entry is a closed
  decision, not an oversight. Ten of the forty entries are in this state.

**Two properties of that file will mislead you if you are not told about them.**

First, **a fixed entry keeps its original description, in the present tense, below the `Fixed`
marker.** That is deliberate policy: the record of what was wrong is not deleted when it is
repaired. Issue 43's entry still reads "Every driver sources it as a bare statement and never tests
the status" three paragraphs under **Fixed**. Read the `###` heading for status. Never infer status
from the body.

Second, the file is 1795 lines and holds both numbered entries and an **unnumbered table at the
top** carrying the same force. Search it — by filename, by symbol, by the behaviour you are about
to describe — rather than reading it front to back.

### Out of scope, without exception

- Any defect introduced at or before `30b8164`, or otherwise present in the base branch. This
  includes incorrect hardcoded values (luminosities, centre-of-mass energies, paths, thresholds,
  magic indices), long-standing wrong labels, fragile parsing, missing error handling, and dead or
  unreachable code.
- A pre-existing defect that the change makes more visible, more reachable, or more frequently
  executed without altering it. If the diff points a new caller at old broken code, the old code
  is still out of scope; only the new call site is reviewable, and only for what it does wrong
  itself.
- **Documentation that has fallen out of date.** A sentence in `README.md`, `CLAUDE.md`,
  `doc/IMPROVEMENTS.md` or a code comment that was true of the code when it was written, and was
  made stale by a later change, is out of scope however plainly wrong it now reads. This is
  trivial to repair, it is repaired in batches deliberately, and it is not what this review is
  for. The test is the moment the sentence was written, not the moment you read it: **was it true
  of the code then?** If yes, say nothing.
- **A defect the diff repairs.** If the changed lines fix something that was broken before the
  cut-off commit, that is the work succeeding. Do not report the old behaviour as a finding
  against the lines that remove it. If you cannot state what is worse after the change than
  before it, there is no finding.
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

**High — a documentation claim that was never true.** The diff adds a sentence to a README,
`CLAUDE.md`, `KNOWN_ISSUES.md` or a comment asserting a guarantee, a check or a behaviour the code
**did not have at the moment that sentence was written**. A false recorded claim is worse than
silence, because it stops the next person looking.

This is a narrow class, and it is not documentation drift. A claim that was accurate when written
and has since been overtaken by a later change is out of scope — see the bullet above. Only a
claim that was false on arrival belongs here. If you cannot show the code never behaved that way,
do not report it.

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
  another changed file, write **one finding naming both files** — not one finding per file. One
  defect in two near-duplicate drivers is one defect.
- Before writing, confirm the defect is absent from `KNOWN_ISSUES.md`, and say in the finding that
  you checked.
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
- Defects recorded in `KNOWN_ISSUES.md`. This has its own section above; it is a hard boundary,
  not a convention.

## What the existing checks prove

`tests/repro.py` is a reproducibility lock over the two Run 2 fits. Its `check` subcommand compares
recorded fit results, chi2 values and post-fit bin contents against a baseline — and it compares
**plot filenames only, never plot contents**. A passing check is therefore not evidence against a
regression in what a plot displays.
