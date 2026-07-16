# Statistical procedure — overview

This section summarises the statistical procedure of the dijet+ISR TLA as documented in the analysis note **ANA-EXOT-2022-41-INT1** (Chapters 8, 10, 11), and points to the framework machinery that implements each ingredient.

## Background model: the dijet function

The background $m_{jj}$ spectrum is modelled by a smooth $N$-parameter *dijet function* fitted directly to data:

$$
f(x) \;=\; p_1\,(1-x)^{p_2}\; x^{\;\sum_{i=3}^{N} p_i \,\log(x)^{\,i-3}},
\qquad x \equiv m_{jj}/\sqrt{s},
$$

where $N$ ("$N_\text{par}$") is varied between 4 and 8 to make the shape flexible enough to describe the spectrum without absorbing a potential signal. The XML implementations live in `config/dijetisrTLA/background_dijetisrTLA_<N>Par.template` (available from `threePar` to `tenPar` — the higher orders are used for pseudo-data templates).

A function that is too **rigid** (low $N$) cannot describe the spectrum; one that is too **flexible** (high $N$) can swallow signal or fail to converge. The whole point of the [unblinding flowchart](flowcharts.md) is to select and validate the pair *(fit range, $N_\text{par}$)* — the **fit strategy** — on data and pseudo-data before any interpretation.

## Likelihood

The baseline binned likelihood

$$
-\log \mathcal{L} = -\sum_i^{\text{bins}} \log \mathcal{P}\!\left(N_i,\, n_i(\vec\theta)\right) \;-\; \sum_k^{\text{syst}} \log f(\theta_k, \tilde\theta_k) + \text{const}
$$

is replaced by its asymptotic $\chi^2$ approximation, valid because of the very large per-bin event counts of a TLA:

$$
-\log \mathcal{L} \;\approx\; \tfrac{1}{2}\chi^2 \;-\; \sum_k^{\text{syst}} \log f(\theta_k, \tilde\theta_k) + \text{const}.
$$

This is why every fit in the framework runs `quickFit` with `--chi2fit 1 --poissonerror 1` (see [Running a fit](../running.md)). The approach follows the Run 2 dijet TLA, where full-NLL fits hit machine-precision problems at TLA statistics.

**Fit success criterion:** throughout the procedure a fit is considered *failed* if $p(\chi^2) \le 0.01$ **or** the minimisation is numerically unstable (minimiser status, EDM, parameters pinned at their bounds — check `quickFitLog_*.log` and `edm_*.pdf`; the bounding box must be enlarged if parameters sit on it).

## Staged unblinding

Because the fit-strategy validation relies on pseudo-data constructed from real data (up-scaling a small dataset was shown to bias the spurious-signal test), the analysis unblinds in stages, and **the full validation is repeated at every stage**:

1. **4% unblinded** — $\mathcal{L} = 1$ fb⁻¹ (runs 451866, 452202; 0.918–0.927 fb⁻¹),
2. **20% unblinded** — $\mathcal{L} = 5$ fb⁻¹,
3. **100% unblinded** — $\mathcal{L} = 25$ fb⁻¹ (`data/data23_histos.root`).

No luminosity up-scaling is applied when generating pseudo-data: the toys are Poisson fluctuations of an $(N_\text{par}{+}2)$-parameter fit to the currently unblinded dataset at its *actual* statistics.

## BumpHunter

[pyBumpHunter](https://github.com/scikit-hep/pyBumpHunter) is used in two roles:

- **Window exclusion (masking):** when a B-only fit fails the $p$-value criterion, the most discrepant window — **at most three $m_{jj}$ resolution bins wide** — is masked and the fit retried. The width cap avoids excluding wide regions where the search has unique sensitivity. The resolution binning is re-derived from the start of the fit range whenever the range changes (`python/createBinning.py`).
- **Full-range hypothesis test:** the global BumpHunter $p$-value quantifies whether the data is consistent with the background-only hypothesis ($p > 0.05$).

For the 20% and 100% stages, BumpHunter masking during pseudo-data generation is applied **only when the B-only fit fails** the $p$-value test (applying it unconditionally was found to degrade the B-only $p$-value).

## Interpretations and limits

In the absence of a significant excess, 95% CL upper limits are set with the **CL$_\text{s}$** prescription (`quickLimit`) on:

- the production cross-section of **generic Gaussian resonances** (widths matched to the $m_{jj}$ resolution up to ~15%), and
- the **$Z'$ dark-matter mediator**, translating the cross-section constraint into a constraint on the coupling to quarks via

$$
N_\text{sig} \propto g_q^2
\quad\Longrightarrow\quad
g_q^\text{lim} = g_q^\text{ref} \times \sqrt{\frac{N_\text{lim}}{N_\text{ref}\times 1.25}},
\qquad N_\text{ref} = \mathcal{L}\,\sigma\,BR\,\mathcal{A}\,\epsilon,
$$

where the factor 1.25 accounts for the $b\bar b$ branching ratio not simulated in the signal samples. Expected limits before full unblinding are estimated by scaling the partially-unblinded limit with $\sqrt{\mathcal{L}_\text{full}/\mathcal{L}_\text{partial}}$ or by up-scaling the background-only template and re-running the limit machinery.

## Spurious-signal uncertainty

For the fit strategy finally chosen on the fully unblinded dataset, the spurious-signal uncertainty is the **symmetrised mean of the spurious-signal distribution over the 100 toys, per signal point**, applied to *all* signal points regardless of whether the $|S_\text{spur}| < 0.5\,\sigma_\text{fit}$ criterion is met (failing points are thus penalised with a larger uncertainty).

## Where each piece lives

| Ingredient | Implementation |
|---|---|
| Dijet function, signal models | `config/dijetisrTLA/*.template` XML cards |
| Workspace build | `xmlAnaWSBuilder` (`XMLReader`) |
| χ² fits (B-only / S+B) | `quickFit` via `python/run_anaFit.py` |
| BumpHunter window / p-value | `python/FindBHWindow.py` + `pyBumpHunter` |
| Pseudo-data | `python/generatePseudoData.py` |
| Validation tests | see [Validation tests](validation-tests.md) |
| CL$_\text{s}$ limits | `quickLimit`, plotted with `python/plotLimits.py` |
