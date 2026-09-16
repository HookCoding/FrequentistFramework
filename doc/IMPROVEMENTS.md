# Improvements

One living document for the whole reproducibility/refactoring effort: what the framework now
does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve —
this describes the *current* state, not history. History is [CHANGELOG.md](../CHANGELOG.md).

## Reproducibility harness (`tests/repro.py`)

**Why.** Before any significant change to the repository, there has to be a way to *prove* a
change did not move a physics number. Plan:
[plans/2026-09-15-reproducibility-lock.md](../plans/2026-09-15-reproducibility-lock.md).

**What exists now.** One subcommand, `selfcheck`, and the comparator it tests:

```
python3 tests/repro.py selfcheck
```

`selfcheck` runs the comparator against synthetic data — no ROOT, no ATLAS environment, instant.
It is not yet a reproducibility check of the fits themselves; `env`, `record` and `check` (which
do that) are not built yet.

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

**What is next**, in the order the plan lays out: `env` (verify the software stack against
`install.sh` and the sub-frameworks' own setup scripts), input-spectrum hashing, `record`
(capture a baseline from a run directory), then `check` (the end-to-end entry point). None of
these touch the comparator above — they only need to produce the nested dict it already knows
how to compare.
