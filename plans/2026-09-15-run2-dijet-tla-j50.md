# Run the fit on the Run 2 dijet TLA J50 data (302–2997 GeV, 6 parameters)

**Written** 2026-09-15 17:05 &nbsp;|&nbsp; **Branch** `claude-skills` &nbsp;|&nbsp; **Status** approved, implementation in progress

Archived as written. Two files (the J50 category card and the J50 driver) were created
before this plan was filed here at the reviewer's request; nothing else has been touched.
What actually happens on the run belongs in [CHANGELOG.md](../CHANGELOG.md).

---

## Context

The repository holds full Run 2 dijet TLA data for two triggers but only one driver.
[Input/data/dijetTLA/mjj_spectra_J100_dataAll.root](../Input/data/dijetTLA/mjj_spectra_J100_dataAll.root)
is fitted by [scripts/run_anaFit_run2.sh](../scripts/run_anaFit_run2.sh) (481–3000 GeV, six
background parameters, background-only), set up by the plan
[2026-09-15-run2-dijet-tla-481-3000-sixpar.md](2026-09-15-run2-dijet-tla-481-3000-sixpar.md).
[Input/data/dijetTLA/mjj_spectra_J50_dataAll.root](../Input/data/dijetTLA/mjj_spectra_J50_dataAll.root)
was committed in `858cf49` ("adding full run 2 dijet tla J50 mjj histogram") and nothing in
the repository references it — the low-mass reach that the J50 stream exists to provide is
simply not being fitted.

The goal is a J50 driver that mirrors the J100 one, so both triggers can be run the same way.

### Decisions already made

| Choice | Value | Where it came from |
|---|---|---|
| Fit range | 302 – 2997 GeV | reviewer's choice; 302 is the legacy J50 low edge, 2997 matches the J100 fit's upper edge |
| Background parameters | six | reviewer's choice, mirroring the J100 fit |
| Input histogram | `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj` | the only selection in the file |
| Chi2 / p-value binning | `Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root`, hist `data` | see §4 |

## What the exploration established

Verified directly against the files with ROOT, not assumed:

- **The J50 file carries one selection only.** `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/`,
  with `h_mjj` plus five JES-varied copies (`_genCorrScale`, `_insituScale`, `_gscScale`,
  `_etaJESScale`, `_pileupScale`). No `rejectEta_*` variants, no `afterSelection/nominal`
  path, and none of the `_gscScale_Tile0 / _EM3 / _N90 / _TileGap3` copies the J100 file has.
  So, unlike the J100 driver, there is no `datahist` choice to document.
- **Same granularity as J100.** `TH1F`, 4000 bins of 1 GeV over 0–4000 GeV, 4.754e9 entries.
  `run_anaFit.py` sets `nbins = rangehigh - rangelow`, which this satisfies.
- **Turn-on is well below the chosen range.** The spectrum rises to a peak at ~225 GeV and
  falls monotonically from there (10 GeV sums: 210–220 → 4.27e8, 220–230 → 4.34e8,
  230–240 → 4.05e8, 300–310 → 1.40e8). 302 GeV is comfortably on the plateau.
- **The stream is prescaled.** Above ~300 GeV it holds ~4–5× *fewer* events than J100 over
  the same bins (e.g. 481–506: 3.1e7 vs 1.5e8). At the top of the range the statistics are
  thin — ~1.4e3 events in 2926–2997, against ~1.1e4 for J100. Expected for a prescaled
  low-threshold stream, not a fault, but it is why 2997 is a stats-limited upper edge rather
  than a natural one.
- **The `createBinning.py` fallback is dead.** It reads
  `/afs/cern.ch/work/t/tofitsch/.../resolutionFits.root`, which returns **Permission denied**
  from this account, and its `--end` defaults to 1000 GeV. `--rebinfile`/`--rebinhist` must
  therefore be supplied explicitly, exactly as the J100 driver does.

## Changes

### 1. New — `config/dijetTLA/category_dijetTLA_J50yStar06.template`

Copy of [config/dijetTLA/category_dijetTLA.template](../config/dijetTLA/category_dijetTLA.template)
with one edit:

```xml
<Channel Name="J50yStar06" Type="shape" Lumi="1">
```

Needed because `run_anaFit.py` derives the channel name from the category card via
`getchannel()`, and that name becomes the RooCategory label, the `PostFit_*.root` directory
names and the plot legends. Sharing the J100 card would label every J50 output
`J100yStar06`. Everything else in the card is placeholders and stays untouched.

### 2. New — `scripts/run_anaFit_run2_J50.sh`

Copy of [scripts/run_anaFit_run2.sh](../scripts/run_anaFit_run2.sh) with only these lines
changed. Structure, `flags` assembly, the `run_anaFit.py` invocation and both plotting calls
stay identical:

