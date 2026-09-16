# Improvements

One living document for the whole reproducibility/refactoring effort: what the framework now
does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve —
this describes the *current* state, not history. History is [CHANGELOG.md](../CHANGELOG.md).

## Reproducibility harness (`tests/repro.py`)

**Why.** Before any significant change to the repository, there has to be a way to *prove* a
change did not move a physics number. Plan:
[plans/2026-09-15-reproducibility-lock.md](../plans/2026-09-15-reproducibility-lock.md).

**What exists now.** Two subcommands:

```
python3 tests/repro.py selfcheck
python3 tests/repro.py env
```

`selfcheck` runs the comparator against synthetic data — no ROOT, no ATLAS environment, instant.

`env` verifies the software stack against the files that already declare each pin, rather than
inventing a second source of truth: the four sub-framework SHAs in `install.sh` against
`git rev-parse HEAD` in each gitignored clone; the RooFitExtensions SHA in each sub-framework's
own live `scripts/install_roofitext.sh`; agreement of the `lsetup "views …"` line across all
three `setup_lxplus.sh`; the pyBumpHunter venv's `pyvenv.cfg` against that view and Python 3.9.12;
the installed egg's pinned short SHA; and that none of the four clones have modified tracked
files. It also computes (but cannot yet compare — there is no baseline until `record` exists) the
SHA-256 of the two built binaries, and separately *records without asserting* the resolved
`cmake` version and the numpy/scipy/uproot versions the BumpHunter step actually sees — see
`KNOWN_ISSUES.md` issue 10 for what that last one currently turns up.

Those versions matter to the analysis — they drive the 10 000 pseudo-experiments behind
`global_Pval` — even though nothing here can pin them, so the plan's amended §1 requires a
durable record of the versions each baseline was produced with, held in the baseline provenance
block, which `env` reads and compares against, warning non-fatally on any difference. That record
does not exist until `record` is built, so for now `env` only observes and prints. It does not
keep a cache of its own observations: a record the tool overwrites with each run answers "did
this change since I last looked", not "what produced these numbers".

`env` is not yet a reproducibility check of the fits themselves; `record` and `check` (which do
that) are not built yet.

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
