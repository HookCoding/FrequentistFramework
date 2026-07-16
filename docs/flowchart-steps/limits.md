# Step 8 — S+B fits and limit setting

The final phase of the [full-unblinding flowchart](../statistics/flowcharts.md#4-inspecting-the-fully-unblinded-data-figure-105-100-stage): signal-plus-background fits for every signal hypothesis and, in the absence of a significant excess, 95% CL CL$_\text{s}$ upper limits.

## Gaussian signal

In `scripts/run_anaFit.sh` set:

```bash
pars=<chosen Npar word>          # the chosen fit strategy
rangelow=<chosen range start>
dosignal=1                       # S+B fit; POI = nsig_mean<M>_width<W>
dolimit=1                        # run quickLimit after a successful fit
sigmean=400                      # loop over the mass grid
sigwidth=8                       # loop over widths (% of mass); <= mjj resolution ... 15%
datafile=data/data23_histos.root
datahist=mjj
signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
outputfile=${folder}/FitResult_anaFit_${pars}Par_mean${sigmean}_width${sigwidth}.root
```

and loop `sigmean` (and `sigwidth`) over the signal grid, e.g. `for sigmean in 150 160 180 200 225 250 300 350 400 ...`. A minimal standalone scan over an existing workspace is sketched in `scripts/splusbfits.sh`.

## $Z'$ parametrised signal

Switch the signal model to the DSCB parametrisation with per-mass systematics:

```bash
sigwidth=-1                      # width taken from the DSCB parametrisation
signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA_zprime_parametrized.template
categoryfile=config/dijetisrTLA/category_dijetisrTLA_zprime_parametrized.template
sysfile=/eos/user/.../MGPy8EG_S1_qqa_Ph25_mRp${sigmean}_gASp1_qContentUDSC/signalUncertainty_interpolated.json
```

and **uncomment the `--sysfile $sysfile` argument** in the `run_anaFit.py` call. The JSON (produced by `tla-ntuple-analysis`, interpolatable between mass points with `python/interpolateSignalUncertainty.py` / `python/InterpolateZPrime.py`) provides the nominal DSCB parameters and the `MAG_SCALE_*` / `MAG_RESOLUTION_*` systematic magnitudes; any systematic not present in the JSON is automatically set to zero.

For fits to the actual $Z'$ MC shape histograms (`data/zprime_shapes/`), use `sigwidth=-999` — the POI becomes `nsig_mR<mass>`.

## What runs

1. `quickFit` performs the S+B fit with `-p nsig_<signame>`; the fitted yield and its error land in `FitParameters_*.root`.
2. Failed S+B fits get **one** automatic BumpHunter-masked retry (same machinery as [step 1](bkg-only-fit.md)); a second failure terminates the procedure for that hypothesis ("S+B model failed to describe the data").
3. With `dolimit=1` and a successful fit, `quickLimit` scans the POI:

    ```
    quickLimit -f <ws> -d combData -p nsig_<signame> --checkWS 1 \
               --initialGuess 100000 --minTolerance 1E-06 --muScanPoints 20 \
               --minStrat 2 --nllOffset 0 --GKIntegrator 1 -o Limits_....root
    ```

    producing observed and expected (±1σ, ±2σ) CL$_\text{s}$ limits on the signal yield.

!!! warning
    `quickLimit` does not support masked (`BlindRange`) workspaces — limits are only run when the unmasked fit passed the $p(\chi^2)$ gate (`dolimit` is internally conditioned on it).

## Plotting and interpretation

```bash
python python/plotLimits.py <Limits files...> -b      # cross-section limits vs mass
python python/plotLimits_joined.py ...                # combined/overlay versions
```

(Adjust the `lumi` constant at the top of the script for the dataset.) Toy-based cross-checks of the limit distribution can be plotted with `python/PlotToyLimitsDistribution.py`, exclusion-coverage checks with `python/plotFalseExclusion.py` / `plotFalseExclusionCandles.py` and `python/createCoverageGraph.py`.

### From yields to $g_q$

Cross-section limits translate to the $Z'$ coupling via

$$
g_q^\text{lim} = g_q^\text{ref}\,\sqrt{\frac{N_\text{lim}}{N_\text{ref}\times 1.25}},
\qquad N_\text{ref} = \mathcal{L}\,\sigma\,BR\,\mathcal{A}\,\epsilon,
$$

(the 1.25 accounts for the unsimulated $b\bar b$ decays; valid in the narrow-width approximation, $g_q \lesssim 0.5$).

### Expected limits before full unblinding

Two equivalent proxies (note, Section 11.2):

- scale the partial-dataset limit by luminosity: $\tilde N_\text{lim}(25.5\,\text{fb}^{-1}) = N_\text{lim}(0.927\,\text{fb}^{-1}) \times \sqrt{25.5/0.927}$, or
- up-scale the background-only template to full luminosity (`generatePseudoData.py --scaling <sf>`) and run the full limit machinery on it.
