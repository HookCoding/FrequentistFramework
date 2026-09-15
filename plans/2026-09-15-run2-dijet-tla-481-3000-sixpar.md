# Run the fit on the new Run 2 dijet TLA data (481–3000 GeV, 6 parameters)

**Written** 2026-09-15 14:27 &nbsp;|&nbsp; **Branch** `claude-skills` &nbsp;|&nbsp; **Status** approved and implemented

Archived as written, before implementation. What actually happened, including the two
places where the run contradicted this plan, is in the notebook entries for 2026-09-15
14:33 through 15:02 in [CHANGELOG.md](../CHANGELOG.md). Known divergences: `ndof` came
out 51 (not the ~50 estimated here), and `nsig` is held constant at 0 in a
background-only fit rather than floating.

> **Note.** This plan originally explained the fix by contrasting it with the repository's
> other, higher-energy analysis flavour, whose data has since been removed from this branch.
> Those contrasts have been trimmed so the plan reads as a record of the Run 2 work alone.

---

## Context

The last commit (`30b8164`, "uploaded run2 dijet tla mjj with tile gap veto") replaced
[Input/data/dijetTLA/mjj_spectra_J100_dataAll.root](../Input/data/dijetTLA/mjj_spectra_J100_dataAll.root)
with a 6.4× larger file containing the full Run 2 dijet TLA J100 mjj spectrum, including
tile-gap-veto variants. Nothing in the repository points at it: the only existing driver
was wired to a different configuration, and [README.md](../README.md) documented neither
the new file nor any of the knobs you would change to use it.

The goal is to run a background-only fit over **481–3000 GeV with 6 background parameters**
on the tile-gap-veto spectrum, and to leave behind documentation that makes the run
reproducible. Two things block this today beyond simple reconfiguration: the postfit
channel name is hardcoded to a single literal value in five places, and the
resolution-binning step used for the chi2/p-value is broken for any range above 1000 GeV.

Requested deliverables: this plan for review **before** any code changes, and a changelog
document giving a clean timeline of what changed in the repository.

### Decisions already made

| Choice | Value |
|---|---|
| Input histogram | `hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj` (tile gap veto, HLT path) |
| Chi2 / p-value binning | Official Run 2 binning from `fullRun2TLAJ100mjj.root` (57 bins, 481–2997) |
| Analysis flavour | `config/dijetTLA/` (Run 2, √s = 13 TeV) |

## What the exploration established

Verified directly against the files, not assumed:

