# Step 1 — Background-only fit (with BumpHunter masking)

The first phase of the [validation flowchart](../statistics/flowcharts.md#1-validating-a-fit-strategy-figure-101): fit the unblinded $m_{jj}$ distribution with an $(N_\text{par}{+}2)$-parameter dijet function, masking with BumpHunter on failure. The same configuration (with `pars` = $N_\text{par}$ instead of $N_\text{par}{+}2$) is used for all other B-only fits in the procedure.

## Configure `scripts/run_anaFit.sh`

```bash
out_dir=<your output area>

for pars in ten          # (1) Npar+2 for the pseudo-data template fit
do
  for rangelow in 125    # (2) current fit-range start; loop e.g. "125 126 127" when walking the flowchart
  do
    rangehigh=1000

    dosignal=0           # (3) B-only
    dolimit=0
    doprefit=1

    datafile=data/data23_histos.root   # (4) the unblinded dataset for this stage
    datahist=mjj

    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template
    outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root

    maskthreshold=0.01   # (5) p(chi2) gate; -1 disables BH masking
```

1. To validate a strategy $N_\text{par}=8$ over the full range you first need a template fit with `pars=ten`. When you later re-fit pseudo-data toys with the strategy itself, set `pars=eight`.
2. Following the flowchart, when all $N_\text{par} \le 8$ fail you increase `rangelow` by 1 GeV and start over. The $m_{jj}$ resolution binning used by BumpHunter is automatically re-derived for the new `rangelow` (`python/createBinning.py` creates `Input/data/dijetisrTLA/mjjResolutionBinning_<rangelow>.root` if missing).
3. `dosignal=0` removes the POI: quickFit runs the plain background-only fit.
4. At the 4%/20% stages point `datafile`/`datahist` to the partial-unblinding histograms instead.
5. With the default `maskthreshold=0.01` the BumpHunter provision of the flowchart is applied automatically (see below).

Then run:

```bash
. scripts/run_anaFit.sh
```

## What happens on failure — automatic BumpHunter masking

If the global fit has $p(\chi^2) \le$ `maskthreshold`, `run_anaFit.py` automatically:

1. runs `python/FindBHWindow.py` (inside the `pyBH_env` venv) on `Run3TLA_rebinned/{postfit,data}` from the `PostFit_*.root` file,
2. writes the most discrepant window to `<folder>/BHresults.json` (`MaskMin`, `MaskMax`, `BlindRange`),
3. clones the XML cards to `*_masked.xml`, adding `Blind="true"` and the `BlindRange`, rebuilds the workspace (`*_masked.root`) and refits with the window masked (`--range SBLo_Run3TLA,SBHi_Run3TLA`).

The console output ends with one of three verdicts:

| Message | Flowchart meaning |
|---|---|
| `p(chi2) threshold passed. Exiting with succesful fit.` | **Pass** — proceed (template OK for pseudo-data) |
| `Continuing with successful (window-excluded) fit.` | **Pass after 1st failure** — but check `BHresults.json`: if the window sits at the *start* of the spectrum, treat it as a turn-on and increase $N_\text{par}$ instead |
| `p(chi2) threshold still not passed. Exiting with failed fit status.` | **Fail 2nd time** — increase $N_\text{par}$ by 1 (edit `pars`); after `pars` corresponding to $N_\text{par}=8$ fails, increase `rangelow` by 1 GeV |

!!! warning "Window width"
    The flowchart caps the exclusion window at **three $m_{jj}$ resolution bins**. Inspect the reported window in `BHresults.json` and the BumpHunter plots — a wider or start-of-spectrum window must not simply be masked.

## Checking the result

```bash
python python/plotPostFit.py -i ${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root -o ${folder}/postFit.pdf
root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"
```

- `postFit.pdf` — data vs post-fit with residuals; residuals must look like pure statistical fluctuations.
- `quickFitLog_*.log` / `edm_*.pdf` — minimiser health (status 0, small EDM, no parameter at its bound).
- `FitParameters_*.root` — the `chi2` histogram stores $\chi^2$, $N_\text{bins}$, $N_\text{pars}$, ndof and the $p$-value used by the gate.
