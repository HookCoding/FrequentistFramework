# FrequentistFramework

ATLAS statistical-fit framework for dijet / TLA bump-hunt analyses. It wraps three C++
sub-frameworks, cloned at pinned SHAs from their public GitHub mirrors
([xmlAnaWSBuilder](https://github.com/tofitsch/xmlAnaWSBuilder),
[quickFit](https://github.com/tofitsch/quickFit),
[workspaceCombiner](https://github.com/tofitsch/workspaceCombiner)), plus
[pyBumpHunter](https://github.com/scikit-hep/pyBumpHunter) behind Python drivers that
template XML workspace cards, run the fit, and extract postfit histograms, fit parameters
and p-values.

The pipeline is: **card templating → ROOT prefit → workspace build → fit → extraction →
optional BumpHunter masking loop → plots**. [python/run_anaFit.py](python/run_anaFit.py) is
the orchestrator; read it first.

Project records: [CHANGELOG.md](CHANGELOG.md) is a work notebook of what was done, when and
why; [plans/](plans/) holds the implementation plans written beforehand.

# Install

```
setupATLAS
lsetup git
git clone <this repository>
cd FrequentistFramework
. install.sh
```

`install.sh` clones and cmake-builds the sub-frameworks at pinned SHAs (takes a while).

# Setup

```
. setup.sh
```

## Environment

There is no `pip`/`uv` dependency file, and adding one would be misleading: the Python and
ROOT stack comes from a pinned CVMFS LCG view, not from PyPI. The pins that define a run are:

| Component | Pin | Where |
|---|---|---|
| LCG view | `views LCG_102a x86_64-centos9-gcc11-opt` (ROOT 6.26.08) | `quickFit/setup_lxplus.sh`, `xmlAnaWSBuilder/setup_lxplus.sh` |
| xmlAnaWSBuilder | `6b84050f3c0206a6f30eb40b103cc101e68505cc` | `install.sh` |
| quickFit | `0408030b6c8d74a2e2c27a864a02756132d08f5a` | `install.sh` |
| workspaceCombiner | `7d484ad3f89c4075d2c567aa4503fc56e1bb9468` | `install.sh` |
| pyBumpHunter | `91f49a622bd77622edb02a1a2788fc12835e5b72` | `install.sh` |
| RooFitExtensions | `ba94bfcbfa4f4a4e3541ade09580399e409e8514` | `<fw>/scripts/install_roofitext.sh` inside each pinned clone |
| `cmake` | **unpinned** — resolved by `lsetup cmake` at build time | `<fw>/setup_lxplus.sh` |
| pyBumpHunter venv | Python 3.9.12 from the same LCG_102a view; only the pyBumpHunter egg is installed in it, numpy/scipy/uproot leak in from the LCG view via `PYTHONPATH` (**unpinned**) | `pyBumpHunter/pyBH_env/pyvenv.cfg` |

pyBumpHunter lives in its own virtualenv (`pyBumpHunter/pyBH_env`) because its numpy conflicts
with the CVMFS one; `run_anaFit.py` activates it inline for the BumpHunter step only.

The results recorded in [CHANGELOG.md](CHANGELOG.md) were produced with LCG_102a.

`install.sh` and `setup.sh` must be **sourced**, not executed — they `cd` around and export
`$_DIRFIT`, `$_DIRXMLWSBUILDER` and `$_DIRCOMB`. All commands must be run **from the
repository root**: `scripts/setup_buildAndFit.sh` refuses to run if `xmlAnaWSBuilder/` and
`quickFit/` are not in `$PWD`, and each driver stops on that refusal with
`ERROR: run this from the FrequentistFramework repository root.` rather than carrying on into
the fit with no environment. Until 2026-09-17 the drivers did carry on — see
[KNOWN_ISSUES.md](KNOWN_ISSUES.md) issue 43.

# Run

Output defaults to `<repo>/run/`, and each driver names its own subdirectory under it — there is
no single shape:

| Driver | Subdirectory |
|---|---|
| `run_anaFit.sh`, `run_anaFit_run2.sh` | `run_<rangelow>_<rangehigh>_<n>Par/` |
| `run_anaFit_run2_J50.sh` | `run_J50_<rangelow>_<rangehigh>_<n>Par/` |
| `run_anaFit_syst.sh` | `run_systematics_<rangelow>_<rangehigh>_<n>Par/` |
| `run_nloFit.sh` | `outOfTheBoxFit/` |

Override the parent with `OUT_DIR=/path/to/eos/area` for toy studies fanned out over HTCondor —
AFS home quotas are too small for hundreds of runs. **`OUT_DIR` does not reach
`scripts/run_anaFit_flowchart.sh`**, which hardcodes `folder=run/outOfTheBoxPD` and ignores
`$out_dir` entirely.

```
. scripts/run_anaFit_run2.sh        # Run 2 dijet TLA J100  (13 TeV)
. scripts/run_anaFit_run2_J50.sh    # Run 2 dijet TLA J50   (13 TeV)
```

Other drivers: `scripts/run_nloFit.sh` (NLO-template fit), `scripts/run_anaFit_syst.sh`,
`scripts/run_anaFitLoop.sh`, `scripts/run_swiftFit.py`.

**Check the exit status of the two Run 2 drivers.** If a fit fails p(chi2), has its most
significant window masked by BumpHunter, is re-fitted and *still* fails, `run_anaFit.py` reports
that as a non-zero exit and the driver prints an `ERROR: … this result must not be used` banner
and exits non-zero itself. The postfit plots are still written in that case — they are the
diagnostics you need in order to see why — so the plots alone do not tell you whether the fit was
accepted. Until 2026-09-17 this verdict was computed and then discarded, and a rejected fit exited
0 ([KNOWN_ISSUES.md](KNOWN_ISSUES.md) issue 38); anything that checks these drivers' status will
now start seeing failures it previously missed.

# Configuration

|  | Run 2 dijet TLA J100 | Run 2 dijet TLA J50 |
|---|---|---|
| Driver | `scripts/run_anaFit_run2.sh` | `scripts/run_anaFit_run2_J50.sh` |
| √s | 13 TeV | 13 TeV |
| Fit range | 481 – 3000 GeV | 302 – 2997 GeV |
| Bins in range | 2519 (1 GeV) | 2695 (1 GeV) |
| Background parameters | six | six |
| Channel name | `J100yStar06` | `J50yStar06` |
| Data file | `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root` | `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root` |
| Data histogram | `hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj` | `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj` |
| Cards | `config/dijetTLA/` (top/background/signal cards shared; category card is per-channel) | same |
| Rebinning | `Input/data/dijetTLA/fullRun2TLAJ100mjj.root` (57 bins, 481–2997) | `Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root`, hist `data` (75 bins, 171–3217, clipped to range) |

## Run 2 input data

`Input/data/dijetTLA/mjj_spectra_J100_dataAll.root` holds the full Run 2 dijet TLA J100
spectrum. Every histogram is `TH1F`, 4000 bins of 1 GeV over 0–4000 GeV. Four selections,
each with an `afterSelection/nominal/` and an `HLT_j0_perf_ds1_L1J100/` sub-path (plus ten
JES-varied copies of `h_mjj` alongside the nominal one):

| Directory | Selection |
|---|---|
| `hists_yStar06` | no eta veto |
| `hists_yStar06_rejectEta_10_16` | **tile gap veto** — rejects 1.0 < \|eta\| < 1.6 (the default) |
| `hists_yStar06_rejectEta_10_24` | wider veto — rejects 1.0 < \|eta\| < 2.4 |
| `hists_yStar06_requireEta_10_16` | the complement — gap region only |

`Input/data/dijetTLA/fullRun2TLAJ100mjj.root` holds the published Run 2 spectrum at analysis
binning (`Dijet mass distribution (J100)/Hist1D_y1`, 57 bins from 481 to 2997). It is used as
the rebinning target for the chi2/p-value, not as a fit input — its first bin edge is exactly
481, which is why the fit range starts there.

`Input/data/dijetTLA/mjj_spectra_J50_dataAll.root` holds the full Run 2 dijet TLA J50
spectrum: `TH1F`, 4000 bins of 1 GeV over 0–4000 GeV, but a single selection only
(`hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/`, plus five JES-varied copies of `h_mjj`) —
no eta-veto variants and no `afterSelection/nominal` path. The J50 stream is prescaled: above
~300 GeV it carries roughly 4–5× fewer events than J100 in the same bins, so statistics are
thin at the top of its 302–2997 fit range. There is no published J50 analysis-binning file;
the fit instead reuses `Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root`,
whose edges over 481–2997 are identical to the published J100 binning above, just extended
down to 171 — this is what lets the two fits' rebinned results line up bin-for-bin where they
overlap.

# Outputs

In `$out_dir/run_<rangelow>_<rangehigh>_<n>Par/`:

| File | Contents |
|---|---|
| `*_fromTemplate.xml` | the templated cards actually fed to the workspace builder |
| `FitResult_anaFit_<n>Par_bkgOnly.root` | quickFit result + saved workspace |
| `PostFit_anaFit_<n>Par_bkgOnly.root` | one directory per channel, each with `data`, `postfit`, `residuals`, `chi2` |
| `FitParameters_anaFit_<n>Par_bkgOnly.root` | `postfit_params`, covariance and correlation |
| `quickFitLog_*.log`, `edm_*.pdf` | fit log and EDM convergence plot |
| `postFit.pdf`, `post_fit.pdf` | postfit plots from `plotPostFit.py` and `plot_postfit.cpp` |
| `BHresults.json` | only when the BumpHunter masking loop ran |

The `chi2` histogram's bins are labelled, in order: `chi2`, `chi2/ndof`, `nbins`, `npars`,
`ndof`, `pval`.

# Gotchas

- **The number of background parameters is parsed from the background card's filename**
  (`..._sixPar.template` → 6), and only when `--doprefit` is given. Without `--doprefit` the
  `PARn` placeholders are never substituted and literal `PAR2`, `PAR3`, … reach the workspace
  builder.
- **The channel name is authored once**, in `<Channel Name="...">` in the category card.
  `run_anaFit.py` derives it from there; `plotPostFit.py -c` and `plot_postfit.cpp`'s third
  argument take it explicitly. Change it in the card, nowhere else.
- **`sigmean` only matters for s+b fits.** In a background-only run `nsig` is held constant at
  0 (it shows as `C` in `quickFitLog_*.log`), so the signal Gaussian is inert. With
  `--dosignal` it floats, and `sigmean` must then lie inside `[rangelow, rangehigh]` — a
  Gaussian centred outside the observable range is an edge artefact. Keeping `sigmean` inside
  the range regardless means the card stays meaningful when you flip `dosignal` on.
- **XMLReader and quickFit only warn on failure** — they do not return a non-zero exit code.
  Check `quickFitLog_*.log`, not the exit status.
- **`npars` in the chi2 histogram is counted from the workspace, not from the template
  filename.** `getNPars()` counts non-constant variables of the channel pdf, excluding the
  observable and the nuisance parameters, so it can disagree with the `<n>Par` in the card
  name. Read `npars` and `ndof` out of the `chi2` histogram rather than assuming them.
- **`createBinning.py` is only a fallback** and has two defects: it reads a hardcoded path in
  another user's work area, and its `--end` defaults to 1000 GeV, so a fit above 1000 GeV
  would silently get a truncated chi2 binning. Pass `--rebinfile` and `--rebinhist` explicitly
  instead.
- **`.gitignore` swallows `*.txt`, `*.pdf`, `*.png` and `run/`** — new docs or result lists in
  those formats need `git add -f`.
- **`sigwidth == -999`** is the sentinel for "Z' sample" mode: it changes the signal name
  (`mR<mass>`), the POI name and the temp card filenames.
- Shell drivers carry heavily commented-out configuration history. Prefer editing the live
  lines over deleting the record.

# Validation studies

[python/README.md](python/README.md) documents the downstream chain: pseudodata generation →
spurious-signal test → signal-injection linearity → background stability → F-test, with the
toy fits fanned out over HTCondor via `submission/condor_handler.py` + `condor_submit.sub`.
Read it before touching anything under `python/` named `Inject*`, `create*Graph*`,
`SpuriousSignal`, `BackgroundStability` or `FTest`.

# Reproducibility

`tests/repro.py` is a regression harness for the two Run 2 dijet TLA fits (J100 481-3000 GeV,
J50 302-2997 GeV) — the only two analyses this repository currently produces. It cannot prove the
physics is *right*, only that a change did not move it; see
[plans/2026-09-15-reproducibility-lock.md](plans/2026-09-15-reproducibility-lock.md) for the
design and [doc/IMPROVEMENTS.md](doc/IMPROVEMENTS.md) for how it works.

```
python3 tests/repro.py selfcheck            # comparator's own test, no ROOT, instant
python3 tests/repro.py env                  # software pins vs what's actually on disk/CVMFS
python3 tests/repro.py check --quick        # J100 only, ~1-2 min
python3 tests/repro.py check                # both analyses, incl. J50's BumpHunter masking, ~6 min
```

**`record`/`check` need `python3` itself to already have PyROOT importable** — the plain lxplus
system `python3` has this with no setup at all, which is what the driver subprocesses they launch
are sourced against anyway. Run them from a shell that has *not* activated
`pyBumpHunter/pyBH_env` (it carries no ROOT bindings, only the pyBumpHunter egg) or sourced an
ATLAS/lsetup environment that puts a different `python3` first on `$PATH` — either produces a
clear `ERROR: ... has no ROOT module` rather than running.

`check` re-runs the driver(s) with `OUT_DIR` pointed at a scratch directory — `run/` itself is
never touched — and compares the fitted parameters, `minNll`, chi2/p-values, postfit bins and
BumpHunter output against `tests/baseline_J100.json`/`baseline_J50.json`. One exception to that
isolation, inherited rather than introduced: the BumpHunter step writes `bump.png` and
`BH_statistics.png` with bare relative filenames, so any run that reaches it — a real J50 fit or a
`check` — rewrites those two files at the repository root
([KNOWN_ISSUES.md](KNOWN_ISSUES.md) issue 23). Copy them elsewhere if you need to keep them. Floats are compared
within a tolerance (tight: `rtol=1e-6`; p-values: `rtol=1e-5`); most other fields must match
exactly. Run `check --quick` while iterating and the full `check` before committing or merging —
commit only on PASS.

`check --quick` verifies J100's two input hashes and not J50's, which is all a J100-only
comparison depends on; the full `check` verifies all four.

**Baselines are re-cut only when a physics change is intended**, with the reason recorded:
`tests/repro.py record {J100,J50} --force --reason "..."`. Re-cutting to make an unexplained
failure go away defeats the entire point of the harness — if `check` fails, read it in order:
did `env` warn about a version drift, did an input spectrum's hash change, and only then look at
which fitted quantity moved.

**Re-run the fit before re-cutting.** `record` reads its numbers from a run directory but records
the software provenance as it is *now*, so re-cutting from an older `run/…` directory pairs those
numbers with binaries and versions that did not produce them
([KNOWN_ISSUES.md](KNOWN_ISSUES.md) issue 32). `record` prints any failing `env` check whether or
not `--force` is given, but with `--force` it prints them as a warning and writes anyway — read
them before trusting the baseline.

**`global_Pval` will be the first number to move on any LCG bump.** numpy reaches pyBumpHunter by
leaking from the LCG view, and its 10 000 pseudo-experiments are drawn from it; `seed=666` makes
that deterministic for a fixed numpy, but the result is quantised at 1e-4, so any numpy shift
moves it by far more than the p-value tolerance absorbs. A `global_Pval`/`significance` failure
alongside an `env` numpy warning means the stack moved, not the fit — read it as "numpy changed",
not "the fit changed".

`env` also fails if the built `XMLReader`/`quickFit` binaries' SHA-256, or any of the software
pins, no longer match the baseline's provenance. A rebuild legitimately changes the digest even
with identical source and pins — a different compiler, a different machine, or even a
non-reproducible link step can do it — so this is expected to fire after every `install.sh`
re-run, not just after a source change. A deliberate pin bump in `install.sh` fires the pin check
the same way, and that check is what makes a bump visible at all: a re-cloned, rebuilt
sub-framework agrees with `install.sh` by construction, so only the baseline can say the stack has
moved. The fix in either case is the same `record --force --reason "..."` as above, not a flag to
skip the check: silently accepting a rebuilt binary or a bumped pin is exactly the hole these
checks exist to close.

# Links

* [Falk's tutorial recording](https://indico.cern.ch/event/1266089/)
* [Falk's slides](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/FrequentistFramework/-/tree/master/doc?ref_type=heads)
* [JMX unblinding approval](https://indico.cern.ch/event/1607958/)
* [1k slides of notes](https://docs.google.com/presentation/d/10mfb9mbDt6-nh7eKaL4_34VH2Yx_fdRuKtgvNG3sepE/edit?slide=id.p#slide=id.p)
* Code walkthrough slides and transcript: [doc/](doc/)
