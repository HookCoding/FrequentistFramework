# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ATLAS statistical-fit framework for dijet/TLA bump-hunt analyses. It wraps three C++
sub-frameworks cloned at pinned SHAs from their public GitHub mirrors (`xmlAnaWSBuilder`,
`quickFit`, `workspaceCombiner`) plus `pyBumpHunter`
behind Python drivers that template XML workspace cards, run the fit, and extract postfit
histograms, fit parameters and p-values.

## Commands

All commands must be run **from the repository root** — `setup.sh` and
`scripts/setup_buildAndFit.sh` abort if `xmlAnaWSBuilder/` and `quickFit/` are not in `$PWD`.

```bash
setupATLAS && lsetup git    # lxplus/CVMFS environment first
. install.sh                # clone + cmake-build the sub-frameworks (one-off, ~long)
. setup.sh                  # source (do NOT execute) before any run — sets $_DIRFIT etc.
. scripts/run_anaFit_run2.sh      # Run 2 dijet TLA J100 - the working entry point
. scripts/run_anaFit_run2_J50.sh  # Run 2 dijet TLA J50
```

`scripts/run_anaFit.sh` is the Run 3 ISR TLA configuration and **cannot be run in this tree**: it
reads `data/data23_histos.root`, and `data/` does not exist here. It is kept because it is the
configuration the Run 3 work will resume from, not because it works today. The two Run 2 drivers
above are the ones with recorded baselines (`tests/repro.py`).

`install.sh` and `setup.sh` must be **sourced**; they `cd` around and export env vars.

Output defaults to `<repo>/run/` (`out_dir=${OUT_DIR:-$PWD/run}` at the top of each driver) —
every output lands under `$out_dir/run_<rangelow>_<rangehigh>_<n>Par/`. Set `OUT_DIR` to an
EOS path for HTCondor toy studies; AFS home quotas are too small for hundreds of runs.

Other drivers: `scripts/run_nloFit.sh` (NLO-template fit, uses `setup_buildCombineFit.sh`),
`scripts/run_anaFit_syst.sh`, `scripts/run_anaFitLoop.sh`, `scripts/run_swiftFit.py`.

