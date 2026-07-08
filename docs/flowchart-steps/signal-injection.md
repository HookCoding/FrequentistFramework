# Step 4 — Signal injection and linearity test (SILT)

Inject known signal yields into the background template, refit, and check $|S_\text{fit} - S_\text{inj}| < 0.5\,\sigma_\text{fit}$ and linearity (see [test definition](../statistics/validation-tests.md#signal-injection-and-linearity-test-silt)).

## 1. Inject signal into the toys

The injection happens **before** the Poisson fluctuation, on the pseudo-data file from [step 2](pseudodata.md).

=== "Gaussian signal"

    ```bash
    python python/InjectGaussian.py \
        --infile   <pseudo-data file from step 2> \
        --histname pseudodata \
        --sigmean  400 --sigwidth 8 --sigamp 3 \
        --firsttoy 0 --lasttoy 99
    ```

    `--sigamp` is the injected significance in units of $\sqrt{B}$, with $B$ the background within the FWHM ($\pm1.18\,\sigma$) around the peak. For the linearity scan loop over amplitudes (e.g. 0–5); `python/inject_gaussians.sh` prints the full mass × width × amplitude loop used in the analysis.

=== "Z′ signal (recommended: MC histogram sampling)"

    ```bash
    python python/InjectZprime.py \
        --infile   <pseudo-data file from step 2> \
        --histname pseudodata \
        --sigfile  <...>/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC.root \
        --sigfile_dscb <...>/signalUncertainty_interpolated.json \
        --sighist  mjj_yStar_cut_nominal \
        --sigamp 3 --firsttoy 0 --lasttoy 99
    ```

    Sampling from the MC histogram (with the DSCB fit only used to define the sampling range) avoids the bias from the DSCB's slowly decaying tails; this was the method chosen for Run 3. Passing only `--sigfile <json>` instead samples from the pure DSCB shape. Wrapper loops: `python/inject_zprime.sh`, `python/inject_zprime_dscblimits.sh`, `python/inject_dscb.sh`.

The output file contains injected toys named after the injection parameters (`..._mean400_width8_amp3`).

## 2. Fit the injected toys

Same [HTCondor setup as the SS test](spurious-signal.md), with the *injected* pseudo-data as input — in `submission/condor_script.sh` switch to the "signal injected" block:

```bash
datafile=<injected pseudo-data file>
outputfile=${folder}/FitResult_anaFit_${pars_BS}Par_pseudodata${p}_injected_mean${si_mean}_width${si_width}_amp${si_amp}_fit_mean${sigmean}_width${sigwidth}.root
```

The fitted signal hypothesis (`-m`, `-w`) must match the injected one; `condor_handler.py` generates the argument list over masses, widths, amplitudes and toys (`-M`, `-W`, `-A` carry the injection parameters).

## 3. Collect and plot

```bash
# list the FitParameters files of all injected fits
find <outdir>/injected/pseudodatafits_*/fit_*_injected_*/FitParameters_anaFit_*_pseudodata_*.root \
     > injected_paths_eightPar.txt

python python/createExtractionGraph_signalInjection.py injected_paths_eightPar.txt \
     --outfile extractionGraphs_injection_eightPar.root

python python/plotExtractionGraph.py extractionGraphs_injection_eightPar.root
```

The result is the SILT plot: fitted yield vs injected yield (in $\sqrt{B}$ units) per signal hypothesis, with the bottom panel showing $|S_\text{spur}|/\sigma_\text{fit}$ against the $\pm 0.5$ criterion.

## Pass / fail

- **Pass:** response linear and within $\pm 0.5\,\sigma_\text{fit}$ at all amplitudes (small deviations at very large injections are tolerated; isolated exceedances may be accepted with convener agreement).
- **Fail:** same escalation as the SS test — increment $N_\text{par}$, then restrict range / drop the signal point.
- Wide signals (relative width ≳ 15%) are expected to perform worst; the method is not recommended beyond that width.
