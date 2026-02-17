# Instructions
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
