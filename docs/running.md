# Running a fit

The standard entry point is:

```bash
. scripts/run_anaFit.sh
```

This wrapper sets up the environment, configures one (or a loop of) fit configurations, and calls the actual driver `python/run_anaFit.py`. **All analysis choices are made by editing the variables at the top of the wrapper** — the sections below explain each of them. What to set for each step of the unblinding procedure is documented in [Running the flowchart](flowchart-steps/index.md).

## Anatomy of `scripts/run_anaFit.sh`

```bash
out_dir=/afs/cern.ch/work/<u>/<user>/tlafits   # where all results are stored

for pars in seven                # background function: number of parameters (word form)
do
  for rangelow in 125            # lower edge of the fit range [GeV]
  do
    for sigmean in 400           # signal mass hypothesis [GeV]
    do
      rangehigh=1000             # upper edge of the fit range [GeV]
      sigwidth=8                 # Gaussian signal width in % of the mass
      dosignal=0                 # 0: B-only fit, 1: S+B fit
      dolimit=0                  # 1: run quickLimit (CLs) after a successful S+B fit
      datafile=data/data23_histos.root
      datahist=mjj
      folder=$out_dir/run_${rangelow}_${rangehigh}_${pars}Par

      topfile=config/dijetisrTLA/dijetisrTLA.template
      signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
      backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template
      categoryfile=config/dijetisrTLA/category_dijetisrTLA.template

      outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root
      nbkg="dummy"               # overwritten by the prefit
      maskthreshold=0.01         # p(chi2) below which BumpHunter masking kicks in
      doprefit=1                 # ROOT prefit to seed the parameters

      ./python/run_anaFit.py --datafile ... --rangelow ... $flags
    done
  done
done
```

### The knobs

