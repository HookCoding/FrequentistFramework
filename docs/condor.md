# Batch submission (HTCondor)

The toy-based validation tests (spurious signal, signal injection) require thousands of independent fits — one per (signal mass, width, toy [, injection amplitude]). The `submission/` directory contains the HTCondor machinery: `condor_handler.py` (job-list generator), `condor_script.sh` (per-job payload), `condor_submit.sub` (submit file), plus the variants under `submission/common/` and archived production runs (e.g. `condor_run_10param_8param/`).

## Files

```
submission/
├── condor_handler.py      # generates condor_args.txt (one line per job)
├── condor_args.txt        # -m <mass> -w <width> -p <toy> [-M -W -A injection] -r <outfolder>
├── condor_script.sh       # payload: env setup + one run_anaFit.py call
├── condor_submit.sub      # condor submit file (queue arguments from ../condor_args.txt)
└── common/                # shared/older variants
```

## One-time adaptation

!!! danger "Hard-coded paths"
    Both `condor_script.sh` and `condor_handler.py` hard-code `localdir` to a previous author's checkout (`/afs/cern.ch/work/l/lbazzano/tla/FrequentistFramework`). **Change `localdir` to your FrequentistFramework directory in both files.** Also verify that the setup script they source exists in your checkout — use `scripts/setup_buildAndFit.sh` (older revisions reference `scripts/setup_buildCombineFit.sh`).

Output folders (`-r`) usually point to EOS; make sure you have write access and quota — 100 toys × a full mass grid produces $\mathcal{O}(10^4)$ folders with several ROOT files each.

## Workflow

1. **Configure the payload** — edit the marked block of `submission/condor_script.sh`: `rangelow`/`rangehigh`, `pars_B` (pseudo-data template parameters, $N_\text{par}+2$), `pars_BS` (fit strategy $N_\text{par}$), the `datafile` (plain or injected pseudo-data, see [step 3](flowchart-steps/spurious-signal.md) / [step 4](flowchart-steps/signal-injection.md)), the signal/background/category cards and the `outputfile` naming.
2. **Generate the job list**:

    ```bash
    cd submission
    python condor_handler.py
    ```

    Edit the loops in `condor_handler.py` to set the mass/width (and amplitude) grid, the number of toys, and the output-folder scheme. Job flavour defaults to `workday` (8 h); the notification email is also set there.

3. **Submit**:

    ```bash
    condor_submit condor_submit.sub
    ```

    Logs go to `job_$(Process).{log,out,err}` in the submit directory.

4. **Collect** — each job leaves the standard `run_anaFit` outputs (`FitResult_*`, `FitParameters_*`, `PostFit_*`) in its `-r` folder. Aggregate with `createExtractionGraph.py` (SS) or `createExtractionGraph_signalInjection.py` (SILT) as described in the respective step pages.

## Monitoring and hygiene

```bash
condor_q                      # job status
condor_q -analyze <clusterid> # why jobs idle
condor_rm <clusterid>         # remove
grep -L "Done!" job_*.out     # jobs that did not finish cleanly
```

Resubmission is easiest by regenerating `condor_args.txt` with only the missing (mass, width, toy) combinations — the fits are independent, so partial reruns are safe.
