# Install
```
setupATLAS
lsetup git
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/FrequentistFramework.git --branch tofitsch_baseline_fit
cd FrequentistFramework
. install.sh
```

then change `out_dir` at the start of `scripts/run_anaFit.sh`. This is where all results will be stored

# Setup

```
. setup.sh
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
the 100% unblinding file
```
./data/data23_histos.root
```
 is from:
```
https://gitlab.cern.ch/tla-atlas-run3/tla-ntuple-analysis/-/tree/full-unblinding/outputs/FINAL_100pc_unblinding_histograms?ref_type=heads
```

# Quality checks

Run the lightweight safety-net checks locally with:

```bash
py -3 -m pip install pytest ruff black
py -3 scripts/quality_check.py
```

The checks currently cover:
- a small repo-root regression test under tests/
- linting with ruff
- formatting validation with black
