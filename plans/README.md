# Plans

Implementation plans written before the work they describe, kept so the reasoning behind a
change can be found later. Each file is archived **as it was written**, not edited to match
what happened afterwards — a plan is a record of intent, and quietly rewriting it to look
correct destroys the only thing it is good for.

What actually happened is in [CHANGELOG.md](../CHANGELOG.md), the work notebook. Where a plan
and the notebook disagree, the notebook is right.

## Index

| Plan | Written | Branch | Status |
|---|---|---|---|
| [Run 2 dijet TLA, 481–3000 GeV, six parameters](2026-09-15-run2-dijet-tla-481-3000-sixpar.md) | 2026-09-15 | `claude-skills` | Approved and implemented |
| [Repository-relative output directory](2026-09-15-repo-relative-output-dir.md) | 2026-09-15 | `claude-skills` | Approved and implemented |
| [Run 2 dijet TLA J50, 302–2997 GeV, six parameters](2026-09-15-run2-dijet-tla-j50.md) | 2026-09-15 | `claude-skills` | Approved, implementation in progress |
| [Lock the software versions and the J50/J100 results before refactoring](2026-09-15-reproducibility-lock.md) | 2026-09-15 | `claude-skills` | Approved and implemented |

### Run 2 dijet TLA, 481–3000 GeV, six parameters

Wiring the framework up to the Run 2 J100 mjj spectrum with the tile gap veto, added
2026-07-22 but unreferenced by anything in the repository. Covers de-hardcoding the postfit
channel name, making the chi2 rebinning configurable, and adding a Run 2 driver.

Implemented the same day. Two of its predictions were contradicted by the actual run and are
flagged at the top of the file.

### Repository-relative output directory

Every shell driver hardcodes an absolute EOS output path belonging to whoever last ran it, so
a fresh clone writes nowhere useful until that line is edited by hand. Replaces those with a
default derived from the repository location, plus an `OUT_DIR` override that the HTCondor toy
studies need because the repository sits on a nearly-full AFS volume.

Implemented the same day. Verified end to end: `scripts/run_anaFit_run2.sh` with no `OUT_DIR`
set now lands output at `run/run_481_3000_sixPar/` inside the repository.

### Run 2 dijet TLA J50, 302–2997 GeV, six parameters

The J50 mjj spectrum added in `858cf49` has no driver — nothing in the repository runs it, so
the low-mass reach the J50 stream exists to provide goes unfitted. Adds a J50 driver mirroring
the J100 one, plus the one new card it needs (the channel name), reusing every other card and
an existing binning file that already covers 171–3217 GeV.

### Lock the software versions and the J50/J100 results before refactoring

Before rewriting the code around the J50 and J100 fits, pins down the software stack (the four
sub-framework SHAs, the CVMFS LCG view, the pyBumpHunter venv) and the two fits' outputs as a
regression baseline, so later changes can be checked against known-good numbers instead of
eyeballed against the CHANGELOG. Scope is strictly those two analyses — 27 of the repository's
1570 tracked files participate in a J50 or J100 run.

Implementation started 2026-09-16 with `tests/repro.py`'s comparator engine and its `selfcheck`
subcommand, plus `doc/IMPROVEMENTS.md` and `KNOWN_ISSUES.md`. `env` followed the same day,
verifying the four sub-framework SHAs, the RooFitExtensions checkouts, the CVMFS LCG view and the
pyBumpHunter venv against the files that already declare them — 20/20 checks pass against the
current tree. `record` followed next, cutting `tests/baseline_J100.json` and `baseline_J50.json`
from the two runs already on disk, and `env` now reads whichever baseline exists and warns
(non-fatally) if the live ROOT/cmake/numpy/scipy/uproot versions drift from what is recorded
there. Building `record` also caught a latent bug in `env`'s cmake/ROOT version probe and, from
there, retracted the tenth known issue found while building `env` — it turned out to be a false
alarm from the same class of probe bug, not a real limitation (see `CHANGELOG.md`). `check` came
last: `env` plus the four input hashes first, then each driver re-run with `OUT_DIR` pointed at a
scratch directory under the already-gitignored `run/`, compared against its baseline. `check
--quick` (J100 only) and the full `check` (both analyses, including J50's BumpHunter masking path)
both pass against the baselines cut from the runs already on disk; a hand-perturbed baseline was
confirmed to produce a readable failure before being restored. §6 followed: the dead
`scripts/install_roofitext.sh` and inert `.gitmodules` are deleted, `install.sh` clones from the
sub-frameworks' public GitHub mirrors instead of the unreachable CERN GitLab URLs, and the
`README.md`/`CLAUDE.md` documentation is corrected to match. Verification closed it out: a real
background-parameter perturbation, re-fit for real rather than hand-edited, produced a readable
`check` failure and reverting it produced a clean PASS again; `run/run_481_3000_sixPar/` was
confirmed untouched throughout (file mtimes all predate this work) and the final `git status` is
clean. The harness is in place and the gaps it found are closed.

## Adding a plan

Name the file `YYYY-MM-DD-short-slug.md`, add a row to the index above and a short paragraph
saying what it is for. Links inside a plan are relative to this folder, so repository paths
need a `../` prefix.

**Only plans for the branch that is checked out belong here.** Plans live in a personal
`~/.claude/plans/` directory that spans every project and branch, so they are not
interchangeable: a plan written against another branch describes files that may not exist here,
and copying one in imports that branch's state through the back door. Archive a plan in this
folder only when it was written for this branch.
