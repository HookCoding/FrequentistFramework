# Analysis Workflow Overview

After running `run_anaFit.py` on an **mjj histogram**, the script produces a folder containing:

- XML files  
- PDF files
- ROOT files with fit information, background template + pseudodata histograms if generated in the `python generatePseudoData.py` step, and others

In the case of TLA Run 2, this fit corresponds to an **Npar+2 background-only fit**, used as a **background template** to generate pseudodata. As a **first test** to validate the fit strategy, we perform an **Npar fit** (not Npar+2) on the generated pseudodata and verify that the **p-value** is valid for most toys.

The following sections describe the subsequent validation tests.

---

## Spurious Signal Test

This test fits all pseudodata histograms (typically 100–1000) using a **B+S fit** and extracts the signal strength.

### Running on Condor

1. Go to the submission folder and set the output folder names and other parameters in a new `condor_args.txt` file by running:
   ```
   python condor_handler.py
   ```
2. Configure signal, background, category, etc. in `condor_script.sh`. `datafile` must contain the pseudodata histograms generated earlier.
3. Submit the job:
   ```
   condor_submit condor_submit.sh
   ```

Each pseudodata toy produces one output folder with the same structure as the `run_anaFit` step. Each fit stores the fitted signal strength.

### Collecting Results

Example command:

```
python createExtractionGraph.py --outfile extractionGraphs_ninePar_min90_zprime.root --filespath "/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_90_1000_ninePar/pseudodatafits_sevenPar_quickFitEdit_minTol_zprime/fit_sevenPar_mass*/FitParameters_anaFit_Par_pseudodata_mean*"
```

This generates a ROOT file (e.g. `extractionGraphs.root`) containing all toy histograms and graph points.

### Plotting Spurious Signal

To collect the graph points and make a pretty plot do:
```
python SpuriousSignal.py extractionGraphs.root
```

The test can be run using Gaussian or Z′ signal shapes. For Z′, the systematic uncertainties file must be included in `run_anaFit.py`. This file is a json obtained by fitting a Z′montecarlo spectrum and analyzing the systematic shifts with the [TLA ntuple analysis framework](https://gitlab.cern.ch/tla-atlas-run3/tla-ntuple-analysis).

---

## Signal Injection Linearity Test

This test injects signal into each background pseudodata toy and checks whether the extracted signal strength scales linearly with the number of injected events. Different injector scripts exist depending on the signal model and sampling method:

- `inject_gaussians.sh`
- `inject_zprime.sh`
- `inject_zprime_dscblimits.sh`

### Gaussian Injection Example

```
python InjectGaussian.py --infile /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root --histname pseudodata --sigmean 800 --sigwidth 15 --sigamp 5 --firsttoy 0 --lasttoy 99
```

`sigamp` is given in units of √B, where **B** is the number of background events within ±1σ of the signal (determined of course by the sigmean and sigwidth).

### Z′ Injection Options

Using only DSCB shape (JSON):

```
python InjectZprime.py --infile /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root --histname pseudodata --sigfile /eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/signalUncertainty_interpolated.json --sighist mjj_yStar_cut_nominal --sigamp 5 --firsttoy 0 --lasttoy 99
```

Using Monte-Carlo histogram (preferred for realistic tails):

```
python InjectZprime.py --infile /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root --histname pseudodata --sigfile /eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC.root --sigfile_dscb /eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/signalUncertainty_interpolated.json --sighist mjj_yStar_cut_nominal --sigamp 5 --firsttoy 0 --lasttoy 99 n
```
In TLA Run 3 this was the chosen method to analyze Z′ injections because a DSCB fit to montecarlo spectrums may not perform well in the tails, leading to slow decays. This means that if this parametrized function was used for sampling, there would be a bias and many events would be sampled from these tails. In order to avoid this, the only use of the DSCB function was to find the range where we would sample from the original montecarlo histogram.

### Fitting Injected Toys

Run a similar script to the one from the Spurious Signal study, this time using the injected pseudodata. First create extraction graphs:

```
python createExtractionGraph_signalInjection.py injected_paths_tenPar_width5.txt --outfile extractionGraphs_tenPar_min108.root
```

The txt file is supposed to contain a list of injected data. Here is an example on how to do this file collection:

```
find /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/injected/pseudodatafits_eightPar_quickFitEdit_minTol_injected_mean*_width5_amp*/fit_eightPar_mass*_width*_pseudodata*_injected_mean*_width*_amp*/FitParameters_anaFit_Par_pseudodata_*.root > injected_paths_tenPar_width5.txt

```
another example:
```
find /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_125_1000_tenPar/injected/pseudodatafits_eightPar_quickFitEdit_minTol_injected_mean*_width5_amp*/fit_eightPar_mass*_width*_pseudodata*_injected_mean*_width*_amp*/FitParameters_anaFit_Par_pseudodata_*0.root > injected_paths/injected_paths_125_tenPar_width5.txt
```

Plot results:

```
python plotExtractionGraph.py extractionGraphs_tenPar_min108.root
```

This completes the **Signal Injection Linearity Test** (Gaussian or Z′). For Z′, include systematics in `run_anaFit.py`.

---

##  Background Stability Test

This test compares the original background template and the background component from B+S fits to injected toys. Run:

```
python BackgroundStability.py --toyfiles injected_paths/injected_paths_tenPar_injected_min108_mean120_width15_amp3_BS.txt --toyhist Run3TLA_bkgonly/postfit --reffile /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root --refhist unfluctuated --outfile backgroundStability_tenPar_injected_min108_mean120_width15_amp3.pdf
```

This helps identify statistical fluctuations or outliers causing SS or SILT issues.

---

## F-Test

Finally, compare different background parameterizations:

```
python FTest.py /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_130_1000_eightPar/PostFit_anaFit_eightPar_bkgOnly.root /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_130_1000_sevenPar/PostFit_anaFit_sevenPar_bkgOnly.root /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_130_1000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root /eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_130_1000_fivePar/PostFit_anaFit_fivePar_bkgOnly.root
```

This evaluates whether using a higher-order fit is statistically justified.

---

