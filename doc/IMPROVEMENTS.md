# Improvements

One living document for the whole reproducibility/refactoring effort: what the framework now
does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve —
this describes the *current* state, not history. History is [CHANGELOG.md](../CHANGELOG.md).

## Reproducibility harness (`tests/repro.py`)

**Why.** Before any significant change to the repository, there has to be a way to *prove* a
change did not move a physics number. Plan:
[plans/2026-09-15-reproducibility-lock.md](../plans/2026-09-15-reproducibility-lock.md).

**What exists now.** Three subcommands:

```
python3 tests/repro.py selfcheck
python3 tests/repro.py env
python3 tests/repro.py record {J100,J50} [DIR] [--force --reason "..."]
```

`selfcheck` runs the comparator against synthetic data — no ROOT, no ATLAS environment, instant.

`env` verifies the software stack against the files that already declare each pin, rather than
inventing a second source of truth: the four sub-framework SHAs in `install.sh` against
`git rev-parse HEAD` in each gitignored clone; the RooFitExtensions SHA in each sub-framework's
own live `scripts/install_roofitext.sh`; agreement of the `lsetup "views …"` line across all
three `setup_lxplus.sh`; the pyBumpHunter venv's `pyvenv.cfg` against that view and Python 3.9.12;
the installed egg's pinned short SHA; and that none of the four clones have modified tracked
files. It also computes (but cannot yet compare — there is no baseline until `record` exists) the
SHA-256 of the two built binaries, and separately *records without asserting* the resolved ROOT,
`cmake` and numpy/scipy/uproot versions the BumpHunter step actually sees, reading the LCG
view's own `bin/` directly on CVMFS rather than through `lsetup` (see *Versions that cannot be
pinned* below for why).

Those versions matter to the analysis — they drive the 10 000 pseudo-experiments behind
`global_Pval` — even though nothing here can pin them, so the plan's amended §1 requires a
durable record of the versions each baseline was produced with, held in the baseline provenance
block. `env` reads whichever baseline exists (`tests/baseline_J100.json` if present, else
`baseline_J50.json`) and compares the live values against its `provenance.versions`, warning
non-fatally on any difference and never failing the command. Before any baseline exists it says
so and compares nothing. `env` never writes that record — only `record` does, and only when
building a new baseline from scratch.

`env` is not yet a reproducibility check of the fits themselves; `check` (which does that) is not
built yet.

### Versions that cannot be pinned

The resolved ROOT and `cmake` versions, and the numpy/scipy/uproot versions the BumpHunter step
sees, are read straight from the LCG view's own directory on CVMFS
(`/cvmfs/sft.cern.ch/lcg/views/<view>/bin/{root-config,cmake}`) rather than by asking `lsetup` to
put them on `$PATH` first. In this session's non-interactive shell, `lsetup`'s `PATH` edits do
not survive being probed in isolation — a bare `lsetup "views …"` followed by `cmake --version`
silently resolves the system's `/usr/bin/cmake` instead of the view's. Going to the view's own
`bin/` sidesteps that entirely and is what the framework's own compiled binaries were actually
built against.

The numpy/scipy/uproot probe is different: there is no file to read the answer from, because the
question is whether `python/FindBHWindow.py`'s actual activation line
(`source pyBH_env/bin/activate; python3 ...`) can import them at all. That probe replicates the
real invocation context — `scripts/setup_buildAndFit.sh`, exactly as every driver sources it,
not a simplified one-line stand-in — before activating the venv. See `CHANGELOG.md`'s 2026-09-16
`record` entry for why the simplified version of this probe gave a false negative.

**The comparator.** `compare(baseline, candidate, rtol_scale=1.0)` flattens two nested
dict/list structures to dotted key paths and compares every leaf:

- **tight** (`rtol=1e-6, atol=1e-8`): fitted parameters and errors, `minNll`, `chi2`,
  `chi2/ndof`, postfit bin contents, the data integral.
- **pvalue** (`rtol=1e-5, atol=1e-8`): the rebinned chi2 p-value, BumpHunter `global_Pval` and
  `significance`.
- **exact**: `status`, `covQual`, `nbins`, `npars`, `ndof`, `MaskMin`, `MaskMax`, `BlindRange`,
  `seed`, `npe`, the directory listing, and anything not otherwise classified.
- **note**: environment-observation keys (e.g. ROOT version) — recorded when they differ, never
  fail. The ROOT version legitimately differs between a bare shell and a sourced one.

A missing or extra key between baseline and candidate is always a failure. Every mismatch is
reported, not just the first. `rtol_scale` widens both float classes at once, for the
cross-machine case.

**What is next**, in the order the plan lays out: input-spectrum hashing, `record` (capture a
baseline from a run directory), then `check` (the end-to-end entry point). `record` and `check`
will need `env`'s checks too — `run_env_checks()` is already factored out so `check` can call it
rather than re-implementing it. Only `record`/`check` touch the comparator above — they need to
produce the nested dict it already knows how to compare; `env` deliberately does not use it (see
the design note in `tests/repro.py` above the `env` code: most of its checks are mutual-agreement
or dirty-file assertions, not a baseline-vs-candidate comparison).
