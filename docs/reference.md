# Reference

## Repository layout

```
FrequentistFramework/
├── install.sh                 # one-time install (clones + builds sub-packages)
├── setup.sh                   # per-shell environment setup
├── rebuild_pkgs.sh            # rebuild C++ packages (CMake >= 4 workaround)
├── scripts/                   # run wrappers
├── python/                    # drivers, tests, plotting
├── config/dijetisrTLA/        # XML template cards for this analysis
├── config/{dijetTLA,...}      # cards of earlier/other analyses (Run 2 TLA, bbyy, ...)
├── data/                      # data23_histos.root, zprime_shapes/
├── Input/data/dijetisrTLA/    # resolution binning + auxiliary inputs
├── submission/                # HTCondor machinery
├── xmlAnaWSBuilder/           # sub-package (workspace building)
├── quickFit/                  # sub-package (fits, quickLimit)
├── workspaceCombiner/         # sub-package
├── pyBumpHunter/              # sub-package (+ pyBH_env virtualenv)
├── atlasstyle-00-04-02/       # ATLAS plotting style macros
└── doc/                       # code walk-through slides
```

## Key scripts (`scripts/`)

| Script | Purpose |
|---|---|
| `run_anaFit.sh` | **Main entry point** — configure and run one fit chain ([docs](running.md)) |
| `run_anaFit_flowchart.sh` | B-only fit + pseudo-data generation in one go (Run 2 dijet TLA example of the flowchart start) |
| `run_anaFitLoop.sh`, `run_anaFit_syst.sh`, `run_anaFit_zprime.py` | loop/systematics/$Z'$ variants of the wrapper |
| `setup_buildAndFit.sh` | environment setup used inside the run scripts |
| `splusbfits.sh` | quickFit S+B scan over an existing workspace |
| `run_nloFit*.sh`, `run_buildAndFit_*_swift.sh`, `run_swiftFit.py` | alternative fitters (NLO function, SWiFt) — not part of the baseline procedure |
| `install_*.sh` | install helpers used by `install.sh` |
| `condor_handler.py` | condor job-list generator (same as `submission/`) |

## Key Python tools (`python/`)

| Tool | Role in the procedure |
|---|---|
| `run_anaFit.py` | build → prefit → fit → extract → (BH mask) → (limit) driver |
| `PreFit.py`, `PreFitWS.py`, `pfe.py` | ROOT prefit to seed parameters and `nbkg` |
| `ExtractPostfitFromWS.py`, `ExtractTH1FromWS.py`, `ExtractFitParameters.py` | post-fit histograms / parameter extraction, $p(\chi^2)$ |
| `createBinning.py` | derive the $m_{jj}$ resolution binning from `rangelow` |
| `FindBHWindow.py` | pyBumpHunter window search + global $p$-value |
| `generatePseudoData.py` | Poisson toys from a background template |
| `InjectGaussian.py`, `InjectZprime.py`, `inject_*.sh` | signal injection into toys |
| `createExtractionGraph.py`, `createExtractionGraph_signalInjection.py` | aggregate fitted yields over toys |
| `SpuriousSignal.py` | SS summary plot ($S_\text{spur}$, $\sigma_\text{fit}$, ratio panel) |
| `plotExtractionGraph.py` | SILT linearity plot |
| `BackgroundStability.py`, `runBackgroundStability.sh` | background-stability comparison |
| `FTest.py` | $F$-test between $N_\text{par}$ options |
| `plotPostFit.py`, `PlotResiduals.py`, `plotChi2Ndof*.py`, `getChi2Distribution.py` | fit-quality plots |
| `plotLimits.py`, `plotLimits_joined.py`, `PlotToyLimitsDistribution.py` | limit plots |
| `plotFalseExclusion*.py`, `createCoverageGraph.py`, `createToleranceGraph.py` | coverage / false-exclusion studies |
| `fitSignalUncertainty.py`, `interpolateSignalUncertainty.py`, `InterpolateZPrime.py` | DSCB signal parametrisation & interpolation between mass points |
| `rebin.py`, `color.py`, `simple_analysis.py`, `simple_bkg_fit.py` | utilities / standalone checks |

## XML template cards (`config/dijetisrTLA/`)

| Card | Placeholders replaced by `run_anaFit.py` |
|---|---|
| `dijetisrTLA.template` (top) | `CATEGORYFILE`, `OUTPUTFILE`, `SIGNAME` |
| `category_dijetisrTLA.template` | `DATAFILE`, `DATAHIST`, `RANGELOW`, `RANGEHIGH`, `BINS`, `NBKG`, `NSIG`, `SIGNALFILE`, `BACKGROUNDFILE`, `SIGNAME` |
| `background_dijetisrTLA_<N>Par.template` (`threePar`–`tenPar`) | `PAR1`…`PARn` (prefit seeds; ranges parsed from `[PARi, lo, hi]`) |
| `signal/signal_dijetisrTLA.template` | `SIGNAME`, `SIGMEAN`, `SIGWIDTH` (Gaussian) |
| `signal/signal_dijetisrTLA_zprime_parametrized.template` + `category_..._zprime_parametrized.template` | DSCB nominals `NOMINAL_*` and systematics `MAG_SCALE_*`, `MAG_RESOLUTION_*` from the `--sysfile` JSON |
| `noSyst/*` | systematics-free $Z'$ variants |

The masked variants (`*_masked.xml`, `Blind="true"`, `BlindRange`) are generated automatically at run time.

## Known gotchas

!!! warning "Hard-coded paths"
    - `python/createBinning.py` reads the resolution fit from an absolute path (`.../tlafits/FrequentistFramework/Input/data/dijetisrTLA/resolutionFits.root`). Pre-generated binnings for common `rangelow` values are shipped in `Input/data/dijetisrTLA/` (e.g. `mjjResolutionBinning_125.root`); for a *new* `rangelow`, fix the path in `createBinning.py` first.
    - `submission/condor_script.sh` and `condor_handler.py` hard-code `localdir` — see [Batch submission](condor.md).
    - Several commented example paths in `scripts/run_anaFit.sh` point to `/eos/user/l/lbazzano/...`; they require that user's EOS to be accessible and are kept only as provenance of past studies.

!!! warning "Sourcing and CWD"
    All run scripts must be **sourced from the repository root**; binaries and cards are addressed with relative paths.

!!! warning "sigwidth magic values"
    `--sigwidth` in `run_anaFit.py`: positive = Gaussian width in % of mass; `-1` = width from the DSCB parametrisation (with `--sysfile`); `-999` = $Z'$ MC-sample mode (POI `nsig_mR<mass>`).

## Statistical procedure source

The procedure implemented here is defined in the analysis note **ANA-EXOT-2022-41-INT1** — *Search for low mass di-jet resonances produced in association with an initial-state photon using the Trigger-Level Analysis workflow in early Run 3*:

- Chapter 8.2 — background estimation strategy and validation tests,
- Chapter 10 — unblinding strategy and flowcharts (Figures 10.1–10.5),
- Chapter 11 — statistical analysis, likelihood and limit setting.
