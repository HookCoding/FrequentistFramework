# Analysis Workflow Overview

After running `run_anaFit.py` on an **mjj histogram**, the script produces a folder containing:

- XML files  
- A PDF report  
- ROOT files (original + pseudodata histograms)  
- Fit information

This corresponds to an **Npar+2 background-only fit**, used as a **background template** to generate pseudodata with:

```
python generatePseudoData.py
```

For **TLA Run 2**, we instead perform an **Npar fit** (not Npar+2) on the generated pseudodata and verify that the **p-value** is valid for most toys — this is the **first test**.

The following sections describe the subsequent validation tests.

---

## ✅ Spurious Signal Test

This test fits all pseudodata histograms (typically 100–1000) using a **B+S fit** and extracts the signal strength.

### Running on Condor

1. Set the output folder names in `condor_args.txt` by running:
   ```
   python condor_handler.py
   ```
2. Configure signal, background, category, etc. in `condor_script.sh`  
   `datafile` must contain the pseudodata histograms generated earlier.
3. Submit the job:
   ```
   condor_submit condor_submit.sh
   ```

Each pseudodata toy produces one output folder (same structure as `run_anaFit`). Each fit stores the fitted signal strength.

### Collecting Results

Example command:

```
python createExtractionGraph.py \
  --outfile extractionGraphs_ninePar_min90_zprime.root \
  --filespath "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_90_1000_ninePar/pseudodatafits_sevenPar_quickFitEdit_minTol_zprime/fit_sevenPar_mass*/FitParameters_anaFit_Par_pseudodata_mean*"
```

This generates a ROOT file (e.g. `extractionGraphs.root`) containing all toy histograms.

### Plotting Spurious Signal

```
python SpuriousSignal.py extractionGraphs.root
```

The test can be run using Gaussian or Z′ signal shapes.  
For Z′, the systematic uncertainties file must be included in `run_anaFit.py`.

---

## ✅ Signal Injection Linearity Test

This test injects signal into each background pseudodata toy and checks whether the extracted signal strength scales linearly with the number of injected events.

Different injector scripts exist depending on the signal model:

- `inject_gaussians.sh`
- `inject_zprime.sh`
- `inject_zprime_dscblimits.sh`

### Gaussian Injection Example

```
python InjectGaussian.py \
  --infile /eos/.../Run3_TLA108_1000_tenPar_finebinned_scale.root \
  --histname pseudodata \
  --sigmean 800 \
  --sigwidth 15 \
  --sigamp 5 \
  --firsttoy 0 \
  --lasttoy 99
```

`sigamp` is given in units of √B, where **B** is the number of background events within ±1σ of the signal.

### Z′ Injection Options

Using only DSCB shape (JSON):

```
python InjectZprime.py \
  --infile ... \
  --histname pseudodata \
  --sigfile signalUncertainty_interpolated.json \
  --sighist mjj_yStar_cut_nominal \
  --sigamp 5 \
  --firsttoy 0 \
  --lasttoy 99
```

Using Monte-Carlo histogram (preferred for realistic tails):

```
python InjectZprime.py \
  --infile ... \
  --histname pseudodata \
  --sigfile systematics.root \
  --sigfile_dscb signalUncertainty_interpolated.json \
  --sighist mjj_yStar_cut_nominal \
  --sigamp 5 \
  --firsttoy 0 \
  --lasttoy 99
```

### Fitting Injected Toys

Run the Spurious Signal study again using the injected pseudodata.

Create extraction graphs:

```
python createExtractionGraph_signalInjection.py injected_paths_tenPar_width5.txt \
  --outfile extractionGraphs_tenPar_min108.root
```

Example file collection:

```
find /eos/.../fit_eightPar_mass*_width*_pseudodata*_injected*/FitParameters_anaFit_Par_pseudodata_*.root \
  > injected_paths_tenPar_width5.txt
```

Plot results:

```
python plotExtractionGraph.py extractionGraphs_tenPar_min108.root
```

This completes the **Signal Injection Linearity Test** (Gaussian or Z′).  
For Z′, include systematics in `run_anaFit.py`.

---

## ✅ Background Stability Test

This compares:

- the original background template  
**vs.**
- the background component from B+S fits to injected toys

Run:

```
python BackgroundStability.py \
  --toyfiles injected_paths/...txt \
  --toyhist Run3TLA_bkgonly/postfit \
  --reffile /eos/.../Run3_TLA108_1000_tenPar_finebinned_scale.root \
  --refhist unfluctuated \
  --outfile backgroundStability_tenPar_injected_min108_mean120_width15_amp3.pdf
```

This helps identify statistical fluctuations or outliers causing SS or SILT issues.

---

## ✅ F-Test

Finally, compare different background parameterizations:

```
python FTest.py \
  /eos/.../PostFit_anaFit_eightPar_bkgOnly.root \
  /eos/.../PostFit_anaFit_sevenPar_bkgOnly.root \
  /eos/.../PostFit_anaFit_sixPar_bkgOnly.root \
  /eos/.../PostFit_anaFit_fivePar_bkgOnly.root
```

This evaluates whether using a higher-order fit is statistically justified.

---