There is no linter config or CI on this branch. `tests/repro.py` is a reproducibility-lock
harness scoped to the J50/J100 fits only (`env`/`record`/`check`/`selfcheck` subcommands, see
the README's Reproducibility section) — it is not a general test suite for the repository.

## Architecture

The fit is a template-substitution pipeline, not a library. [python/run_anaFit.py](python/run_anaFit.py)
is the orchestrator; read it first.

1. **Card templating.** `config/<analysis>/*.template` are XML files with ALL-CAPS placeholders
   (`DATAFILE`, `RANGELOW`, `NBKG`, `PAR1..PARn`, `SIGMEAN`, `MAG_*`). `run_anaFit.py` copies
   them into the run `--folder` and rewrites placeholders via `replaceinfile()` (regex `re.sub`).
   The chain is top card → category card → background card + signal card.
2. **ROOT prefit** (`--doprefit`). [python/PreFit.py](python/PreFit.py) fits the background
   function with randomized retries to get sane starting parameters and `nbkg`, which are
   substituted back into the background card. **The number of background parameters is parsed
   from the background filename** (`..._sevenPar.template` → `nPars=7`).
3. **Workspace build + fit.** `build_fit_extract()` shells out to `xmlAnaWSBuilder/build/bin/XMLReader`
   then `quickFit/build/quickFit`. Both are called with `subprocess` and only *warn* on non-zero
   exit — check the log, not the return code.
4. **Extraction.** [python/ExtractPostfitFromWS.py](python/ExtractPostfitFromWS.py) (`PostfitExtractor`)
   rebins to resolution binning, computes chi2/p-value, writes `PostFit_*.root`;
   [python/ExtractFitParameters.py](python/ExtractFitParameters.py) writes `FitParameters_*.root`.
   Output filenames are derived by string-replacing `FitResult` in `--outputfile`.
5. **BumpHunter masking loop.** If p(chi2) < `--maskthreshold`, `python/FindBHWindow.py` runs
   inside the separate `pyBumpHunter/pyBH_env` venv (activated inline in a shell string, because
   its numpy conflicts with the CVMFS one), writes `BHresults.json`, and the whole build+fit is
   repeated with `Blind="true"` / `BlindRange` injected into copies of the cards. Failure to pass
   the threshold twice returns -1.

Post-fit plotting is [python/plotPostFit.py](python/plotPostFit.py) and
[plot_postfit.cpp](plot_postfit.cpp) (`root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"`),
which pulls ATLAS style from `atlasstyle-00-04-02/`.

### Validation studies

[python/README.md](python/README.md) documents the downstream chain in detail: pseudodata
generation → spurious-signal test → signal-injection linearity → background stability → F-test,
with the toy fits fanned out over HTCondor via `submission/condor_handler.py` +
`condor_submit.sub`. Read it before touching anything under `python/` named `Inject*`,
`create*Graph*`, `SpuriousSignal`, `BackgroundStability` or `FTest`.

## Conventions and traps

- `sigwidth == -999` is the sentinel for "Z' sample" mode: it changes the signal name
  (`mR<mass>`), the POI name, and the temp card filenames.
- `.gitignore` swallows `*.txt`, `*.pdf`, `*.png` and `run/` — new docs or result lists in those
  formats need `git add -f`.
- Shell drivers are heavily commented-out configuration history (alternative `datafile`,
  `folder`, `sysfile` paths). Prefer editing the live lines over deleting the record.
- Analysis flavours live side by side under `config/` and `Input/`: `dijetTLA`, `dijetTLAnlo`,
  plus legacy `bbyy`, `ttHyy`, `high_mass_diphoton`.

## Triaging issues

Findings go in [KNOWN_ISSUES.md](KNOWN_ISSUES.md); recording one is the obligation, fixing it is
a choice. Rank them by one question: **could this let an analysis run to completion and produce a
result that is now unphysical because of a code change?** That class comes first — a fit that
fails loudly costs an afternoon, a fit that succeeds with a silently wrong number reaches a
plot, a talk or a paper. Examples in this repository: XMLReader and quickFit warn on failure and
still return 0, so a failed fit looks like a successful one; `re.sub("PAR1", …)` running before
`PAR10` would corrupt a ten-parameter card without complaining; and the comparator in
`tests/repro.py` used to treat NaN as a match, so a fit that failed into NaN could pass `check`.

Everything that *fails closed* — crashes, tracebacks, a check that stops instead of passing — is
a lower tier however ugly it looks. It cannot put a wrong number in front of anyone. Fix those
when they are cheap or when they sit on a path about to be rewritten; otherwise record them and
move on. Defensive code written for situations that never arise is its own cost.

## Planning

Before starting non-trivial work, add a plan to `plans/` (see [plans/README.md](plans/README.md)
for naming and the index) and get it approved. Trivial changes (typos, comment fixes) don't need
one.

### Implementing a plan

**Never work through an approved plan end to end without stopping.** Plans are implemented in
small, individually committable sections, with a human in the loop at every boundary. Running
straight through is not efficiency — it produces a large diff nobody reviewed, and here a silent
mistake reaches a physics number before anyone sees it.

For each section:

1. Do the smallest piece that stands on its own and could be committed by itself.
2. Stop. Explain what was done: what changed, why, what was verified and how, and anything that
   turned out differently from what the plan predicted.
3. Wait for a human to review it. Do not commit, and do not begin the next section, until they
   have replied.

A section is not finished until its documentation is written, in the same section as the code.
This is standing — it does not need to be asked for each time.

If a section turns out to be bigger than expected, split it further rather than pressing on. If
the plan turns out to be wrong mid-way, stop and say so rather than improvising around it: a
plan contradicted by reality is a finding worth surfacing, and `plans/` keeps plans as written
precisely so that stays visible.

## Branch scope

Work stays on the branch that is checked out. Do not read from, diff against, or
switch to another branch — no `git checkout`/`switch`/`worktree`, no
`git show <branch>:file`, `git log <branch>`, `git diff <branch>`, and no reading
`.git/refs/heads/<branch>` directly. If an object from elsewhere is genuinely
needed, name the commit SHA and say why.

`.claude/hooks/no-other-branches.sh` enforces this as a PreToolUse/Bash hook when
it is wired into `.claude/settings.json`.