| Variable | Meaning | Typical values |
|---|---|---|
| `pars` | Number of parameters $N$ of the dijet background function; selects the template `background_dijetisrTLA_<pars>Par.template` | `four` … `ten` |
| `rangelow`, `rangehigh` | Fit range in $m_{jj}$ [GeV] | `125`, `1000` |
| `datafile` / `datahist` | Input ROOT file and histogram (1-GeV-binned $m_{jj}$) | `data/data23_histos.root` / `mjj` for data; a pseudo-data file / `pseudodata_<i>` for toys |
| `dosignal` | Adds the signal component and fits its yield `nsig` (S+B fit); the POI is `nsig_mean<M>_width<W>` (Gaussian) or `nsig_mR<M>` ($Z'$) | `0` or `1` |
| `dolimit` | Runs `quickLimit` after a successful S+B fit | `0` or `1` |
| `sigmean`, `sigwidth` | Signal hypothesis: mass [GeV] and Gaussian width [% of mass]. Special value `sigwidth=-999` switches to $Z'$ sample mode (POI `nsig_mR<M>`) | `400`, `8` |
| `sysfile` | JSON with the parametrised $Z'$ signal (DSCB parameters + systematic magnitudes), produced by `tla-ntuple-analysis`. Only used when the `--sysfile` argument is uncommented | see [S+B fits](flowchart-steps/limits.md) |
| `maskthreshold` | If the global fit $p(\chi^2)$ falls below this, BumpHunter masking is triggered ([details](flowchart-steps/bkg-only-fit.md)); set to `-1` to disable masking | `0.01` |
| `doprefit` | Run a plain-ROOT prefit first to determine starting parameters and `nbkg` | `1` |
| `folder` | Output directory for this configuration | `$out_dir/run_${rangelow}_${rangehigh}_${pars}Par` |

!!! tip "Convention: `Npar` vs the `pars` word"
    The flowchart speaks of a fit strategy $N_\text{par}$ and of pseudo-data templates built with $N_\text{par}+2$ parameters. The `pars` variable is simply the literal parameter count of the function being fitted *right now*: to build a pseudo-data template for an $N_\text{par}=8$ strategy you run with `pars=ten`; to run the validation fits of that strategy you run with `pars=eight`.

## What `python/run_anaFit.py` does

`run_anaFit.py` executes one full build–fit–extract cycle:

1. **Template instantiation** — copies the four XML cards (`topfile`, `categoryfile`, `backgroundfile`, `signalfile`) into `folder/` and substitutes the placeholders `DATAFILE`, `DATAHIST`, `RANGELOW`, `RANGEHIGH`, `BINS`, `NBKG`, `NSIG`, `SIGNAME`, `SIGMEAN`, `SIGWIDTH`, `BACKGROUNDFILE`, `SIGNALFILE`, `CATEGORYFILE`, `OUTPUTFILE` (and, with a `--sysfile`, the DSCB nominal parameters and `MAG_*` systematic magnitudes). Unreplaced `[MAG_*]` uncertainties are zeroed.
2. **Prefit** (`--doprefit`, class `PreFitter` in `python/PreFit.py`) — a standalone ROOT $\chi^2$ fit of the dijet function with thousands of retries; its best-fit parameters seed the XML card (`PAR1` … `PARn`) and its integral sets the `nbkg` range.
3. **Workspace build** — `xmlAnaWSBuilder/build/bin/XMLReader -x <topfile> -o "logy integral" --minimizerStrategy 0` creates the `RooWorkspace` (`wsfile`).
4. **Fit** — `quickFit/build/quickFit` with the analysis-standard options:

    ```
    --chi2fit 1 --poissonerror 1        # chi2 approximation of the NLL (see statistics)
    --hesse 1 --minStrat 2 --minTolerance 1E-6
    --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1
    --GKIntegrator 1 --nllOffset 0 --optConst 2
    ```

    For an S+B fit (`--dosignal`) the POI `-p nsig_<signame>` is added. The full quickFit log goes to `quickFitLog_*.log`, and `plot_edm.py` renders the estimated-distance-to-minimum evolution to `edm_*.pdf`.
5. **Post-fit extraction** — `ExtractPostfitFromWS.py` writes data/post-fit/residual histograms (fine-binned and rebinned to the $m_{jj}$ resolution binning) to `PostFit_*.root`, and `ExtractFitParameters.py` writes the fit parameters, $\chi^2$, ndof and $p$-value to `FitParameters_*.root`. The resolution binning `Input/data/dijetisrTLA/mjjResolutionBinning_<rangelow>.root` is created on demand by `python/createBinning.py` (re-derived from the start of the fit range, as prescribed by the unblinding strategy).
6. **$p$-value gate and BumpHunter masking** — if the global $p(\chi^2) \le$ `maskthreshold`, pyBumpHunter is run (`python/FindBHWindow.py`) on the rebinned data/post-fit histograms, the most discrepant window (≤ 3 resolution bins) is written to `BHresults.json`, the XML cards are cloned into `*_masked.xml` with `Blind="true"` / `BlindRange`, and the build+fit is repeated with the window masked. If the masked fit still fails the threshold, the driver exits with failure status — in flowchart terms, *fail 2nd time*.
7. **Limit setting** (`--dolimit`, S+B only) — `quickLimit` scans the POI to produce the CL$_\text{s}$ limits file `Limits_*.root`.

## Outputs

For a configuration `run_125_1000_sevenPar` with a B-only fit you will find in `folder/`:

| File | Content |
|---|---|
| `dijetisrTLA_combWS_sevenPar.root` | RooWorkspace built by XMLReader |
| `FitResult_anaFit_sevenPar_bkgOnly.root` | quickFit result (post-fit workspace, fit result, NP values) |
| `PostFit_anaFit_sevenPar_bkgOnly.root` | `Run3TLA[_rebinned]/{data, postfit, residuals}` histograms |
| `FitParameters_anaFit_sevenPar_bkgOnly.root` | fit parameters, `chi2` summary histogram ($\chi^2$, nbins, npars, ndof, pval), fitted `nsig` for S+B |
| `quickFitLog_anaFit_sevenPar_bkgOnly.log` | full minimiser log |
| `edm_anaFit_sevenPar_bkgOnly.pdf` | EDM vs iteration |
| `BHresults.json`, `*_masked.root/.xml` | only when BumpHunter masking was triggered |
| `Limits_anaFit_*.root` | only with `--dolimit` |
| `postFit.pdf`, `plots/…` | post-fit plots from `python/plotPostFit.py` and `plot_postfit.cpp` |

The wrapper finishes by producing the post-fit plots:

```bash
python python/plotPostFit.py -i ${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root -o ${folder}/postFit.pdf
root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"
```

!!! note
    The trailing `alert` in `run_anaFit.sh` is a personal shell alias (terminal bell); if your shell doesn't define it the resulting `command not found` is harmless.

## Direct invocation

`run_anaFit.py` can be called directly; `--help` lists all options:

```bash
./python/run_anaFit.py \
    --datafile data/data23_histos.root --datahist mjj \
    --topfile config/dijetisrTLA/dijetisrTLA.template \
    --categoryfile config/dijetisrTLA/category_dijetisrTLA.template \
    --backgroundfile config/dijetisrTLA/background_dijetisrTLA_sevenPar.template \
    --signalfile config/dijetisrTLA/signal/signal_dijetisrTLA.template \
    --wsfile run/ws.root --outputfile run/FitResult_anaFit.root \
    --nbkg dummy --rangelow 125 --rangehigh 1000 \
    --sigmean 400 --sigwidth 8 \
    --maskthreshold 0.01 --folder run --doprefit
```
