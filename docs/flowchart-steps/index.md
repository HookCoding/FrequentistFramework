# Running the flowchart — overview

This section maps every box of the [unblinding flowcharts](../statistics/flowcharts.md) onto concrete framework commands and tells you **exactly what to change** in the scripts for each step. All steps are configurations of the same `run_anaFit.sh` → `run_anaFit.py` pipeline described in [Running a fit](../running.md).

## Step ↔ tool map

| Flowchart box | Doc page | Main tools |
|---|---|---|
| B-only fit ($N_\text{par}$ or $N_\text{par}{+}2$) on data, incl. BumpHunter masking | [1. Background-only fit](bkg-only-fit.md) | `run_anaFit.sh`, `run_anaFit.py`, `FindBHWindow.py` |
| Make pseudo-data template + toys | [2. Pseudo-data generation](pseudodata.md) | `generatePseudoData.py` |
| Spurious signal test | [3. Spurious signal test](spurious-signal.md) | condor + `createExtractionGraph.py`, `SpuriousSignal.py` |
| Signal injection + linearity | [4. Signal injection test](signal-injection.md) | `InjectGaussian.py`/`InjectZprime.py`, `createExtractionGraph_signalInjection.py`, `plotExtractionGraph.py` |
| Background stability | [5. Background stability](background-stability.md) | `BackgroundStability.py` |
| Choosing the strategy ($F$-test) | [6. Choosing the fit strategy](choose-strategy.md) | `FTest.py` |
| Inspect (partially/fully) unblinded data | [7. Inspecting the data](inspection.md) | `run_anaFit.sh`, `plotPostFit.py`, `PlotResiduals.py` |
| S+B fits, limits, interpretations | [8. S+B fits and limits](limits.md) | `run_anaFit.sh` (`dosignal`/`dolimit`), `quickLimit`, `plotLimits.py` |

## The typical loop at one unblinding stage

For a given unblinded dataset (4%, 20% or 100%):

1. **Scan B-only fits** over $(N_\text{par}{+}2, \text{range})$ on data until one passes — [step 1](bkg-only-fit.md). This is the pseudo-data *template* fit, so `pars` = strategy $N_\text{par}$ + 2.
2. **Generate 100 toys** from the passing template — [step 2](pseudodata.md).
3. For each surviving strategy $N_\text{par}$ and each signal hypothesis, run the toy fits on condor and evaluate **SS** ([step 3](spurious-signal.md)), **SILT** ([step 4](signal-injection.md)) and **background stability** ([step 5](background-stability.md)).
4. **Choose** among the passing strategies — [step 6](choose-strategy.md).
5. **Inspect the data** with the chosen strategy — [step 7](inspection.md).
6. At the 100% stage: run the **interpretations and limits** — [step 8](limits.md).

## Inputs per unblinding stage

| Stage | Dataset | Typical `datafile` / `datahist` |
|---|---|---|
| 4% (≈0.93 fb⁻¹) | runs 451866, 452202 | partial-unblinding histograms (EOS, `tla-ntuple-analysis` outputs) |
| 20% (≈5 fb⁻¹) | PU20 run list | partial-unblinding histograms (EOS) |
| 100% (25 fb⁻¹) | full 2023 TLA stream | `data/data23_histos.root` / `mjj` (shipped with the repo) |

The signal-systematics JSON files for the parametrised $Z'$ model (per mass point) come from `tla-ntuple-analysis`, e.g.

```
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp<MASS>_gASp1_qContentUDSC/signalUncertainty_interpolated.json
```

and the corresponding $Z'$ MC shape histograms live in `data/zprime_shapes/`.

!!! warning "Fail = $p(\chi^2) \le 0.01$ or unstable"
    Everywhere in this section "the fit passes" means the driver printed `p(chi2) threshold passed` **and** the minimisation was healthy — check `quickFitLog_*.log` (minimiser status, EDM) and `edm_*.pdf`, and make sure no parameter is pinned at its range boundary (enlarge the ranges in the background template if it is).
