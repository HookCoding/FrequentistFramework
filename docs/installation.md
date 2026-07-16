# Installation

The framework is designed to run on **lxplus** (EL9) with the ATLAS software environment from CVMFS. All C++ sub-packages are built against **LCG_102a** (`x86_64-centos9-gcc11-opt`, ROOT 6.26/08).

## Prerequisites

- Access to CERN GitLab (`gitlab.cern.ch`) with Kerberos authentication (the clone URLs use `https://:@gitlab.cern.ch:8443/...`).
- `/cvmfs/atlas.cern.ch` mounted (any lxplus node).
- For the batch tests: access to HTCondor (`condor_submit`) and enough quota on AFS/EOS for the fit outputs.

## Clone and install

```bash
setupATLAS
lsetup git
git clone https://:@gitlab.cern.ch:8443/tla-atlas-run3/FrequentistFramework.git --branch tofitsch_baseline_fit
cd FrequentistFramework
. install.sh
```

!!! warning "Source, don't execute"
    `install.sh` (like `setup.sh` and the run scripts) must be **sourced** (`. install.sh`), not executed, because it exports environment variables into your shell.

## What `install.sh` does

1. **Clones the three C++ packages** from the `tla-atlas-run3` GitLab group at pinned commits on the `tofitsch_baseline_fit` branch:
   - `xmlAnaWSBuilder` (commit `6b84050f`)
   - `quickFit` (commit `0408030b`)
   - `workspaceCombiner` (commit `7d484ad3`)
2. For each of them:
   - sources the package's `setup_lxplus.sh` (sets up LCG_102a and CMake),
   - installs and builds the shared **RooFitExtensions** library (`scripts/install_roofitext.sh`),
   - builds the package itself with CMake into `<package>/build/`.
3. **Clones pyBumpHunter** from GitHub at commit `91f49a62` and installs it into a dedicated virtual environment `pyBumpHunter/pyBH_env`. The venv is activated automatically by `run_anaFit.py` whenever BumpHunter is needed — you never activate it by hand during normal running.

After a successful install you should have, among others:

```
xmlAnaWSBuilder/build/bin/XMLReader
quickFit/build/quickFit
quickFit/build/quickLimit
workspaceCombiner/build/...
pyBumpHunter/pyBH_env/
```

## Configure the output directory

All results are written below a single output directory. Edit the first line of `scripts/run_anaFit.sh`:

```bash
out_dir=/afs/cern.ch/work/<u>/<user>/tlafits   # <-- change this
```

Fit outputs for a given configuration land in `${out_dir}/run_<rangelow>_<rangehigh>_<pars>Par/`.

## Troubleshooting

??? failure "CMake ≥ 4 rejects `cmake_minimum_required(3.1)`"
    Recent `lsetup cmake` versions provide CMake ≥ 4, which refuses to configure the sub-packages. Rebuild them passing a policy override:

    ```bash
    cd <package>
    . setup_lxplus.sh
    rm -rf build && mkdir build && cd build
    cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..
    make -j4
    ```

    The helper `rebuild_pkgs.sh` in the repository root does this for all three C++ packages in one go.

??? failure "`XMLReader`/`quickFit` not found when running"
    The run scripts call the binaries via relative paths (`xmlAnaWSBuilder/build/bin/XMLReader`, `quickFit/build/quickFit`). Always launch fits **from the FrequentistFramework root directory** and make sure the builds completed (check `install_*.log` / `rebuild_*.log`).

??? failure "pyBumpHunter import errors"
    `run_anaFit.py` sources `pyBumpHunter/pyBH_env/bin/activate` before calling `python/FindBHWindow.py`. If imports fail, re-create the venv:

    ```bash
    cd pyBumpHunter
    rm -rf pyBH_env
    python3 -m venv pyBH_env
    . pyBH_env/bin/activate
    python3 setup.py install
    deactivate
    ```

## Input data

The repository ships the **100% unblinded** 2023 data histograms:

```
data/data23_histos.root        # histogram: mjj
```

taken from [`tla-ntuple-analysis` (full-unblinding outputs)](https://gitlab.cern.ch/tla-atlas-run3/tla-ntuple-analysis/-/tree/full-unblinding/outputs/FINAL_100pc_unblinding_histograms). Partial-unblinding datasets and signal-systematics JSON files used at earlier stages live on EOS (see [Running the flowchart](flowchart-steps/index.md)).
