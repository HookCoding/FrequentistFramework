# Setup

Every new shell needs the software environment before anything can be run:

```bash
cd FrequentistFramework
. setup.sh
```

## What `setup.sh` does

`setup.sh` checks that the sub-packages exist and then sources, in order:

1. `workspaceCombiner/setup_lxplus.sh`
2. `xmlAnaWSBuilder/setup_lxplus.sh`
3. `quickFit/setup_lxplus.sh`

Each of these runs `atlasLocalSetup.sh` and

```bash
lsetup "views LCG_102a x86_64-centos9-gcc11-opt"   # ROOT 6.26/08, Python 3.9
lsetup cmake
```

and exports the package's environment variables (`_DIRCOMB`, `_DIRXMLWSBUILDER`, `_DIRFIT`) plus `PATH`/`LD_LIBRARY_PATH` entries for the built binaries and the RooFitExtensions library. The guards on `$_DIR...` make re-sourcing a no-op, but the packages themselves refuse to set up twice:

!!! warning "Use a clean shell"
    If you see `_DIRXMLWSBUILDER is already defined, use a clean shell`, start a fresh shell — the LCG views cannot be stacked.

Finally `setup.sh` creates the default scratch directory `run/`.

## Setup inside the run scripts

The run scripts (`scripts/run_anaFit.sh`, `scripts/run_anaFit_flowchart.sh`, ...) source `scripts/setup_buildAndFit.sh` themselves, which performs the same environment setup for `xmlAnaWSBuilder` and `quickFit`. So for interactive fitting a plain `. scripts/run_anaFit.sh` from a clean shell is enough; sourcing `setup.sh` first is only required when you want to run the Python tools (`python/...`) or ROOT macros stand-alone.

## Checklist before running

- [x] You are in the **FrequentistFramework root** directory (all paths in scripts and XML cards are relative to it).
- [x] The environment is set up (`echo $_DIRFIT` prints the quickFit directory).
- [x] `out_dir` in `scripts/run_anaFit.sh` points to your output area.
- [x] The input `datafile`/`datahist` you configured actually exist (default: `data/data23_histos.root` with histogram `mjj`).
