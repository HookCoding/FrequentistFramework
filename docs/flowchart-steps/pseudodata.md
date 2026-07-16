# Step 2 — Pseudo-data generation

Once the $(N_\text{par}{+}2)$ B-only fit on data has passed ([step 1](bkg-only-fit.md)), its post-fit shape becomes the **background template** from which the validation toys are drawn: each toy is a bin-wise Poisson fluctuation of the template.

## Command

The `generatePseudoData.py` call is already present (commented out) at the bottom of `scripts/run_anaFit.sh` — uncomment the *no upscaling* variant, or run it directly:

```bash
toys=100

python python/generatePseudoData.py \
    --infile  ${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root \
    --inhist  Run3TLA/postfit \
    --outhist pseudodata \
    --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale.root \
    --nreplicas $toys
```

| Option | Meaning |
|---|---|
| `--infile` / `--inhist` | the post-fit background template from step 1 (`PostFit_*` file, `Run3TLA/postfit` histogram, fine-binned) |
| `--outhist` | base name; toys are written as `pseudodata_0` … `pseudodata_<N-1>`, plus the `unfluctuated` template |
| `--nreplicas` | number of toys (**100** in the baseline procedure) |
| `--scaling` | luminosity scale factor applied before fluctuation — **leave at the default 1** |

!!! danger "No luminosity up-scaling"
    Unlike earlier TLA iterations, this analysis does **not** up-scale the template to the full expected luminosity before fluctuating (`--scaling` stays 1). Up-scaling attributes fake statistical significance to fluctuations of the low-statistics dataset and was shown to corrupt the spurious-signal test. This is precisely why the validation is repeated at each unblinding stage.

!!! note "BumpHunter masking during template building"
    For the 20% and 100% stages, BumpHunter masking in [step 1](bkg-only-fit.md) is applied **only when the B-only template fit fails** the $p$-value test — not preventively (doing so was found to worsen the B-only $p$-value on the 20% dataset).

## Sanity check: B-only fits on the toys

The first test of a strategy $N_\text{par}$ is that a plain $N_\text{par}$ fit (not $N_\text{par}{+}2$) works on the toys. Point the fit at a toy by changing **two lines** in `scripts/run_anaFit.sh`:

```bash
pars=eight        # the strategy Npar being validated (template above was ten)
datafile=${out_dir}/run_${rangelow}_${rangehigh}_tenPar/Run3_TLA${rangelow}_${rangehigh}_tenPar_finebinned_scale.root
datahist=pseudodata_0          # loop over toys
```

Fitting all 100 toys is what the [HTCondor machinery](../condor.md) is for; the distribution of the resulting $\chi^2$ $p$-values can be inspected with `python/getChi2Distribution.py` / `python/plotChi2Ndof.py`.

## Validation of the generation workflow

Appendix .11.3 of the note stress-tests this workflow (response to real injected signal and to turn-on features). The corresponding checks can be reproduced by injecting signal into the data *before* the template fit (`python/InjectGaussian.py` on the data histogram) and confirming that BumpHunter flags and masks the injected window.
