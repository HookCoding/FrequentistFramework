# FrequentistFramework

ATLAS statistical-fit framework for dijet / TLA bump-hunt analyses. It wraps three CERN
GitLab C++ sub-frameworks ([xmlAnaWSBuilder](https://github.com/tofitsch/xmlAnaWSBuilder),
[quickFit](https://github.com/tofitsch/quickFit),
[workspaceCombiner](https://github.com/tofitsch/workspaceCombiner)) plus
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
| pyBumpHunter venv | Python 3.9.12 from LCG_105; numpy, matplotlib, scipy, uproot (**unpinned**) | `scripts/install_pyBumpHunter.sh` |

pyBumpHunter lives in its own virtualenv (`pyBumpHunter/pyBH_env`) because its numpy conflicts
with the CVMFS one; `run_anaFit.py` activates it inline for the BumpHunter step only.

The results recorded in [CHANGELOG.md](CHANGELOG.md) were produced with LCG_102a. The
untracked `requirements.txt` is not a usable pip input — do not `pip install -r` it.

`install.sh` and `setup.sh` must be **sourced**, not executed — they `cd` around and export
`$_DIRFIT`, `$_DIRXMLWSBUILDER` and `$_DIRCOMB`. All commands must be run **from the
repository root**; the setup scripts abort if `xmlAnaWSBuilder/` and `quickFit/` are not in
`$PWD`.

# Run

Output defaults to `<repo>/run/`; every output lands under
`$out_dir/run_<rangelow>_<rangehigh>_<n>Par/`. Override with `OUT_DIR=/path/to/eos/area` for
toy studies fanned out over HTCondor — AFS home quotas are too small for hundreds of runs.

```
. scripts/run_anaFit_run2.sh    # Run 2 dijet TLA  (13 TeV)
```

Other drivers: `scripts/run_nloFit.sh` (NLO-template fit), `scripts/run_anaFit_syst.sh`,
`scripts/run_anaFitLoop.sh`, `scripts/run_swiftFit.py`.

# Configuration

|  | Run 2 dijet TLA |
|---|---|
| Driver | `scripts/run_anaFit_run2.sh` |
| √s | 13 TeV |
| Fit range | 481 – 3000 GeV |
| Bins in range | 2519 (1 GeV) |
| Background parameters | six |
| Channel name | `J100yStar06` |
| Data file | `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root` |
| Data histogram | `hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj` |
| Cards | `config/dijetTLA/` |
| Rebinning | `Input/data/dijetTLA/fullRun2TLAJ100mjj.root` (57 bins, 481–2997) |

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
- **Sub-frameworks are both git submodules and gitignored.** `install.sh` clones them at
  pinned SHAs; never commit into them from here.
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

# Links

* [Falk's tutorial recording](https://indico.cern.ch/event/1266089/)
* [Falk's slides](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/FrequentistFramework/-/tree/master/doc?ref_type=heads)
* [JMX unblinding approval](https://indico.cern.ch/event/1607958/)
* [1k slides of notes](https://docs.google.com/presentation/d/10mfb9mbDt6-nh7eKaL4_34VH2Yx_fdRuKtgvNG3sepE/edit?slide=id.p#slide=id.p)
* Code walkthrough slides and transcript: [doc/](doc/)
