# Install
```
setupATLAS
lsetup git
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/FrequentistFramework.git --branch tofitsch_baseline_fit
cd FrequentistFramework
. scripts/install_FrequentistFramework.sh
. scripts/install_pyBumpHunter.sh
. pyBumpHunter/pyBH_env/bin/activate
deactivate
. scripts/install_quickFit_and_xmlAnaWSBuilder.sh
```

# Setup

```
cd work/tlafits/FrequentistFramework
. scripts/setup_buildCombineFit.sh
```

# Run
```
. scripts/run_anaFit.sh
```

# Links
* [FrequentistFramework](https://gitlab.cern.ch/tla-atlas-run3/FrequentistFramework/-/tree/lbazzano-fitValidation?ref_type=heads)
* [Falk's tutorial recording](https://indico.cern.ch/event/1266089/)
* [Falk's slides](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/FrequentistFramework/-/tree/master/doc?ref_type=heads)
* [JMX unblinding approval](https://indico.cern.ch/event/1607958/)
* [1k slides of notes](https://docs.google.com/presentation/d/10mfb9mbDt6-nh7eKaL4_34VH2Yx_fdRuKtgvNG3sepE/edit?slide=id.p#slide=id.p)

# Files
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
