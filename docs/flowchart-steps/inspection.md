# Step 7 — Inspecting the data

With the strategy chosen in [step 6](choose-strategy.md), the unblinded data itself is inspected. The procedure differs between the intermediate stages (4%, 20% — [Figure 10.4](../statistics/flowcharts.md#3-inspecting-partially-unblinded-data-figure-104-4-and-20-stages)) and the full dataset ([Figure 10.5](../statistics/flowcharts.md#4-inspecting-the-fully-unblinded-data-figure-105-100-stage)).

## Intermediate stages (4%, 20%)

Run a B-only fit on the partial dataset with the chosen strategy — [step 1 configuration](bkg-only-fit.md) with:

```bash
pars=<chosen Npar word>          # e.g. eight — NOT Npar+2
rangelow=<chosen range start>
datafile=<partial-unblinding histogram file>
datahist=mjj
dosignal=0
maskthreshold=0.01
```

Then follow the outcomes:

- **Fit passes immediately** and the residuals (`postFit.pdf`, `python/PlotResiduals.py`) show only statistical scatter → with convener approval, proceed to the next unblinding phase.
- **Fit fails once** → the automatic BumpHunter masking kicks in. Whatever the masked refit gives, inspect the full-range BumpHunter $p$-value (printed by `python/FindBHWindow.py`, stored in `BHresults.json`) **and** check for jet-calibration or selection features that could have triggered the exclusion.
- **Masked fit fails too** → the feature must be understood (calibration, selection bias, turn-on) before unblinding proceeds.

!!! warning
    Unblinding proceeds **only after** any feature introduced by the calibration or analysis selection is understood — a passing masked fit is not by itself a green light.

## Full dataset (100%)

First re-run the *validation* and *choice* flowcharts (steps 1–6) on the full dataset without modification. Then two independent workflows:

### BumpHunter interpretation (B-only)

Same B-only fit configuration as above with `datafile=data/data23_histos.root`, `datahist=mjj`:

- fit passes → data consistent with the background-only hypothesis;
- fails once → automatic ≤3-bin BumpHunter mask, refit;
- fails twice → check calibration features; if unresolved there is *no clear BumpHunter interpretation* — consult the conveners;
- after a successful masked fit, test the **global BumpHunter $p$-value**: $p \le 0.05$ → check calibration features, then quantify the discovery significance; in all cases check what the mask hid before reporting anything.

### Gaussian/$Z'$ interpretation (S+B)

S+B fits for **all** signal hypotheses, then limits — the configuration is described in [step 8](limits.md). Per the flowchart: one BumpHunter-masked retry on a failed S+B fit; a second failure means the S+B model failed to describe the data. A statistically significant fitted yield triggers the calibration-feature checks before any significance is quoted.

## Tools for eyeballing the spectrum

| Tool | Purpose |
|---|---|
| `python/plotPostFit.py -i <PostFit>.root -o out.pdf` | data/fit overlay + ratio |
| `root -l -q 'plot_postfit.cpp("<folder>", "<pars>")'` | ATLAS-style post-fit + residual plot |
| `python/PlotResiduals.py` | residual significance distributions |
| `python/plotChi2Ndof.py`, `python/plotChi2Ndof2D.py` | χ²/ndof summaries over many fits |
| `plot_edm.py` (run automatically) | minimiser EDM trace |
