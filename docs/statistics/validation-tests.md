# Validation tests

A candidate fit strategy $(N_\text{par}, \text{range})$ must pass all of the following tests on pseudo-data before it may be used on data. Each test is run **per signal hypothesis** (signal type — Gaussian or $Z'$ —, mass and width) over typically **100 statistically independent toys**. How to actually run them is described step by step in [Running the flowchart](../flowchart-steps/index.md).

## Background-only fit on pseudo-data

The most basic check: an $N_\text{par}$ fit (note: *not* $N_\text{par}+2$) on each pseudo-data toy must succeed, i.e. have a valid $p(\chi^2)$ for the large majority of toys and stable minimisation.

## Spurious signal (SS) test

Detects signal-retrieval bias when **no signal is present**. S+B fits are performed on the 100 background-only toys and the fitted signal yield $S$ is recorded per toy.

$$
|S_\text{spur}| < 0.5\,\sigma_\text{fit}
$$

where $S_\text{spur}$ is the **mean** of the retrieved-yield distribution over the toys and $\sigma_\text{fit}$ its **RMS**. A significant deviation from zero means the background function "manufactures" signal.

Notes from the analysis:

- The test is performed both with **Gaussian templates** (width set per mass point to the $m_{jj}$ resolution) and with the **parametrised $Z'$ (DSCB) template**.
- The result is sensitive to procedural details: pseudo-data must come from an $N_\text{par}+2$ template ($N_\text{par}+1$ gives notably worse results), and the minimiser settings matter.
- 100 toys are sufficient — 1000-toy cross-checks give more Gaussian-looking distributions but essentially identical means/RMS.
- Subject to convener agreement, a *small* number of configurations with $0.5 < |S_\text{spur}|/\sigma_\text{fit} < 1$ may be tolerated.

Implementation: S+B fits on toys via [HTCondor](../condor.md); collection with `python/createExtractionGraph.py`; final plot with `python/SpuriousSignal.py`.

## Signal injection and linearity test (SILT)

Detects retrieval bias when **signal is present**. A signal of known yield $S_\text{inj}$ is injected into the background template *before* the Poisson fluctuation of each toy; injections are done at several amplitudes (in units of $\sqrt{B}$, with $B$ the background within the FWHM around the peak). The criterion is

$$
S_\text{spur} \;=\; S_\text{fit} - S_\text{inj} \;<\; 0.5\,\sigma_\text{fit},
$$

and the fitted yield must scale **linearly** with the injected yield. The $0.5\,\sigma_\text{fit}$ threshold (instead of the conventional $0.1\,S_\text{fit}$) follows the Run 2 TLA, appropriate when the injected signal is comparable to the expected limit. Wider signals ($\gtrsim 15\%$ relative width) interact pathologically with the dijet function's degrees of freedom — the functional-fit method is only recommended below that.

Implementation: `python/InjectGaussian.py` / `python/InjectZprime.py` (+ the `inject_*.sh` loops), toy fits via HTCondor, collection with `python/createExtractionGraph_signalInjection.py`, plots with `python/plotExtractionGraph.py`.

## Background stability test

Checks that the **background component** of the S+B fit is insensitive to the injected signal. For each injected toy, the post-fit background is compared with the original (unfluctuated) background template; the deviation must satisfy

$$
|\Delta B| < 3\,\sigma_\text{stat}
$$

with any localised distortion around the injected mass indicating signal leakage into the background model.

Implementation: `python/BackgroundStability.py` on the S+B toy fits from the signal-injection step.

## $F$-test

Used when **several $N_\text{par}$ values pass all tests for the same fit range**: choose the lowest-complexity function that still describes the data. For a "null" fit with $n_0$ parameters and an "alternate" fit with $n_\text{alt} > n_0$:

$$
F = \frac{\left(\chi^2_0 - \chi^2_\text{alt}\right) / \left(n_\text{alt} - n_0\right)}
         {\chi^2_\text{alt} / \left(N_\text{bins} - n_\text{alt}\right)}
$$

with $p(F)$ from the $F$-distribution. **$p(F) < 0.05$** means the extra parameter improves the fit significantly, so the lower-$N_\text{par}$ option is discarded; otherwise the simpler function is kept. The test is performed on unblinded data and is insensitive to localised structures.

Implementation: `python/FTest.py`, comparing the `PostFit_*.root` outputs of B-only fits with successive $N_\text{par}$.

## Summary of criteria

| Test | Criterion | Tool |
|---|---|---|
| B-only fit | $p(\chi^2) > 0.01$ and numerically stable | `run_anaFit.py` |
| Spurious signal | $\lvert S_\text{spur}\rvert < 0.5\,\sigma_\text{fit}$ | `SpuriousSignal.py` |
| Signal injection / linearity | $\lvert S_\text{fit} - S_\text{inj}\rvert < 0.5\,\sigma_\text{fit}$, linear response | `plotExtractionGraph.py` |
| Background stability | deviation $< 3\,\sigma_\text{stat}$ | `BackgroundStability.py` |
| $F$-test (strategy choice) | keep lowest $N_\text{par}$ with $p(F) \ge 0.05$ | `FTest.py` |
| BumpHunter (full range) | global $p > 0.05$ | `FindBHWindow.py` |
