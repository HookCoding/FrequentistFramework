# Step 6 — Choosing the fit strategy

When [steps 1–5](index.md) leave more than one validated $(N_\text{par}, \text{range})$ pair, the [choice flowchart](../statistics/flowcharts.md#2-choosing-a-fit-strategy-figure-102) picks one:

1. **Prefer the largest fit range.** If a single strategy has it, done.
2. Otherwise, among the strategies sharing the largest range, run B-only fits on data for each $N_\text{par}$ (smallest first, with the usual one-shot BumpHunter retry) and use the **$F$-test** to keep the lowest $N_\text{par}$ that is not significantly improved by adding parameters.

## Running the B-only fits

One fit per $N_\text{par}$ candidate, exactly as in [step 1](bkg-only-fit.md) but with `pars` set to the strategy value (not +2), e.g.

```bash
for pars in five six seven eight    # candidates sharing the chosen range
```

Each produces `${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root` in its own `run_<lo>_<hi>_<pars>Par` folder.

## Running the F-test

`python/FTest.py` takes the `PostFit` files **ordered from highest to lowest $N_\text{par}$** and computes $F$ and $p(F)$ for each adjacent pair:

```bash
python python/FTest.py \
    ${out_dir}/run_125_1000_eightPar/PostFit_anaFit_eightPar_bkgOnly.root \
    ${out_dir}/run_125_1000_sevenPar/PostFit_anaFit_sevenPar_bkgOnly.root \
    ${out_dir}/run_125_1000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root \
    ${out_dir}/run_125_1000_fivePar/PostFit_anaFit_fivePar_bkgOnly.root
```

Useful options: `--output <name>` for the plot files, `--noftest` to only draw the residual overlays, `--zerochi2` when fitting unfluctuated templates.

The output plot overlays the fit residuals of all candidates and prints, per step in complexity, $\chi^2/n$ and $p(F_{n\to n+1})$.

## Decision rule

$$
p(F) < 0.05 \implies \text{the additional parameter significantly improves the fit — discard the simpler function.}
$$

Walk up from the smallest $N_\text{par}$: the chosen strategy is the first one whose comparison with the next-larger function gives $p(F) \ge 0.05$.

!!! note
    The $F$-test only compares fits **with the same range and binning** ($N_\text{bins}$ enters the formula). Strategies with different ranges are ranked by the range-first rule above, never by $F$-test.

The resulting $(N_\text{par}, \text{range})$ is the analysis fit strategy for this unblinding stage — everything downstream ([inspection](inspection.md), [limits](limits.md)) uses it.
