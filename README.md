## Install

This program runs on Unix systems.

```bash
setupATLAS
lsetup git
git clone https://github.com/tofitsch/FrequentistFramework --branch harry
cd FrequentistFramework
bash install.sh --build
```

Do not run the installer with `. install.sh` or `source install.sh`. The installer uses `exit` to report failures, which would terminate the active shell session if it were sourced.

Change `out_dir` at the start of `scripts/run_anaFit.sh` to select where the analysis results will be stored.

## Setup

```bash
. setup.sh
```

## Run

```bash
. scripts/run_anaFit.sh
```

## Links

- [FrequentistFramework](https://gitlab.cern.ch/tla-atlas-run3/FrequentistFramework/-/tree/lbazzano-fitValidation?ref_type=heads)
- [Falk's tutorial recording](https://indico.cern.ch/event/1266089/)
- [Falk's slides](https://gitlab.cern.ch/atlas-phys-exotics-dijet-tla/FrequentistFramework/-/tree/master/doc?ref_type=heads)
- [JMX unblinding approval](https://indico.cern.ch/event/1607958/)
- [1k slides of notes](https://docs.google.com/presentation/d/10mfb9mbDt6-nh7eKaL4_34VH2Yx_fdRuKtgvNG3sepE/edit?slide=id.p#slide=id.p)

## Files

The 100% unblinding file is:

```text
data/data23_histos.root
```

It is from the [full-unblinding histogram outputs](https://gitlab.cern.ch/tla-atlas-run3/tla-ntuple-analysis/-/tree/full-unblinding/outputs/FINAL_100pc_unblinding_histograms?ref_type=heads).

## Tier 1 and Tier 2 validation

Tier 1 provides the scientific safety system for the authoritative J100 and J50 background-only workflows. It protects the launcher contracts, required scientific artifacts, schema-version-2 provenance, fit parameters, and chi-square p-values.

Tier 2 provides the reproducible Python development environment and the lightweight pytest, Ruff, and Black quality gate.

Create and activate the development environment with:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev-lock.txt
```

Run the complete lightweight Tier 1 and Tier 2 quality gate with:

```bash
python scripts/quality_check.py --mode full
```

This command runs the approved lightweight pytest suite and the configured Ruff and Black checks. Scientific tests that require ROOT and the prepared analysis dependencies are separate from the lightweight gate.

For complete operating and validation details, see:

- [Tier 1 system](doc/TIER1_SYSTEM.md)
- [Tier 2 system](doc/TIER2_SYSTEM.md)
- [Tier 1 environment provenance](doc/TIER1_ENVIRONMENT_PROVENANCE.md)
