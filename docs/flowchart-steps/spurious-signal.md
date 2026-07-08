# Step 3 — Spurious signal test

S+B fits on the 100 background-only toys, for every signal hypothesis, checking $|S_\text{spur}| < 0.5\,\sigma_\text{fit}$ (see [test definition](../statistics/validation-tests.md#spurious-signal-ss-test)).

This is $\mathcal{O}(100\ \text{toys} \times N_\text{mass} \times N_\text{width})$ fits — run it on [HTCondor](../condor.md).

## 1. Configure the per-toy fit

Edit `submission/condor_script.sh` (this is the payload each job runs):

```bash
localdir=/afs/cern.ch/work/<u>/<user>/.../FrequentistFramework   # (1) YOUR checkout
...
rangelow=125            # (2) the fit range of the strategy under test
rangehigh=1000

pars_B=ten              # (3) template used to GENERATE the pseudo-data (Npar+2)
pars_BS=eight           # (4) strategy Npar used for the S+B fit

# bkg only // SS
datafile=<path to the pseudo-data file from step 2>
outputfile=${folder}/FitResult_anaFit_${pars_BS}Par_pseudodata${p}_mean${sigmean}_width${sigwidth}.root

datahist="pseudodata_${pseudodata}"
dosignal=1              # S+B fit: the POI nsig_mean<M>_width<W> is fitted
dolimit=0
```

1. **Both** the `localdir` in `condor_script.sh` and in `submission/condor_handler.py` are hard-coded to the original author's area — change them to your checkout, and check the sourced setup script name matches an existing one (`scripts/setup_buildAndFit.sh`).
2. Same `rangelow`/`rangehigh` as the strategy being validated.
3. The `datafile` must be the pseudo-data produced in [step 2](pseudodata.md) with `pars_B` parameters.
4. The S+B fit uses the strategy's own $N_\text{par}$.

For the **$Z'$ shape** instead of Gaussians, switch in the same script to the parametrised signal cards and enable the systematics JSON (see [S+B fits](limits.md#z-parametrised-signal)).

## 2. Generate the job list and submit

```bash
cd submission
python condor_handler.py        # writes condor_args.txt: one line per (mass, width, toy)
condor_submit condor_submit.sub
```

Each `condor_args.txt` line has the form

```
-m 400 -w 8.00 -p 17 -r <outdir>/pseudodatafits_eightPar/fit_eightPar_mass400_width8_pseudodata17
```

(`-m` signal mass, `-w` width, `-p` toy index, `-r` per-job output folder). Edit the loops in `condor_handler.py` to set the mass/width grid and the output folder naming.

## 3. Collect the fitted yields

Each job writes a `FitParameters_*.root` containing the fitted `nsig`. Aggregate them:

```bash
python python/createExtractionGraph.py \
    --outfile extractionGraphs_eightPar_min125.root \
    --filespath "<outdir>/run_125_1000_tenPar/pseudodatafits_eightPar/fit_eightPar_mass*/FitParameters_anaFit_*Par_pseudodata_mean*"
```

## 4. Evaluate

```bash
python python/SpuriousSignal.py extractionGraphs_eightPar_min125.root
```

This produces the SS summary plot: per mass point, the marker is $S_\text{spur}$ (mean over toys) with $\sigma_\text{fit}$ (RMS) as error bar, and the bottom panel shows $S_\text{spur}/\sigma_\text{fit}$ with the $\pm 0.5$ pass lines. Adjust the luminosity label / axis ranges at the top of `SpuriousSignal.py` for your unblinding stage (blocks for 1, 5 and 25 fb⁻¹ are provided).

## Pass / fail

- **Pass:** all mass/width points within $\pm 0.5$ (isolated points up to 1.0 may be tolerated with convener agreement).
- **Fail:** discard this $N_\text{par}$, increment it and repeat from the toy fits (the pseudo-data of step 2 is unchanged). If $N_\text{par}=8$ fails too: restrict the fit range or drop the offending signal point, per the flowchart.
- Whatever passes here defines the **spurious-signal uncertainty** at the final stage: the symmetrised mean per signal point, applied to *all* points.
