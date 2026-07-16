# Step 5 — Background stability test

Checks that the background component of the S+B fit is not distorted by injected signal: for each toy, the post-fit background is compared with the original unfluctuated template, requiring deviations below $3\,\sigma_\text{stat}$ (see [test definition](../statistics/validation-tests.md#background-stability-test)).

## Inputs

Reuses the S+B fits on **injected** toys from [step 4](signal-injection.md) — no new fits are needed. You need:

- the list of per-toy `PostFit` outputs (`Run3TLA_bkgonly/postfit` histograms) of the injected S+B fits,
- the unfluctuated background template (`unfluctuated` histogram in the pseudo-data file from [step 2](pseudodata.md)).

## Command

```bash
# one list per (mass, width, amplitude) working point
find <outdir>/injected/pseudodatafits_eightPar_injected_mean400_width8_amp3/fit_*/PostFit_anaFit_*.root \
     > injected_paths_mean400_width8_amp3_BS.txt

python python/BackgroundStability.py \
    --toyfiles injected_paths_mean400_width8_amp3_BS.txt \
    --toyhist  Run3TLA_bkgonly/postfit \
    --reffile  <pseudo-data file from step 2> \
    --refhist  unfluctuated \
    --outfile  backgroundStability_eightPar_mean400_width8_amp3.pdf
```

The wrapper `python/runBackgroundStability.sh` loops this over working points.

## Interpretation

The plot overlays, per toy, the ratio of the fitted background to the reference template:

- the spread must be consistent with the **statistical fluctuations** of the toys (continuous band, no outliers),
- a systematic distortion **around the injected mass** indicates the background function absorbing signal — the residual differences may only come from statistics, the one-parameter difference between the B and S+B fits, or (the failure mode) the signal leaking into the background shape,
- **criterion:** deviation $< 3\,\sigma_\text{stat}$ everywhere.

This test also helps diagnose *why* a strategy failed SS/SILT: localized instabilities show up here as coherent toy-by-toy distortions.

## Pass / fail

Failure counts as "any failure" in the flowchart's test box: discard the $N_\text{par}$, increment and repeat [steps 3–5](spurious-signal.md).
