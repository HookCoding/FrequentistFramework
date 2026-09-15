# Work notebook

A running record of work on this repository: one entry per activity, in the order it happened,
each with the objective it was done for and what came out of it. Append new entries at the
bottom. Times are local (CERN).

Entries are not rewritten once written, even when something in them later turns out to be
wrong. A mistake found later gets its own new entry, appended where it was found, explaining
what was wrong and what was done about it; the original entry is touched only to add a one-line
pointer to that new entry — never to remove or reword the mistake itself.

Subheadings used inside an entry, as they apply: **Objective**, **Found**, **Added**,
**Changed**, **Fixed**, **Verified**, **Decided**, **Left alone**.

**Contents**

- [2026-03-01 23:09 — Install and path cleanup](#2026-03-01-2309--install-and-path-cleanup)
- [2026-07-20 10:35 — Bring in the published Run 2 J100 spectrum](#2026-07-20-1035--bring-in-the-published-run-2-j100-spectrum)
- [2026-07-20 10:36 — Bring in the Run 2 J50 spectrum](#2026-07-20-1036--bring-in-the-run-2-j50-spectrum)
- [2026-07-22 12:14 — First upload of the Run 2 J100 fine-binned spectrum](#2026-07-22-1214--first-upload-of-the-run-2-j100-fine-binned-spectrum)
- [2026-07-22 14:26 — Re-upload the J100 spectrum with the tile gap veto](#2026-07-22-1426--re-upload-the-j100-spectrum-with-the-tile-gap-veto)
- [2026-09-15 14:05 — Survey the new data and find what blocks a 481–3000 fit](#2026-09-15-1405--survey-the-new-data-and-find-what-blocks-a-4813000-fit)
- [2026-09-15 14:33 — De-hardcode the channel name, make the rebinning configurable](#2026-09-15-1433--de-hardcode-the-channel-name-make-the-rebinning-configurable)
- [2026-09-15 14:38 — Add the Run 2 driver and run the fit](#2026-09-15-1438--add-the-run-2-driver-and-run-the-fit)
- [2026-09-15 14:48 — Run 3 regression check](#2026-09-15-1448--run-3-regression-check)
- [2026-09-15 14:55 — Rewrite the README](#2026-09-15-1455--rewrite-the-readme)
- [2026-09-15 15:02 — Record the environment pins; licensing left open](#2026-09-15-1502--record-the-environment-pins-licensing-left-open)
- [2026-09-15 15:10 — Archive the implementation plans in the repository](#2026-09-15-1510--archive-the-implementation-plans-in-the-repository)
- [2026-09-15 15:20 — Remove the 2026-09-04 plan archived here by mistake](#2026-09-15-1520--remove-the-2026-09-04-plan-archived-here-by-mistake)
- [2026-09-15 15:40 — Make the output directory repository-relative](#2026-09-15-1540--make-the-output-directory-repository-relative)

---

## 2026-03-01 23:09 — Install and path cleanup

**Objective.** Make the install reproducible on a fresh account and stop the code depending on
one person's directories.

**Changed.** Improved the pyBumpHunter install, added histograms, removed hard-coded paths,
fixed a broken symlink. Four commits over about 25 minutes (`827eb5d` … `1bd3005`).

**Left alone.** `python/createBinning.py` kept its hard-coded
`/afs/cern.ch/work/t/tofitsch/...` input path — this came back to bite on 2026-09-15.

---

## 2026-07-20 10:35 — Bring in the published Run 2 J100 spectrum

**Objective.** Have the published Run 2 dijet TLA J100 mjj spectrum available in the
repository.

**Added.** `Input/data/dijetTLA/fullRun2TLAJ100mjj.root`, 11.6 kB. HEPData-style:
`Dijet mass distribution (J100)/Hist1D_y1`, 57 bins at analysis (resolution) binning, edges
481 → 2997.

This is the published spectrum, not a fit input — the fine 1 GeV binning the prefit needs is
not in it. It later turned out to be exactly the right rebinning target (see 2026-09-15 14:05).

---

## 2026-07-20 10:36 — Bring in the Run 2 J50 spectrum

**Objective.** Same, for the J50 trigger.

**Added.** `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`, 165 kB. Single directory
`hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/`, six histograms, 4000 bins over 0–4000 GeV.
No eta-veto variants — the simpler, older layout.

---

## 2026-07-22 12:14 — First upload of the Run 2 J100 fine-binned spectrum

**Objective.** Provide the fine-binned J100 spectrum that the fit can actually run on.

**Added.** `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`, 353 kB, one selection.

---

## 2026-07-22 14:26 — Re-upload the J100 spectrum with the tile gap veto

**Objective.** Make it possible to exclude the tile gap region (1.0 < |eta| < 1.6) from the
selection, and to compare against the complementary and wider-veto selections.

**Changed.** Same path, re-uploaded 353 kB → 2.3 MB. Now four top-level selections:

| Directory | Selection |
|---|---|
| `hists_yStar06` | no eta veto |
| `hists_yStar06_rejectEta_10_16` | tile gap veto — rejects 1.0 < \|eta\| < 1.6 |
| `hists_yStar06_rejectEta_10_24` | wider veto — rejects 1.0 < \|eta\| < 2.4 |
| `hists_yStar06_requireEta_10_16` | the complement — gap region only |

Each with `afterSelection/nominal/` and `HLT_j0_perf_ds1_L1J100/` sub-paths, and ten JES-varied
copies of `h_mjj` alongside the nominal.

**Left alone.** Nothing in the repository pointed at this file — the driver was still wired to
Run 3 ISR TLA. That is what the 2026-09-15 session picked up.

---

## 2026-09-15 14:05 — Survey the new data and find what blocks a 481–3000 fit

**Objective.** Decide whether the 2026-07-22 file can be fitted over 481–3000 GeV with six
background parameters, and work out what in the repository would have to change first.

**Found.**

- The spectra are 1 GeV binned over 0–4000 GeV, and **481 and 3000 are both exact bin edges** —
  2519 bins in range, matching `nbins = rangehigh - rangelow` in `run_anaFit.py`. No
  edge-snapping needed.
- `rangelow=481` is not arbitrary: it is exactly the first edge of the published binning in
  `fullRun2TLAJ100mjj.root`, which makes that the natural rebinning target.
- `config/dijetTLA/` is the right card set. Its background templates use √s = 13000 GeV
  consistently, matching the Run 2 data *and* matching `PreFit.py`, which is hardcoded to
  13000. The `config/dijetisrTLA/` cards are 13600 and would have prefitted the wrong energy.
- A six-parameter Run 2 template already existed
  (`background_dijetTLA_J100yStar06_sixPar.template`). `nPars` is parsed from the *filename*
  substring `"six"`, and only when `--doprefit` is passed.
- **Blocker 1.** The channel name was hardcoded to `Run3TLA` in five places. It comes from
  `<Channel Name=...>` in the category card — `Run3TLA` for dijetisrTLA, `J100yStar06` for
  dijetTLA — so switching flavour would have thrown a `KeyError` *after* the expensive fit.
- **Blocker 2.** The rebinning step was broken above 1000 GeV: `createBinning.py` reads a
  hard-coded path in another account's work area (**Permission denied** from here), its
  `--end` defaults to 1000 so the binning would have stopped near 1024 GeV while the run
  reported 481–3000, and its resolution fit is Run 3 ISR, valid only over 90–2000 GeV.
- The chosen histogram has zero negative and zero empty bins in range — worth checking, because
  `xmlAnaWSBuilder` calls `getchar()` on a negative bin and would hang a batch job with no
  diagnostic.
- `xmlAnaWSBuilder` accepts a slash-qualified `HistName`, so the nested directory path works.

**Decided.** Tile-gap-veto selection on the HLT path
(`hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj`); published Run 2 binning as the
rebinning target rather than fixing `createBinning.py`; a separate Run 2 driver rather than
editing the Run 3 one.

---

## 2026-09-15 14:33 — De-hardcode the channel name, make the rebinning configurable

**Objective.** Clear the two blockers above without changing any existing Run 3 behaviour.

**Changed.** `python/run_anaFit.py` — new `getchannel()` helper reads `<Channel Name="...">`
from the category card, and the name is threaded through `build_fit_extract()` to the quickFit
sideband range (`SBLo_`/`SBHi_`), the `GetPval()` lookups and the BumpHunter histogram names.
The category card is now the single place the channel is written down. `config/dijetisrTLA/`
resolves to `Run3TLA`, so Run 3 is unchanged by construction.

**Added.**

- `--rebinfile` / `--rebinhist` on `run_anaFit.py`. When given, the rebinned chi2/p-value and
  BumpHunter take their bin edges from that histogram and `createBinning.py` is not invoked.
  When omitted, the old auto-generation path runs exactly as before.
- `-c` / `--channel` on `python/plotPostFit.py`, default `Run3TLA`.
- A third parameter `chan` on `plot_postfit.cpp`'s `plot_postfit()`, default `"Run3TLA"`, so
  the existing two-argument call stays valid.

**Fixed.** A fit above 1000 GeV no longer silently gets a chi2 binning truncated near 1024 GeV,
provided `--rebinfile`/`--rebinhist` are supplied.

**Left alone.** `createBinning.py` itself — the Run 2 path bypasses it entirely. A comment at
the call site now warns about the 1000 GeV default.

---

## 2026-09-15 14:38 — Add the Run 2 driver and run the fit

**Objective.** Produce the 481–3000 GeV, six-parameter, background-only fit on the
tile-gap-veto spectrum, and check it end to end rather than trusting that it built.

**Added.** `scripts/run_anaFit_run2.sh`, a Run 2 driver alongside the untouched Run 3 one. The
three unused selections are kept as commented alternatives. `out_dir` had to move: the Run 3
driver's `/eos/home-t/tofitsch/tlafits` belongs to another account and is not writable, so
nothing could have been written there at all.

**Note.** The first launch at 14:38 accidentally started **two concurrent runs** into the same
output directory (a backgrounded `&&` chain kept a variable I thought it had lost). Those
outputs were discarded and a single clean run was done at 14:45. The numbers were identical
either way, but the doubled run is not a valid record.

**Verified** — clean run, 14:45–14:46:

| Check | Result |
|---|---|
| Templated card | `HistName="hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj"`, `Observable="obs_x_channel[481,3000]"`, `Binning="2519"` |
| Background card | no `PAR` placeholders left unsubstituted |
| `nbkg` | 7.6524e8 — matches the histogram integral over 481–3000 computed independently |
| Fine binning | 2519 bins, chi2/ndof = 1.0000, p = 0.496 |
| Rebinned | 57 bins spanning **481–2997**, chi2/ndof = 1.478, ndof = 51, **p = 0.0149** |
| PostFit directories | `J100yStar06`, `J100yStar06_bkgonly`, `J100yStar06_rebinned`, `J100yStar06_bkgonly_rebinned` — i.e. not `Run3TLA` |
| Fitted parameters | `nbkg`, `p2`…`p6` (`p1` pinned at 1 and constant; `nsig` constant at 0) |
| Plots | `postFit.pdf`, `post_fit.pdf`, `edm_*.pdf` all rendered |

p = 0.0149 is above the 0.01 mask threshold, so the fit was accepted and its BumpHunter
masking loop did not run.

`quickFitLog_*.log` contains two `Migrad did not converge (status 1). Retrying with higher
strategy.` warnings. These are quickFit's conservative reading of Minuit status 1 (covariance
forced positive-definite); Minuit reports `Valid minimum`, the retries land on the same FCN
(1259.111938), and the run ends `Fit Summary of POIs (STATUS OK)` at EDM = 3.1e-08. Not a
failure, but expect to see it.

**Corrected two things I had written down wrongly before checking them against the run:**
`npars` is 6, not ~8, so ndof = 51; and `nsig` does *not* float in a background-only fit — the
log shows it constant at 0, so `sigmean` only matters under `--dosignal`. Both were fixed in
the README and the driver comment.

---

## 2026-09-15 14:48 — Run 3 regression check

**Objective.** Confirm the existing Run 3 ISR TLA workflow still behaves exactly as before,
since every change above was meant to be default-preserving.

**Verified.** Re-ran the previous configuration with **no new arguments** (135–1000 GeV,
sevenPar, `config/dijetisrTLA/`), which exercises every new default:

- channel resolved to `Run3TLA`; 865 bins; fine-binned p = 0.356; rebinned p = 0.0055.
- p < 0.01, so the BumpHunter masking path *did* run — calling `FindBHWindow.py` with
  `Run3TLA_rebinned/postfit` and `Run3TLA_rebinned/data`, and the masked refit with
  `--range SBLo_Run3TLA,SBHi_Run3TLA`. Byte-identical to the strings that were hardcoded before
  the change. Masked fit p = 0.039.

Between this and the 14:38 entry, every branch touched by the channel change is covered: the
plain and `_bkgonly` p-value lookups, the BumpHunter histogram names and the quickFit sideband
range, under both `J100yStar06` and `Run3TLA`.

---

## 2026-09-15 14:55 — Rewrite the README

**Objective.** The README documented only the Run 3 input file and told you to clone a branch
that no longer matches this work; nothing in it said what to change for a new input.

**Changed.** `README.md` now carries both configurations side by side (driver, √s, range, bins,
parameter count, channel name, data file and histogram, cards, rebinning), the contents and
directory structure of the Run 2 input file, the output file layout, and a Gotchas section:
filename-derived parameter count, the `--doprefit` requirement, where the channel name is
authored, `sigmean` only mattering for s+b fits, and the fact that XMLReader and quickFit only
*warn* on failure so the log has to be read rather than the exit status.

**Removed.** The stale clone branch and the old "Files" section that documented
`data/data23_histos.root` as the only input — it is now one row of the configurations table.

---

## 2026-09-15 15:02 — Record the environment pins; licensing left open

**Objective.** Make a run reproducible by writing down what actually defines the environment,
and decide what to do about the missing LICENSE and citation metadata.

**Added.** A README "Environment" section. There is deliberately no `pyproject.toml`/uv file:
the Python and ROOT stack comes from a pinned CVMFS LCG view, not from PyPI, so a pip file
would be a second and conflicting source of truth. The pins already existed but were spread
across `install.sh` and the sub-frameworks' `setup_lxplus.sh`; they are now in one table —
LCG_102a x86_64-centos9-gcc11-opt (ROOT 6.26.08), the four sub-framework SHAs, and the
pyBumpHunter venv (Python 3.9.12 from LCG_105). The results above were produced with LCG_102a.

**Left alone.** No `LICENSE` and no `CITATION.cff` at the repository root. Both are decisions
for the repository owner and the ATLAS collaboration rather than something to add unilaterally:
this is a fork of `gitlab.cern.ch/tla-atlas-run3/FrequentistFramework` and it vendors four
upstream frameworks — pyBumpHunter carries its own BSD-3-Clause `LICENSE`, copyright Louis
Vaslin — so a repository-level licence has to account for them, and a citation file needs a
real author list. Flagged here rather than guessed at.

---

## 2026-09-15 15:10 — Archive the implementation plans in the repository

**Objective.** Keep the plans that preceded this work inside the repository so the reasoning
behind a change can be found later, instead of leaving them in a personal `~/.claude/plans/`
directory where nobody else can reach them.

**Added.** A `plans/` folder with an index (`plans/README.md`) and two plans, each copied
verbatim rather than retyped:

| File | Written | Branch | Status |
|---|---|---|---|
| `plans/2026-09-15-run2-dijet-tla-481-3000-sixpar.md` | 2026-09-15 14:27 | `claude-skills` | approved and implemented |
| `plans/2026-09-04-tier3-hot-path-support-files.md` | 2026-09-04 12:33 | not `claude-skills` | not implemented here |

**Decided.** Plans are archived **as written**, not edited to match what actually happened — a
plan records intent, and rewriting it to look correct afterwards destroys its only value. Where
a plan and this notebook disagree, the notebook wins, and each plan says so in a header. The
2026-09-15 plan's header names its two known divergences (ndof 51 rather than the ~50
estimated; `nsig` constant rather than floating).

**Found.** The 2026-09-04 plan targets a *different branch*: the Tier 3 documents and launcher
scripts it builds on (`doc/TIER3_COMPLETION_PLAN.md`, `doc/TIER3_SYSTEM.md`,
`doc/TIER3_EXECUTION_TRACE.md`, `scripts/run_anaFit_J100.sh`, `scripts/quality_check.py`) do
not exist on `claude-skills`, though the five Python files it wants to refactor do. It carries
a prominent warning not to execute it here as written.

**Verified.** Repository paths inside the plans were rewritten with a `../` prefix, since links
are now resolved from `plans/`. All 35 relative links across the three files resolve to files
that exist.

> **Correction.** The 2026-09-04 plan listed above should not have been archived in this repo.
> See [2026-09-15 15:20](#2026-09-15-1520--remove-the-2026-09-04-plan-archived-here-by-mistake)
> for what was wrong and what was done about it. This entry is left as originally written.

---

## 2026-09-15 15:20 — Remove the 2026-09-04 plan archived here by mistake

**Objective.** The user asked where the Tier 3 plan referenced in the 15:10 entry came from,
having expected it not to be reachable. Find out, and fix it — without rewriting the 15:10
entry itself. (The notebook's rule, stated by the user in this same exchange: a mistake found
later gets a new appended entry, and the old entry gets nothing more than a one-line pointer to
it. This entry is the first to follow that rule; the 15:10 entry above has been restored to
what it originally said and now carries only that pointer.)

**Found.** `plans/2026-09-04-tier3-hot-path-support-files.md` came from
`~/.claude/plans/take-this-plan-and-inherited-pudding.md` — the user's home directory, not this
repository and not git. Asked for "all plans," the 15:10 entry read that as every file in that
personal directory, which spans every project and branch the user has worked on, rather than
only the plans written for this repository on this branch. That file was written against a
*different* branch: it builds on `doc/TIER3_COMPLETION_PLAN.md`, `doc/TIER3_SYSTEM.md`,
`doc/TIER3_EXECUTION_TRACE.md`, `scripts/run_anaFit_J100.sh` and `scripts/quality_check.py`,
none of which exist on `claude-skills`.

No git rule was technically broken — it was a plain file read in the home directory, not a git
object, so the branch-scope hook (which blocks `git show <sha>:path`, `git checkout`, etc.
against other branches) had nothing to intercept. But copying that file into the repository
imported another branch's state through the back door, which is exactly what the branch-scope
rule exists to prevent.

**Fixed.** Deleted `plans/2026-09-04-tier3-hot-path-support-files.md`. It was untracked the
whole time — `plans/` had never been committed — so nothing entered git history and there is
nothing to revert there. Updated `plans/README.md`: dropped the row for the deleted file from
the index, and added a line stating that only plans written for the checked-out branch belong
in this folder, since `~/.claude/plans/` is not scoped to a single project.

**Verified.** `plans/` now contains only `README.md` and the 2026-09-15 plan. Re-checked every
relative link across the README, this notebook and `plans/`: still none broken.

Not blocking the work above, but worth knowing about:

- **`python/createBinning.py`** reads a hard-coded path in another account's work area
  (`/afs/cern.ch/work/t/tofitsch/.../resolutionFits.root`), not readable from other accounts; a
  readable copy is at `Input/data/dijetisrTLA/resolutionFits.root`. Its `--end` defaults to
  1000 GeV and its `gsc_mjj_reso_fit` is fitted only over 90–2000 GeV.
- **`replaceinfile()`** substitutes `PAR1` before `PAR10`, corrupting
  `background_dijetisrTLA_tenPar.template`. Affects `tenPar` only.
- **`python/plotPostFit.py`** draws chi2 histogram bin 6 labelled `#chi^{2}/ndof`, but bin 6 is
  the **p-value** — `chi2/ndof` is bin 2. A one-character fix, left alone because it would
  change a number on every plot produced so far.
- **`PreFit.py`** hardcodes √s = 13000 GeV in every fit function, which matches the
  `config/dijetTLA/` cards but **not** the `config/dijetisrTLA/` ones (13600). Its log-form
  polynomial is also one order higher than the linear form for the same `nPars`, and the
  randomised retry loop is effectively dead — lines 110–119 overwrite the randomised values on
  every iteration. Affects starting values only.
- **`plot_postfit.cpp`** does not compile under ACLiC (`.L plot_postfit.cpp+`): `ifstream` is
  used without `#include <fstream>`. Harmless — the driver runs the macro interpreted. Its
  luminosity label is also not the full Run 2 value.
- **The pyBumpHunter venv** installs numpy, matplotlib, scipy and uproot **unpinned**, so that
  part of the environment is not reproducible over time.

## 2026-09-15 15:40 — Make the output directory repository-relative

**Objective.** Every shell driver hardcoded an absolute EOS output path belonging to whoever
last ran it (`scripts/run_anaFit.sh` still pointed at `tofitsch`'s area, not writable from this
account), so a fresh clone wrote nowhere useful until that line was found and edited by hand.
Plan: `plans/2026-09-15-repo-relative-output-dir.md`.

**Changed.** `scripts/run_anaFit.sh`, `scripts/run_anaFit_run2.sh`, `scripts/run_anaFit_syst.sh`
and `scripts/run_nloFit.sh` now set `out_dir=${OUT_DIR:-$PWD/run}` — `$PWD` is already
guaranteed to be the repository root, since `setup_buildAndFit.sh` aborts otherwise and every
config/`Input/`/`./python/` path in the drivers is relative. `run_anaFit_syst.sh`'s `folder=`
line, previously hardcoded to `lbazzano`'s EOS area with no `out_dir` variable at all, now
builds on `$out_dir`. In each driver the `mkdir -p $out_dir` was moved to after the
`setup_buildAndFit.sh` guard runs, so a wrong-directory invocation aborts before creating
anything.

`OUT_DIR` is not a later refinement — it is required from the start. AFS home quota here is at
94% (9.83 of 10 GB), and the HTCondor toy studies (`submission/condor_handler.py`) fan out
hundreds of fits; a repo-relative default alone would fail partway through a long campaign.

Updated `README.md` and `CLAUDE.md` to describe the new default and the `OUT_DIR` override
instead of instructing the reader to edit `out_dir` by hand.

**Left alone.** `run_nloFit.sh` sources `scripts/setup_buildCombineFit.sh`, which does not
exist anywhere in the repository — that driver was already broken before this change and stays
broken; only its output-path handling was made consistent with the others for when it is fixed.

**Verified.** `bash -n` on all four edited drivers. Ran `scripts/run_anaFit_run2.sh` end to end
with no `OUT_DIR` set: output landed at `run/run_481_3000_sixPar/` inside the repository (793
kB, matching the earlier EOS copy), p(chi2)=0.015 matching the 2026-09-15 14:38 run, all
expected files present (`FitResult_*`, `PostFit_*`, `FitParameters_*`, `postFit.pdf`,
`quickFitLog_*`), and `git status` confirms `run/` stays untracked. Confirmed the `OUT_DIR`
override resolves to the EOS path as expected without re-running the fit against it, since an
EOS copy from earlier in the session already exists at that path.

`plot_postfit.cpp` prints two `TFile` "does not exist" errors for `*_masked.root` files —
pre-existing, unrelated to this change: the macro unconditionally tries to open masked-fit
output, and this fit's p(chi2)=0.015 passed the 0.01 mask threshold, so no masked files were
ever produced.