- **The new data is 1 GeV binned, 0–4000 GeV.** Both 481 and 3000 are *exact* bin edges,
  giving 2519 bins in range — which matches `nbins = rangehigh - rangelow` at
  [run_anaFit.py:146](../python/run_anaFit.py#L146). No rebinning or edge-snapping needed.
- **`rangelow=481` is not arbitrary.** `Input/data/dijetTLA/fullRun2TLAJ100mjj.root` →
  `Dijet mass distribution (J100)/Hist1D_y1` is the published Run 2 analysis binning:
  57 bins with first edge exactly **481** and last edge **2997**. This is the natural
  rebin target and needs no generation step.
- **`config/dijetTLA/` is the correct flavour.** Its background templates use √s = `13000.`
  consistently, matching the Run 2 data — and matching [PreFit.py](../python/PreFit.py), whose
  fit functions are hardcoded to `13000.`.
- **A 6-parameter Run 2 template already exists**:
  [config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template](../config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template).
  `nPars` is parsed from the *filename substring* `"six"`
  ([run_anaFit.py:197](../python/run_anaFit.py#L197)), and only when `--doprefit` is passed.
- **xmlAnaWSBuilder accepts a slash-qualified `HistName`** — precedent at
  [config/dijetTLA/category_dijetTLA_J75yStar03.xml:3](../config/dijetTLA/category_dijetTLA_J75yStar03.xml#L3)
  (`HistName="Nominal/DSJ75yStar03_..."`), so the nested directory path works as `--datahist`.
- **The sub-frameworks are already built** — `xmlAnaWSBuilder/build/bin/XMLReader`,
  `quickFit/build/quickFit` and `pyBumpHunter/pyBH_env` all exist. No `install.sh` re-run.

### The two real blockers

**1. The channel name is hardcoded to a single literal value in five places.** It comes
from `Channel Name="..."` in the category card. Every `config/dijetTLA/` category card
says `J100yStar06`, but the code assumed the other flavour's value. Switching flavour
without fixing this gives a `KeyError` *after* the expensive fit has already run, at:

- [run_anaFit.py:47](../python/run_anaFit.py#L47) — the quickFit sideband `--range`
- [run_anaFit.py:110,112](../python/run_anaFit.py#L110) — the `GetPval()` lookups
- [run_anaFit.py:344](../python/run_anaFit.py#L344) — the BumpHunter histogram names
- [plotPostFit.py:12,13,39](../python/plotPostFit.py#L12) — the postfit/data/chi2 paths
- [plot_postfit.cpp:60-63,70-73](../plot_postfit.cpp#L60) — the same, ×8

[run_anaFit.py:343](../python/run_anaFit.py#L343) is a commented-out `J100yStar06_rebinned`
variant of line 344 — this switch has been done by hand before, which is exactly the kind of
edit that should stop being manual.

**2. The resolution-binning step is broken for `rangehigh=3000`.**
[run_anaFit.py:77-81](../python/run_anaFit.py#L77) auto-generates a resolution binning file
via `createBinning.py` when it is missing. Three independent faults:

- `createBinning.py` reads a hardcoded path in another user's work area,
  `/afs/cern.ch/work/t/tofitsch/.../resolutionFits.root` — **Permission denied** from this
  account.
- Its `--end` defaults to **1000** and [run_anaFit.py:81](../python/run_anaFit.py#L81) never
  passes `-e`, so the generated binning would stop at ~1024 GeV. The chi2/p-value would be
  computed over 481–1024 while reporting a 481–3000 fit — a silent, wrong result.
- Its resolution fit is only valid over **90–2000 GeV**, and belongs to a different analysis
  entirely.

Using the official Run 2 binning sidesteps all three.

## Plan

### 1. De-hardcode the channel name

**[python/run_anaFit.py](../python/run_anaFit.py) — derive it from the category card.** The
function already has the category template path in hand, so there is nothing for the caller
to keep in sync and no way to get it wrong:

```python
# in run_anaFit(), after tmpcategoryfile is written
channel = re.search(r'Channel Name="([^"]+)"', open(tmpcategoryfile).read()).group(1)
```

Thread `channel` into `build_fit_extract()` (add a parameter defaulting to the existing
literal) and use it at lines 47, 110, 112 and 344 in place of the literal. The other flavour
keeps working untouched, because its category card resolves to the same default.

**[python/plotPostFit.py](../python/plotPostFit.py)** — add `-c/--channel`, defaulting to the
existing literal; use it at lines 12, 13, 39.

**[plot_postfit.cpp](../plot_postfit.cpp)** — add a third parameter `channel`, defaulting to
the existing literal, and build the eight histogram paths with `Form()`.

The plotters take the value explicitly rather than deriving it — they never see the category
card. That is a small duplication of one string, accepted because a wrong value there costs a
missing plot, not a crashed fit.

### 2. Make the rebin binning configurable

**[python/run_anaFit.py:77-81, 101-102](../python/run_anaFit.py#L77)** — add `--rebinfile` and
`--rebinhist` arguments, both defaulting to `None`. When they are given, pass them straight
to `PostfitExtractor` and **skip the `createBinning.py` block entirely**. When absent, keep
the existing auto-generation path byte-for-byte so the other flavour's behaviour is unchanged.

`createBinning.py` is deliberately **not** fixed — our run no longer touches it (see
"Deliberately not changed" below).

### 3. Add a Run 2 driver

Add **`scripts/run_anaFit_run2.sh`** rather than editing the existing driver. The Run 2
configuration differs in roughly ten variables; commenting out the existing lines in a
10 KB file of live configuration history would both obscure that history and break the
other workflow. The repo already keeps flavour-specific drivers side by side
(`run_nloFit.sh`, `run_anaFit_syst.sh`). Zero regression risk on the existing driver.

Contents — a trimmed copy of the existing driver with:

```bash
out_dir=/eos/user/h/hhook/tlafits     # current value is another user's area, NOT writable
pars=six
rangelow=481
rangehigh=3000
dosignal=0 ; dolimit=0 ; doprefit=1
sigmean=1000                          # must sit INSIDE the fit range; 400 does not
sigwidth=8

datafile=Input/data/dijetTLA/mjj_spectra_J100_dataAll.root
datahist=hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj

topfile=config/dijetTLA/dijetTLA_J100yStar06.template
categoryfile=config/dijetTLA/category_dijetTLA.template          # the generic placeholder card
backgroundfile=config/dijetTLA/background_dijetTLA_J100yStar06_${pars}Par.template
signalfile=config/dijetTLA/signal/signal_dijetTLA.template
channel=J100yStar06

rebinfile=Input/data/dijetTLA/fullRun2TLAJ100mjj.root
rebinhist="Dijet mass distribution (J100)/Hist1D_y1"             # quote: spaces + parens
```

Three points worth stating explicitly:

- Use `category_dijetTLA.template`, **not** `category_dijetTLA_J100yStar06_sixPar.template` —
  the latter is a legacy card with ~100 hardcoded signal samples and no placeholders.
- `out_dir` must change: the existing driver's output path is owned by another user and is
  not writable from this account, so it cannot write output at all.
- `sigmean=400` (the current value) falls *below* `rangelow=481`, putting the placeholder
  Gaussian outside the observable range. `dosignal=0` makes it harmless in principle, but
  1000 keeps it inside the range and avoids a degenerate normalisation.

### 4. Rewrite [README.md](../README.md)

Current content is 39 lines and stale: it clones branch `tofitsch_baseline_fit`, links a
*different* branch, and its only "Files" entry is a single hardcoded data file. Replace with:

- **Install / Setup / Run** — corrected, noting `install.sh` and `setup.sh` must be *sourced*,
  and that all commands run from the repository root.
- **Configuration** — driver, data file, histogram, range, parameter count, √s and channel
  name for the Run 2 dijet TLA setup.
- **Input data** — what is in `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`: the four
  selections, the two sub-paths, the 1 GeV binning, and which one is the tile gap veto.
- **Output** — what lands in `$out_dir/run_481_3000_sixPar/`: `FitResult_*`, `PostFit_*`,
  `FitParameters_*`, `quickFitLog_*.log`, `post_fit.pdf`.
- **Traps** — `nPars` comes from the background *filename*; `--doprefit` is required for
  parameter substitution; both sub-frameworks only warn on failure, so read the log.

Keep the existing Links section; drop the stale clone branch and the old "Files" section.

### 5. Add `CHANGELOG.md` — the requested timeline

New file at repo root, [Keep a Changelog](https://keepachangelog.com) format, seeded with the
real history from `git log` so it reads as a timeline rather than a single dump:

```markdown
## [Unreleased]
### Added
- scripts/run_anaFit_run2.sh — Run 2 dijet TLA driver (481–3000 GeV, 6 par, tile gap veto)
- --rebinfile / --rebinhist options on run_anaFit.py
- CHANGELOG.md
### Changed
- Channel name derived from the category card instead of a hardcoded literal
- README.md rewritten: documents the configuration, input data and output layout
### Known issues
- createBinning.py: unreadable hardcoded path; --end defaults to 1000 (see below)

## 2026-07-22
- Uploaded full Run 2 dijet TLA J100 mjj spectrum with tile gap veto (30b8164)
...
```

`.gitignore` swallows `*.txt` but not `*.md`, so this file is tracked normally.

## Files touched

| File | Change |
|---|---|
| [python/run_anaFit.py](../python/run_anaFit.py) | derive channel name; add `--rebinfile`/`--rebinhist` |
| [python/plotPostFit.py](../python/plotPostFit.py) | add `-c/--channel` (default preserved) |
| [plot_postfit.cpp](../plot_postfit.cpp) | add `channel` parameter (default preserved) |
| `scripts/run_anaFit_run2.sh` | **new** — Run 2 driver |
| [README.md](../README.md) | rewritten |
| `CHANGELOG.md` | **new** — change timeline |

Not modified: every file under `config/`, and all input ROOT files.

## Deliberately not changed

Recorded here and in the changelog so the decisions are visible rather than silent:

- **`python/createBinning.py`** — its unreadable hardcoded path and `--end 1000` default are
  real bugs, but our run bypasses it entirely. Fixing it is a separate concern; it stays
  listed under "Known issues".
- **The `PAR1`/`PAR10` regex collision** at [run_anaFit.py:248-251](../python/run_anaFit.py#L248):
  `replaceinfile` substitutes `PAR1` before `PAR10`, corrupting the tenPar template. Affects
  only `tenPar`, not our sixPar run.
- **[plotPostFit.py:39-41](../python/plotPostFit.py#L39) mislabels the plotted number.** It reads
  `chi2` histogram bin **6** and draws it as `#chi^{2}/ndof`, but bin 6 is the **p-value** —
  `chi2/ndof` is bin 2. A one-character fix, and we are already editing this file, but
  changing it alters a number on every plot produced so far, so it is left alone unless you
  want it: say so and it is a one-line change.
- **`PreFit.py` log-form polynomial order** is one higher than the linear form for the same
  `nPars`, and its randomised retry loop is effectively dead
  ([PreFit.py:110-119](../python/PreFit.py#L110) overwrite the randomised values every
  iteration). Pre-existing behaviour affecting starting values only; changing it would alter
  results of the other flavour and belongs in its own change.

## Verification

Run the real entry point, not just an import check:

```bash
setupATLAS && lsetup git          # from the repository root
. setup.sh
. scripts/run_anaFit_run2.sh
```

Then check, in `$out_dir/run_481_3000_sixPar/`:

1. **The prefit converged** — `nbkg` in the log should be ~7.65e8, the integral of the
   tile-gap-veto histogram over 481–3000 (verified independently with ROOT).
2. **The workspace observable is right** — the category XML written into the run folder
   should carry `obs_x_channel[481,3000]` and `Binning="2519"`.
3. **`PostFit_anaFit_sixPar_bkgOnly.root` exists** and contains four directories named
   `J100yStar06`, `J100yStar06_bkgonly`, `J100yStar06_rebinned`, `J100yStar06_bkgonly_rebinned`
   — the presence of `J100yStar06` rather than the other flavour's channel name is the direct
   check that change 1 worked.
4. **The rebinned histogram has 57 bins spanning 481–2997** — the direct check that change 2
   worked and that the binning was not silently truncated at 1000 GeV.
5. **chi2/ndof and p-value** from the `chi2` histogram, whose bins are labelled
   `chi2`, `chi2/ndof`, `nbins`, `npars`, `ndof`, `pval` in that order
   ([ExtractPostfitFromWS.py:105-110](../python/ExtractPostfitFromWS.py#L105)) — read `ndof`
   from bin 5 and `pval` from bin 6 rather than assuming. Report the values; do not assert
   in advance that they are good.
6. **`post_fit.pdf` renders** with residuals, and `FitParameters_anaFit_sixPar_bkgOnly.root`
   holds 6 fitted parameters.

Neither XMLReader nor quickFit returns a non-zero exit code on failure — they only warn — so
step 1 must read `quickFitLog_anaFit_sixPar_bkgOnly.log`, not the exit status.

A physics caveat to flag rather than bury: the p-value depends on the chi2 binning, and the
Run 2 binning tops out at 2997 while the fit runs to 3000. The 2997–3000 sliver is excluded
from the rebinned chi2 automatically — expected, and worth knowing when comparing numbers.
