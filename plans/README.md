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
| [Make the drivers stop when the setup guard fires](2026-09-17-driver-setup-guard.md) | 2026-09-17 | `claude-skills` | Approved and implemented |
| [Refuse a partial `--rebinfile`/`--rebinhist` pair](2026-09-17-rebin-pair-guard.md) | 2026-09-17 | `claude-skills` | Approved, implementation in progress |
| [Close the issues that can reach a physically wrong result](2026-09-17-physics-risk-issues.md) | 2026-09-17 | `claude-skills` | Approved and implemented |

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

It was then declared complete, which it was not. An audit of the implementation against this plan,
later the same day, found two of its requirements never built — `env` does not compare the two
built binaries' SHA-256 against the baseline provenance (plan §1), and the repointed `install.sh`
clone URLs were never verified to resolve (Verification step 2, which the plan says in terms not to
skip) — plus eight smaller deviations. All ten are filed as issues 12–21 in
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md), each with the fix it needs. Both plan gaps were closed the
same day: issue 12 (`env` now compares the built binaries' SHA-256 against the baseline and fails
on a mismatch), and issue 13 (the repository owner ran the pinned-commit-resolves check outside an
agent session; all three URLs confirmed). The eight smaller issues (14–21) were fixed over the
following day, the last (21, re-adding the parser unit tests the 2026-09-16 13:50 entry claimed
but never committed) on 2026-09-17. All ten issues this audit found are closed.

A second review the same day re-ran the whole harness (`selfcheck`, `env` 24/24, a full `check`
over both analyses passing in ~3.5 min) and confirmed every part of this plan is implemented. It
found six further undisclosed problems, filed as issues 22–27 in
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md): none invalidates a recorded number. The five this work
introduced are fixed — the comparator's NaN hole (22) and its crash-instead-of-report paths (26),
the egg check's hardcoded constant (25), a stale sentence in `KNOWN_ISSUES.md` itself (24) and the
"CERN GitLab" description the §6 repoint made untrue (27). Issue 23, BumpHunter plots written to
the repository root, is a fit-path write dating from 2021 and stays open and recorded; only the
documentation that overstated `check`'s isolation was corrected.

A third review filed issues 28–31 — four places where the harness crashes on a condition it should
report — and fixed none of them, deliberately: all four fail closed, so none can let an analysis
complete with a silently wrong number. That call is now a written rule in
[CLAUDE.md](../CLAUDE.md)'s *Triaging issues* section. A fourth review sorted the harness by which
problems could make `check` reach the wrong *verdict* — PASS on a moved number, or FAIL on an
unmoved one — and found six more, issues 32–37, **all six fixed**, since all six lived in
`tests/repro.py` or its documentation rather than on the fit path. Two of them had a false-pass
route: `record --force` silenced the env gate on the only re-cut route the README documents, and
`check`'s top-level comparison was a whitelist that would have ignored a section added to `record`
later. That review also closed the last provenance block that was recorded and never read back
(the software pins), and corrected two severity rankings of its own. The committed baselines were
not re-cut at any point.

### Make the drivers stop when the setup guard fires

`scripts/setup_buildAndFit.sh` refuses to run outside the repository root with `return 1`, but
`return` in a sourced script returns only from that script — so every driver carries on regardless,
creating output in the wrong directory and entering the fit chain with no environment. It fails
closed, which on this repository's triage rule would mean recording it rather than fixing it; it is
fixed because `CHANGELOG.md` and `README.md` both claim the run aborts, and that claim is the
stated justification for the repository-relative `out_dir`. Raised by a GitHub Copilot review
comment, filed as `KNOWN_ISSUES.md` issue 43.

Implemented the same day, in its single section. Its one deliberate omission — the four
`setup_buildCombineFit.sh` call sites, which source a file that does not exist and cannot be
verified against a working fit — stands as written.

### Refuse a partial `--rebinfile`/`--rebinhist` pair

`run_anaFit.py` treats "one of the pair supplied" as identical to "neither supplied" and silently
falls back to a binning that stops at 1000 GeV, while both Run 2 drivers fit to 3000 and 2997. The
rebinned chi2, the p-value that `--maskthreshold` gates on, and the BumpHunter window all move with
it. Unlike issues 44 and 45 this one can change a fitted number, and whether it fails loudly depends
on which machine it runs on. Raised by a GitHub Copilot review comment, filed as `KNOWN_ISSUES.md`
issue 46.

### Close the issues that can reach a physically wrong result

The four open findings that can lead to a physically wrong result or a wrong conclusion, rather than
a crash or a mislabelled plot: no fit status or covariance-quality check at all (issue 40, where
every recorded fit carries a forced covariance and the *errors* feed the downstream studies), a
failed workspace build or fit that is only warned about (the unnumbered table entry), `postFit.pdf`
showing the rejected fit where masking was what got accepted (issue 48), and a p(chi2) gate whose
defining histogram was never settled (issue 39). Scope agreed with the repository owner; issue 44 is
excluded as unfixable from inside this repository, and the fail-closed harness issues as the lowest
tier. §4 is blocked on a statistics decision only the owner can make.

All four sections implemented 2026-09-17/18. §3 was implemented twice: the first version emitted a
second plot file, which would have forced a J50 baseline re-cut for a change that moves no number,
and was replaced on the owner's ruling that the record should only change when the physics does. §4
was unblocked by the owner choosing `<channel>_bkgonly_rebinned` for both branches. No baseline was
re-cut at any point; `tests/repro.py check` passes on both analyses after every section.

## Adding a plan

Name the file `YYYY-MM-DD-short-slug.md`, add a row to the index above and a short paragraph
saying what it is for. Links inside a plan are relative to this folder, so repository paths
need a `../` prefix.

**Only plans for the branch that is checked out belong here.** Plans live in a personal
`~/.claude/plans/` directory that spans every project and branch, so they are not
interchangeable: a plan written against another branch describes files that may not exist here,
and copying one in imports that branch's state through the back door. Archive a plan in this
folder only when it was written for this branch.
