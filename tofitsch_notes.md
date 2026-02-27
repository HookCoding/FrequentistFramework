
* [FrequentistFramework](https://gitlab.cern.ch/tla-atlas-run3/FrequentistFramework/-/tree/lbazzano-fitValidation?ref_type=heads)
* [Falk's tutorial recording](https://indico.cern.ch/event/1266089/)
* [Falk's slides](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/FrequentistFramework/-/tree/master/doc?ref_type=heads)
* [JMX unblinding approval](https://indico.cern.ch/event/1607958/)
* [1k slides of notes](https://docs.google.com/presentation/d/10mfb9mbDt6-nh7eKaL4_34VH2Yx_fdRuKtgvNG3sepE/edit?slide=id.p#slide=id.p)

# Copy files
```
mkdir data_partial

cp /afs/cern.ch/user/l/lbazzano/public/data23_histos.root data_partial

cp /afs/cern.ch/user/l/lbazzano/public/PostFit_anaFit_tenPar_bkgOnly.root data_partial
cp /afs/cern.ch/user/l/lbazzano/public/dijetisrTLA_combWS_tenPar.pdf data_partial

mkdir -p zprime_shapes
cp -r /afs/cern.ch/user/l/lbazzano/public/MGPy8EG_S1_qqa_Ph25_mRp*_gASp1_qContentUDSC zprime_shapes
```

copy the 100% unblinding file from:
```
https://gitlab.cern.ch/tla-atlas-run3/tla-ntuple-analysis/-/tree/full-unblinding/outputs/FINAL_100pc_unblinding_histograms?ref_type=heads
```

to 
```
./data23_histos.root
```

# Install
```
cd work/tlafits
setupATLAS
lsetup git
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/FrequentistFramework.git --branch dev_tofitsch --recursive
cd FrequentistFramework
rm -r quickFit
cp -r ../FrequentistFramework_tomas/quickFit/
. scripts/install_FrequentistFramework.sh
. scripts/install_pyBumpHunter.sh
. pyBumpHunter/pyBH_env/bin/activate
deactivate
```

# Setup

```
cd work/tlafits/FrequentistFramework
. scripts/setup_buildCombineFit.sh
```

# changes suggested by Max

```
# quickFit/app/quickFit.cxx (https://gitlab.cern.ch/tla-atlas-run3/quickFit/-/blob/main/app/quickFit.cxx?ref_type=heads)
# after L292 (https://gitlab.cern.ch/tla-atlas-run3/quickFit/-/blob/main/app/quickFit.cxx?ref_type=heads#L292)
fitter->setChi2Fit(_chi2fit);
fitter->setChi2Constraints(_chi2constraints);
fitter->setPoissonError(_poissonerror);

# FrequentistFramework/python/run_anaFit.py (https://gitlab.cern.ch/tla-atlas-run3/FrequentistFramework/-/blob/lbazzano-fitValidation/python/run_anaFit.py?ref_type=heads#L58)
# wherever you run quickFit command replace with the string below:
"quickFit --chi2fit 1 --poissonerror 0 -f %s -d combData %s --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-10 %s -o %s"

# NOTE adding "--poissonerror 0" to the command means that the data hist errors will be used for chi2 instead of sqrt(N_fit) -- I don't know which behaviour we actually want
```

additionally (for masked fit):

```
# in:
      if (_poissonerror) {
        spdlog::info("Building chi2 with splitrange and Poisson error...");
        chi2 = pdf->createChi2(*dh, RooFit::Extended(true), RooFit::DataError(RooAbsData::Poisson), RooFit::Range(_rangeName), RooFit::SplitRange(False));
      } 
# change False to true in SplitRange
```

then:
```
cd quickfit
rm -rf build/*
cd build
cmake ..
make
cd ../..
```

# Run
in `scripts/run_anaFit.sh` change:

```
-     for pars in eight #eight nine ten #seven #ten #eight # seven eight nine  #six seven eight #nine #four five six seven eight #six #four five seven 
+     for pars in ten #eight nine ten #seven #ten #eight # seven eight nine  #six seven eight #nine #four five six seven eight #six #four five seven 

- datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/maxFile/5fb/data23_histos.root
+ datafile=/afs/cern.ch/work/t/tofitsch/tlafits/data23_histos.root

- folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par
+ folder=/eos/home-t/tofitsch/tlafits/run_${rangelow}_${rangehigh}_${pars}Par

- sysfile=/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp${sigmean}_gASp1_qContentUDSC/signalUncertainty_interpolated.json
+ TODO

```

and in `python/run_anaFit.py` change:

```
- binningFileName = f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"
+ binningFileName = f"/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root"

- rebinfile=f"/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",
+ rebinfile=f"/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root",

- execute("ln -sf ~/WORK/tla/FrequentistFramework/config/dijetisrTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder))
+ execute("ln -sf /afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/config/dijetisrTLA/AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder))
- execute("source pyBumpHunter/pyBH_env/bin/activate; env PYTHONPATH=\"\" python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "Run3TLA_rebinned/postfit", "Run3TLA_rebinned/data", "{}/BHresults.json".format(folder)))
 + execute("source pyBumpHunter/pyBH_env/bin/activate; python3 python/FindBHWindow.py --inputfile %s --bkghist %s --datahist %s --outputjson %s; deactivate" % (postfitfile, "Run3TLA_rebinned/postfit", "Run3TLA_rebinned/data", "{}/BHresults.json".format(folder)))
```

and in `python/createBinning.py` change:

```
- tfile = ROOT.TFile.Open("/afs/cern.ch/user/l/lbazzano/WORK/tla/FrequentistFramework/Input/data/dijetisrTLA/resolutionFits.root", "READ")
+ tfile = ROOT.TFile.Open("/afs/cern.ch/work/t/tofitsch/tlafits/FrequentistFramework/Input/data/dijetisrTLA/resolutionFits.root", "READ")

```

```
mkdir -p /eos/home-t/tofitsch/tlafits

. scripts/run_anaFit.sh
```

# R21
this version of FrequentistFramework cannot be run fuly in R21 but you can run it in R22 (like above) and then run only the relevant parts (xmlAnaWSBuilder, quickFit) on the given output and compare. Do so with `test.sh`.
For this just use a centos7 container (`setupATLAS -c centos7`) and install quickFit and xmlAnaWSBuilder as described in their readmes from:
[quickFit](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/quickFit) branch: muscan,
[xmlAnaWSBuilder](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/quickFit) commit: @8027946f