```bash
rangelow=302
rangehigh=2997

datafile=Input/data/dijetTLA/mjj_spectra_J50_dataAll.root
datahist=hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj

folder=$out_dir/run_J50_${rangelow}_${rangehigh}_${pars}Par

categoryfile=config/dijetTLA/category_dijetTLA_J50yStar06.template

rebinfile=Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root
rebinhist=data
```

`sigmean=1000` / `sigwidth=8` stay (inside the range, and inert in a background-only fit), as
do `doprefit=1`, `dosignal=0`, `dolimit=0`, `maskthreshold=0.01`, `nbkg="dummy"` and the
`for pars in six` loop. The J100-only commented-out `datahist` alternatives are dropped — the
J50 file has none — and the tile-gap-veto comment is replaced by a note that J50 carries a
single selection. `folder` gains a `J50_` prefix so the two triggers cannot collide in `run/`
if their ranges ever overlap.

### 3. Reused unchanged — no new cards

- [config/dijetTLA/dijetTLA_J100yStar06.template](../config/dijetTLA/dijetTLA_J100yStar06.template)
  (top card): holds only `CATEGORYFILE`, `OUTPUTFILE` and `nsig_SIGNAME` placeholders —
  nothing J100-specific despite the name.
- [config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template](../config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template):
  the 6-parameter dijet function at √s = 13000 GeV with every start value a `PARn`
  placeholder filled by the prefit. Trigger-independent. **Its filename must keep containing
  `six`** — `run_anaFit.py` parses `nPars` from the background *filename*.
- `config/dijetTLA/signal/signal_dijetTLA.template`.

A comment in the J50 script says these three are shared, so the `J100` in two of the
filenames does not read as a mistake. Copying the background card to a `J50yStar06` name buys
nothing today — the content would be byte-identical — and is worth doing only if the J50 fit
later needs different parameter bounds.

The existing `config/dijetTLA/background_dijetTLA_J50yStar06_*.xml` files are **not** usable:
they carry literal start values instead of `PARn`, so `--doprefit` has nothing to substitute.

### 4. Rebinning — an existing file covers it, no new data needed

There is no published J50 analysis binning. But
`Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root` (hist `data`, TH1D,
75 bins) holds the standard dijet binning over 171–3217 GeV:

```
171 188 206 224 243 262 282 302 323 344 365 387 410 433 457 481 506 531 ... 2997 3069 3142 3217
```

Verified: its edges over 481–2997 are **identical** to the 57 bins of the published
`fullRun2TLAJ100mjj.root:"Dijet mass distribution (J100)/Hist1D_y1"` that the J100 fit uses.
It is the same binning, extended down into the low-mass region J50 covers. Both 302 and 2997
are exact edges in it, and `ExtractPostfitFromWS.py` clips the edge list to the postfit range,
so the edges outside 302–2997 are dropped automatically.

Using it means the J50 and J100 fits are rebinned onto the same bin boundaries wherever they
overlap, which is what makes the two results comparable.

### 5. Docs

- [README.md](../README.md): the Configuration table gains a J50 column and the Run 2 input
  data section gains a short J50 paragraph.
- [CHANGELOG.md](../CHANGELOG.md): one entry in the existing style.

## Verification

Run from the repository root — the drivers abort otherwise:

```bash
setupATLAS && lsetup git
. setup.sh
. scripts/run_anaFit_run2_J50.sh
```

Then, in `run/run_J50_302_2997_sixPar/`:

1. `quickFitLog_anaFit_sixPar_bkgOnly.log` — **read it, do not trust the exit code**
   (`build_fit_extract()` only warns on non-zero). Confirm the prefit substituted all six
   `PARn` and that quickFit converged.
2. `PostFit_anaFit_sixPar_bkgOnly.root` exists and its directories are named `J50yStar06*`,
   not `J100yStar06*` — the check that change 1 took effect.
3. The rebinned chi2/p-value printed by `run_anaFit.py`. If p < `maskthreshold` (0.01) the
   BumpHunter masking loop fires and reruns the whole build+fit — designed behaviour, but
   inspect `BHresults.json` before believing a bump in a prescaled stream.
4. `postFit.pdf` and `post_fit.pdf` render, with the spectrum starting at 302 GeV.
5. `scripts/run_anaFit_run2.sh` still reproduces `run/run_481_3000_sixPar/`. The shared cards
   were not edited so this should be untouched, but it is a cheap regression check.

## Flagged, not fixed

`plot_postfit.cpp` hardcodes `lumi_label = "#sqrt{s} = 13 TeV, 25 fb^{-1}"` as a file-scope
constant. That is already wrong for the Run 2 J100 fit, and a prescaled J50 stream has a
different effective luminosity again. Pre-existing and out of scope for this plan; making it
a per-channel argument is a small follow-up if wanted.

## What this plan does not do

- No signal fits, limits or F-test for J50. Background-only at six parameters, as asked. A
  narrower or lower-mass window may well prefer five parameters; the `for pars in` loop is
  left in place so an F-test can be run later without editing anything else.
- No J50-specific background card, and no change to any file the J100 fit reads.
