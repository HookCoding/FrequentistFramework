# Lock the software versions and the J50/J100 results before refactoring

**Written** 2026-09-15 &nbsp;|&nbsp; **Amended** 2026-09-16 &nbsp;|&nbsp; **Branch** `claude-skills` &nbsp;|&nbsp; **Status** approved and implemented. A 2026-09-16 audit against this plan found ten deviations, filed as [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issues 12–21; all ten are fixed, the last on 2026-09-17.

Filed as written on 2026-09-15, and left alone through the first two implementation steps.

**One amendment has been made since, recorded here rather than applied silently.** On 2026-09-16,
at the repository owner's explicit instruction, §1's treatment of the versions that cannot be
pinned was rewritten — see *Versions that cannot be pinned* below, with matching edits in §3, §4,
§5 and Verification. The original text said only that `env` "records without asserting" those
versions. The first implementation read that as a local, self-updating cache of the last-observed
values which warned when they changed and then overwrote itself; that leaves no durable statement
of what the versions are *supposed* to be, which is the thing actually needed. That implementation
is to be removed, not extended. Everything outside those sections stands as originally written.

What actually happens on implementation belongs in [CHANGELOG.md](../CHANGELOG.md); where this
plan and the notebook disagree, the notebook is right.

---

## Context

Before any significant change to this repository we need to be able to *prove* that a change
did not move a physics number. Two things have to be nailed down:

1. **The software stack** — the four vendored sub-frameworks, RooFitExtensions, the CVMFS LCG
   view they build against, and the pyBumpHunter venv.
2. **The analysis's own inputs and code** — the drivers, the orchestration and extraction
   modules, the XML template cards and the four input spectra these two fits actually read.
3. **The analysis output** — the Run 2 dijet TLA J100 (481–3000 GeV) and J50 (302–2997 GeV)
   fits.

Both exist today only as prose: [README.md](../README.md) has an Environment table of pins,
[CHANGELOG.md](../CHANGELOG.md) records the fit numbers in hand-written tables. Nothing checks
either. The only regression procedure ever run is the manual eyeball comparison in the
2026-09-15 17:30 changelog entry.

Intended outcome: one script and two committed baseline files under `tests/`, so "did this
refactor change the physics?" becomes one command.

**The files are about to change substantially; the results must not.** This is a regression
harness to be run repeatedly *while* the repository is rewritten, not a one-off audit and
not a freeze on the code.


**Scope is strictly those two analyses.** The repository tracks 1570 files and carries several
analysis flavours that are no longer relevant (`bbyy`, `ttHyy`, `high_mass_diphoton`,
`dijetisrTLA`) plus 313 input spectra. **27 files** participate in a J50 or J100 run, and only
those are covered. Nothing here attempts to test the repository as a whole — a test suite over
dead code would cost effort to write, effort to maintain, and would fail for reasons that have
nothing to do with these two fits.

## What the survey found

The reproducibility chain is in better shape than it first looks, but it is undocumented in
places and actively mis-documented in others.

| Component | Pinned? | Where the pin actually lives |
|---|---|---|
| xmlAnaWSBuilder | yes `6b84050f…` | [install.sh:5](../install.sh) |
| quickFit | yes `0408030b…` | [install.sh:12](../install.sh) |
| workspaceCombiner | yes `7d484ad3…` | [install.sh:19](../install.sh) |
| pyBumpHunter | yes `91f49a62…` | [install.sh:56](../install.sh) |
| RooFitExtensions | yes `ba94bfcb…` | **inside each pinned clone**, `<fw>/scripts/install_roofitext.sh:16` |
| LCG view / ROOT / gcc | yes `LCG_102a x86_64-centos9-gcc11-opt` (ROOT 6.26.08) | `<fw>/setup_lxplus.sh` |
| `cmake` | **no** (`lsetup cmake`, floats) | `<fw>/setup_lxplus.sh` |
| pyBH venv python | `LCG_102a`, 3.9.12 | `pyBumpHunter/pyBH_env/pyvenv.cfg` |
| pyBH numpy/scipy | not installed in the venv; leak in via `PYTHONPATH` from the LCG view — pinned, but by accident | [python/run_anaFit.py:375](../python/run_anaFit.py) |
| Input spectra | 313 `.root` files tracked as plain git blobs, no LFS | [Input/](../Input/) |

**RooFitExtensions is pinned, contrary to first appearances.** [install.sh:28](../install.sh)
runs `. scripts/install_roofitext.sh` *after* `cd $x`, and a sourced path containing a slash
resolves against the current directory — so the sub-framework's own copy runs, and that copy
does `git checkout ba94bfcb…`. All three RooFitExtensions clones on disk are at that SHA. The
repository's own tracked [scripts/install_roofitext.sh](../scripts/install_roofitext.sh) does
`git pull` on master with no pin, but **it is dead code**: `install.sh:28` is its only
reference and never reaches it.

Three things are genuinely wrong rather than merely unpinned:

- **`.gitmodules` is inert.** It declares four submodules, but `git ls-tree HEAD` records no
  gitlink for any of the four paths and `git submodule status` is empty. The paths are plain
  gitignored directories ([.gitignore](../.gitignore) lines 20–25).
- **`install.sh` clones from CERN GitLab URLs that cannot be reached.** The clones on disk came
  from the public GitHub repositories instead
  (`github.com/tofitsch/{xmlAnaWSBuilder,quickFit,workspaceCombiner}`), at exactly the pinned
  SHAs. `install.sh` as written therefore cannot reproduce this tree on a fresh machine — the
  install is broken today, not merely under-documented. (`gitlab.cern.ch` answers HTTP 200, but
  that is the SSO login page, not the repository.)
- **`README.md:48` says the venv is "Python 3.9.12 from LCG_105".** `pyvenv.cfg` says LCG_102a.
  It also lists numpy/matplotlib/scipy/uproot as installed; the venv holds only the
  pyBumpHunter egg and setuptools. `README.md:54` and `CLAUDE.md:34-35` both warn about a
  `requirements.txt` that no longer exists on disk.

**Determinism is good enough to assert on.** Both RNGs on the fit path are fixed-seed —
`TRandom3(42)` at [python/PreFit.py:36](../python/PreFit.py) and `seed=666` at
[python/FindBHWindow.py:67](../python/FindBHWindow.py). quickFit is single-threaded
(`_nCPU = 1`, no `EnableImplicitMT`) with explicit `--minStrat 2 --minTolerance 1E-6
--nllOffset 0 --optConst 2`. This matches the observed bit-identical J100 re-run.

**Byte-level diffing is impossible** — every ROOT file embeds `TFile` creation datetimes and
`quickFitLog_*.log` embeds wall-clock timestamps. Comparison must be object-level.

**Which files are in the analysis path** (a snapshot from this survey, for orientation while
planning the refactor — not a checked artifact, and expected to age): the two drivers and
`scripts/setup_buildAndFit.sh`; `python/run_anaFit.py` with `PreFit`, `ExtractPostfitFromWS`,
`ExtractFitParameters` and `FindBHWindow`; `python/plotPostFit.py`, `plot_edm.py`,
`plot_postfit.cpp` and the three `atlasstyle-00-04-02/Atlas*.{C,h}` pairs; five
`config/dijetTLA/` templates plus `config/dijetisrTLA/AnaWSBuilder.dtd` (symlinked in by
`run_anaFit.py:185` despite the path); and the four inputs above. 27 files out of 1570 tracked
— the rest of the repository plays no part in these two fits.

**The system `python3` already has PyROOT 6.40.04** and reads the 6.26-written files fine, so
the comparison tool needs no `lsetup` and can be run from a bare shell.

## Approach

**One new code file**, `tests/repro.py`, with subcommands — not a checker script plus an
extractor script plus a runner, which would be three files, two languages and a shared constant
table duplicated across them. Plus two committed baseline JSONs. No pytest, no fixtures, no CI,
no new dependency.

```
python3 tests/repro.py selfcheck            # comparator's own test, no ROOT, instant
python3 tests/repro.py env                  # pins on disk vs pins in the installers
python3 tests/repro.py record J100 [DIR]    # write tests/baseline_J100.json
python3 tests/repro.py check                # env + inputs, then re-run both drivers and compare
python3 tests/repro.py check --quick        # J100 only, ~1 min
python3 tests/repro.py check --from DIR     # compare an existing output dir instead
```

### 1. `env` — verify the stack, without inventing a new source of truth

Every expected value is parsed from the file that already declares it:

- pair each `cd <dir>` / `git checkout <40-hex>` in `install.sh`, compare against
  `git -C <dir> rev-parse HEAD`
- parse `git checkout <sha>` from each **`<fw>/scripts/install_roofitext.sh`** — the live
  copies inside the clones, *not* the dead repo-root one — and compare against
  `git -C <fw>/RooFitExtensions rev-parse HEAD`
- parse `lsetup "views …"` from the three `<fw>/setup_lxplus.sh`; assert all three agree
- assert `pyBumpHunter/pyBH_env/pyvenv.cfg` names that same LCG view and Python 3.9.12
- assert the installed egg carries the pinned short SHA (`0.4.3.dev16+g91f49a6`). This is the
  one check the SHA comparison misses: clone updated, venv never rebuilt.
- assert there are **no modified tracked files** in the four clones — `git status --porcelain`
  with `??` entries ignored, because `cmake/`, `RooFitExtensions/` and `pyBH_env/` are normal
  untracked build artefacts and three of the four clones carry them today. A clone sitting at
  the correct SHA whose sources have been edited by hand is otherwise invisible to a SHA
  comparison.
- compare SHA-256 of `xmlAnaWSBuilder/build/bin/XMLReader` and `quickFit/build/quickFit`
  against the digests recorded in the baseline provenance. The SHA pins cover the *sources*,
  not the binaries actually built from them — the ones on disk were built 2026-08-21, and a
  stale or locally rebuilt binary passes every other check here. These are compiled
  dependencies rather than analysis-path code, so unlike the files being refactored their
  digests stay put.

Reading from the gitignored clones is deliberate — that is where the truth lives, and catching
a tree that has silently diverged from what `install.sh` declares is the whole point.

#### Versions that cannot be pinned

*(Amended 2026-09-16 — see the note at the top of this file for what this replaced and why.)*

Four things are left that this repository cannot pin at all: the resolved `cmake` version, and
the numpy, scipy and uproot versions visible to the BumpHunter step. `lsetup cmake` floats and
its line lives inside a gitignored clone; the three Python packages are not installed in
`pyBH_env` and arrive from outside it. (By what route exactly turned out not to be what this
plan assumed — the CHANGELOG has the correction.) The observed ROOT version belongs with them:
the LCG view name is asserted, but a view name is a label, and recording the ROOT build actually
in use is what makes "same view, different build" visible rather than silent.

These are not a lesser class of dependency. They drive the 10 000 pseudo-experiments behind
`global_Pval`, so a change in any of them moves a published number. What is missing is
*enforcement*, not importance — nothing here can force `lsetup cmake` or the view's numpy to
resolve to a given version. The answer to "cannot enforce" is to record, deliberately and
durably:

- **The record of what the versions are supposed to be is the baseline provenance block** (§3).
  A baseline is the statement "these numbers were produced by this stack"; the versions are part
  of that statement, committed beside the numbers they produced, and they change only when a
  baseline is deliberately re-cut with a stated `--reason`. There is no other defensible
  definition of "supposed to be" here, and it needs no new file — the provenance block already
  exists and already has to say what the baseline was cut from.
- **`env` reads that record and compares the live environment against it**, reporting every
  difference as a warning naming both the recorded and the observed value. It never fails on
  one. An LCG bump is not a broken checkout, the user usually cannot undo it, and a check that
  fails for reasons nobody can act on is a check that gets ignored — which would cost far more
  than it protects. Pin drift (§1's assertions) still fails; version drift warns.
- **`env` never writes that record.** A local cache that quietly overwrites itself with each
  run's observations is explicitly rejected. It answers "did this change since I last looked",
  which is not the question being asked; two runs after a version moves it states the new
  version as though it had always been the expectation, and the link between the recorded
  numbers and the software that produced them is gone. The record has to outlive the drift it
  exists to make visible.
- **Before any baseline exists**, `env` says exactly that and compares nothing. It does not seed
  an expectation from whatever the current machine happens to report: an expectation invented by
  observation is the failure being designed out.
- **Both baselines carry the same versions block**, since both are cut from one stack in one
  session. `record` warns when it is about to write a versions block that disagrees with the
  other baseline's — that means the stack moved mid-capture, which is a finding, not a detail.

A version recorded as unavailable is recorded verbatim as unavailable: "numpy could not be
imported here" is a true and useful thing for a baseline to say about the machine that cut it,
and a later run finding numpy present is a difference worth the same warning as any other.

This keeps §1's rule intact — nothing above invents a new source of truth. The baseline is
already the reference the whole harness is built around; this only makes the versions inside it
readable by the one subcommand that can see the live environment.

### 2. Input integrity — the only analysis files hashed

The four input spectra are the one part of the analysis path that must not change while the
code around them is rewritten. A change there means the fit is being asked a different
question, and the baselines stop describing it:

| Input | Used by |
|---|---|
| `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root` | J100 data |
| `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root` | J50 data |
| `Input/data/dijetTLA/fullRun2TLAJ100mjj.root` | J100 chi2 rebinning |
| `Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root` | J50 chi2 rebinning |

Their SHA-256 digests live in each baseline's own provenance block — **there is no separate
manifest file**. The baseline already has to record what it was cut from; making it record the
input hashes too costs four strings and leaves nothing to keep in sync. `check` verifies them
before running anything and stops on a mismatch.

**No file in the analysis path is hashed apart from these four.** An earlier draft of this plan
hashed all 27 files in the analysis path. That was wrong for the situation: almost every one of
them is going to be rewritten, so the hashes would go stale immediately, the check would fail on
every commit, and it would be ignored inside a day — while adding a file that has to be
maintained in lockstep with the refactor. The code is *expected* to change; the outputs are what
must not. Those are guarded by the baselines, which is the whole point of the harness. (The two
built sub-framework binaries are also hashed, but as part of the version pinning in §1 — they
are compiled dependencies, not code being rewritten, so their digests are stable.)

This also keeps the harness path-independent. A refactor that renames drivers, moves modules or
reorganises `config/` breaks nothing here, because nothing records where the code lives — only
where the four inputs live, and those are not being moved.

### 3. `record` / `extract` — what the baseline holds

Captured per fit variant: unmasked, plus the `_masked` set when present (J50 produces one,
J100 does not).

| Source | Quantities |
|---|---|
| `FitResult_*.root` key `fitResult` | `minNll`, `status`, `covQual`; every `floatParsFinal()` entry as name → [value, error] |
| `PostFit_*.root`, every TDirectory | the 6-bin `chi2` block by label: `chi2`, `chi2/ndof`, `nbins`, `npars`, `ndof`, `pval` |
| `PostFit_*.root`, `*_rebinned` dirs only | `postfit` bin contents (57 J100 / 65 J50) and `data` **integral** |
| `BHresults.json` (J50) | `MaskMin`, `MaskMax`, `BlindRange`, and from `pyBHresult`: `global_Pval`, `significance`, `seed`, `npe` |
| directory listing | `sorted(os.listdir(folder))` |
| provenance block | date cut, software pins from §1, SHA-256 of the four input spectra and of the two built binaries, the recorded ROOT / cmake / numpy / scipy / uproot versions — the durable record §1 has `env` compare the live environment against — and the `--reason` if it was ever re-cut |

Reasoning for the inclusions and omissions:

- **Rebinned bins in, fine-binned bins out.** The rebinned histograms are what chi2, the
  p-value and BumpHunter are computed on, and a per-bin lock catches a rebinning or clipping
  regression that a scalar p-value could mask by coincidence. The fine-binned 2519/2695-bin
  `postfit` carries no independent information — it is a deterministic function of the six
  fitted parameters already recorded — so it would add ~10 000 floats per analysis to
  re-assert something already locked.
- **`data` as an integral, not per-bin.** `data` is an input, not a result. One integral
  catches "someone swapped the input file or changed the selection path", which the pins cannot
  see; per-bin data adds 122 numbers for no extra discrimination.
- **`FitParameters_*.root` is skipped entirely.** Its `postfit_params` was verified to be
  bin-for-bin identical to `fitResult.floatParsFinal()`, values *and* errors. Its presence in
  the directory listing is all that is left to check.
- **Directory listing in.** One line, ~20 stable filenames, and it catches the loudest J50
  failure mode: the masked set silently not produced, or `BHresults.json` missing.
- **`seed` and `npe` in.** Cheap insurance — a silent BumpHunter config change fails loudly
  rather than surfacing as an unexplained p-value shift.
- **Skipped:** `edm` (a convergence diagnostic that wanders without meaning), `nllscan` (an
  EDM-plot TTree), `combWS` (a whole workspace), `h2_cov`/`h2_cor` (the errors they yield are
  already locked), the 10001-element arrays inside `pyBHresult`, and all logs and PDFs.

Baselines are captured **from the two runs already on disk** — `run/run_481_3000_sixPar/` and
`run/run_J50_302_2997_sixPar/` — so the recorded reference is exactly the state the CHANGELOG
documents. Written with `indent=1, sort_keys=True`; ~4 kB for J100, ~11 kB for J50. Python
floats round-trip exactly through `json`.

### 4. Tolerances

Per-class, as specified by the reviewer. Comparison is `abs(a-b) <= atol + rtol*abs(b)`.

| Quantity class | rtol | atol |
|---|---|---|
| Fitted parameters and errors, `minNll`, `chi2`, `chi2/ndof`, `postfit` bin contents, `data` integral | 1e-6 | 1e-8 |
| p-values — chi2 bin 6, BumpHunter `global_Pval`, `significance` | 1e-5 | 1e-8 |
| `status`, `covQual`, `nbins`, `npars`, `ndof`, `MaskMin`, `MaskMax`, `BlindRange`, `seed`, `npe`, directory listing | exact | exact |

A `--rtol` flag scales both float classes for the cross-machine case. The comparator flattens
both documents to dotted key paths and reports **all** mismatches, not just the first, so one
run shows the full blast radius. A missing or extra key is a failure in its own right — the
masked set appearing where it should not is real physics, not noise. Keys recording the
observed environment (ROOT version, active view) are printed as notes and never fail: the ROOT
version legitimately differs between a bare shell and a sourced one, and failing on that would
train people to ignore the harness. Pin drift is `env`'s job and fails there; drift in the
versions that cannot be pinned is also `env`'s job and warns there, against the record in the
baseline provenance (§1).

### 5. `check` — the entry point

Runs `env` and the four input hashes first and stops if either fails — a moved number is not
worth diagnosing until the stack is known good and the inputs are known untouched. `env`'s
version warnings (§1) do not stop it, but they are printed before the comparison so that a
mismatch further down is read with them already in view: if numpy moved, that is the first
suspect for a shifted `global_Pval`, and nobody should have to go looking for it. Then runs
each driver with `OUT_DIR` set to a scratch directory so `run/` is never touched, and compares
each output against its baseline.

Two speeds, because this will be run repeatedly rather than once:

| Command | Covers | Time |
|---|---|---|
| `check --quick` | J100 only — no BumpHunter masking path | ~1 min |
| `check` | both analyses, including J50's masked refit | ~6 min |

`--quick` exists because a six-minute check after every edit will be skipped, and a check that
is skipped protects nothing. It catches the large majority of regressions while iterating; the
full run is what gates a commit or a merge.

Allow 1800 s per driver, *not* 300 — a previous J50 run was killed mid-extraction by exactly
that. Do not gate on the drivers' exit codes: XMLReader and quickFit only warn on failure and
still return 0, so the baseline diff is the failure detector. The scratch directory is left in
place — a few MB, and on a failure you want the ROOT files.

`check --from DIR` compares an output directory produced some other way. That matters here: a
large refactor may rename the drivers or the run directories, at which point the built-in
`ANALYSES` table is stale and `--from` is the escape hatch until it is updated.

### 6. Close the gaps

| Change | File |
|---|---|
| Delete the dead, unpinned installer that contradicts the one that actually runs | [scripts/install_roofitext.sh](../scripts/install_roofitext.sh) |
| Delete the inert submodule declaration | `.gitmodules` |
| Repoint the three clone URLs at GitHub and drop the unverifiable `--branch` flag; SHA pins unchanged | `install.sh` lines 3, 10, 17 |
| Fix the venv row (`LCG_105` → `LCG_102a`, and what is actually installed in it), add a RooFitExtensions `ba94bfcb…` row, mark `lsetup cmake` unpinned | [README.md](../README.md) pins table |
| Drop the stale `requirements.txt` sentences | `README.md:54`, `CLAUDE.md:34-35` |
| Drop the "both submodules and gitignored" note, which stops being true | [CLAUDE.md](../CLAUDE.md) Conventions |
| "`tests/` is empty / no test suite" stops being true | [CLAUDE.md](../CLAUDE.md) Commands |

Deleting `scripts/install_roofitext.sh` rather than pinning its `git pull` is deliberate: the
file never executes, so pinning it would create a *second* pin that no build reads — exactly
the ambiguity this change exists to remove. Redirecting `install.sh:28` at it instead was
considered and rejected; the copies differ in three other ways (`$# -gt 0` vs `$# -gt 1`, an
unconditional `rm -r`, an extra cmake-config copy), so switching which one runs is a real
behaviour change for no benefit.

**Repoint `install.sh` at the public GitHub repositories and keep the SHA pins.** The CERN
GitLab URLs are unreachable. The four dependencies live at:

| Dependency | URL | Pin (unchanged) |
|---|---|---|
| xmlAnaWSBuilder | `https://github.com/tofitsch/xmlAnaWSBuilder` | `6b84050f...` |
| quickFit | `https://github.com/tofitsch/quickFit` | `0408030b...` |
| workspaceCombiner | `https://github.com/tofitsch/workspaceCombiner` | `7d484ad3...` |
| pyBumpHunter | `https://github.com/scikit-hep/pyBumpHunter` | `91f49a62...` (URL already correct) |

Each of the three clone lines becomes a bare clone of the GitHub URL — and **drop `--branch
tofitsch_baseline_fit`**. The checkout of the pinned SHA on the following line already decides
the revision, so the branch flag only adds a name that must exist on the fork for the clone to
succeed at all; a default clone fetches every branch, so the pinned SHA stays reachable without
it. Ref enumeration on the forks is blocked by this repository's branch-scope hook, so that
branch name could not be confirmed to exist — one more reason not to depend on it.

All four SHAs stay exactly as they are: they are what is checked out on disk and what produced
the recorded results. This change fixes *where the code is fetched from*, never *which commit*.
The same stale GitLab URLs appear in `.gitmodules`, which this plan deletes outright.

`.gitmodules` deletion gets its own commit and CHANGELOG entry; it is unrelated to the harness.

### 7. Bookkeeping the repo's conventions demand

- **This plan**, archived as written — with any later change to the *design* made as a marked,
  dated amendment that says what it replaced, never as a quiet rewrite to match what happened —
  plus a row in the [plans/README.md](README.md) index and its short descriptive paragraph.
- **[CHANGELOG.md](../CHANGELOG.md)** — appended entries in the existing **Objective / Found /
  Added / Changed / Verified / Decided / Left alone** form, plus rows in the Contents list.
  Append only; do not edit earlier entries. **Verified** must carry the real numbers the
  baselines were cut from and the measured wall time of `check`.
- **[README.md](../README.md)** — a short "Reproducibility" section: the commands, what the
  baselines cover, what the tolerances mean, and when to re-cut a baseline (only when a physics
  change is *intended*, with the reason in the CHANGELOG).
- **[doc/IMPROVEMENTS.md](../doc/IMPROVEMENTS.md)** and
  **[KNOWN_ISSUES.md](../KNOWN_ISSUES.md)** — both new, both created in the first
  implementation step and updated in every step after it. See the standing rule below.
- `CLAUDE.md` already has uncommitted working-tree modifications — read it before editing.

## Using this while the repository changes

The baselines are cut **once, now, before the changes start**, from the two runs already on
disk — the last known-good state. They are the invariant. The files are not.

1. Make a change.
2. `python3 tests/repro.py check --quick` — J100, ~1 min — while iterating.
3. Before committing, and before any merge: full `python3 tests/repro.py check`, ~6 min, both
   analyses including the J50 masking path.
4. Commit only on PASS.

`--quick` skips the BumpHunter masking branch entirely, because J100's p-value sits above the
mask threshold. If the change touches `FindBHWindow.py`, the masking branch in `run_anaFit.py`
or anything in the pyBumpHunter path, `--quick` tells you nothing — go straight to full `check`.

For a pure refactor the expectation is not merely "within tolerance" but **bit-identical**:
same machine, same build, fixed seeds, single-threaded minimiser. The tolerances in §4 exist
for rebuilds and different hardware, not to absorb a refactor's sloppiness. A refactor that
moves a number at 1e-7 has changed the arithmetic, and that is worth understanding before it
is waved through.

**The baselines must never be re-cut to make a failure go away.** This is the one way the whole
plan fails in practice: a change moves a number, and the fastest route back to green is to
re-record. `record` therefore refuses to overwrite an existing baseline unless given
`--force --reason "…"`, and writes that reason, the date, the software pins and the input
hashes into the baseline file. Re-cutting becomes a deliberate, auditable act with a
justification attached rather than a silent one. A baseline is legitimately re-cut only when a
physics change is *intended* — and then the CHANGELOG entry states what moved, by how much, and
why that is correct.

**When `check` fails, read it in this order:** `env` (did the stack move?), then `files` (did an
input change?), then the failing quantities. Clean stack, untouched inputs and a moved output
during a refactor means the refactor changed the physics — which is exactly the finding this
plan exists to produce.

## Documentation is part of the change, not a follow-up

**Standing rule for every step of this work: a step is not complete until its documentation is
written, in the same commit as the code.** This does not need to be asked for per step. Work
reported as done without its documentation is not done, and should be sent back. The reviewer's
attention belongs on whether the change is right, not on chasing the write-up.

Two new files, plus the three that already exist:

| File | Holds | Updated |
|---|---|---|
| `doc/IMPROVEMENTS.md` *(new)* | **One** living document for the whole improvement effort: what the framework now does, why it was changed, and how it is meant to be used. Rewritten in place as things evolve — always describes the current state. | every step that changes behaviour, interfaces or usage |
| `KNOWN_ISSUES.md` *(new)* | Known bugs, limitations and deliberately unguarded edge cases, stated openly. | whenever one is found, fixed, or consciously accepted |
| [README.md](../README.md) | Orientation, environment pins, how to run. | when usage or pins change |
| [CHANGELOG.md](../CHANGELOG.md) | Append-only notebook: what happened, in order, entry per activity. Never rewritten. | every activity |
| `plans/` | Plans archived as written. | one per non-trivial change |

**One improvement document, not a folder of them.** The point of a single file is that there is
one place to look and one place to keep current. Splitting the improvement work across several
documents is how documentation goes stale: each one is individually plausible and collectively
nobody knows which is authoritative.

**`doc/IMPROVEMENTS.md` and `CHANGELOG.md` are not duplicates**, and the difference decides
where a given sentence goes. The changelog is a *notebook*: chronological, append-only, and
deliberately preserves what was believed at the time including mistakes. The improvement
document is a *description of the present*: it is edited freely, and anything in it that has
become untrue is a defect. "On 2026-09-16 the masking threshold was changed to 0.02 because …"
is a changelog entry. "The masking threshold is 0.02" belongs in the improvement document.

### KNOWN_ISSUES.md

**Recording is the obligation; fixing is a choice.** Not every problem needs to be fixed, and
not every edge case needs to be explicitly guarded — a framework this size would drown in
defensive code written for situations that never arise. What is not acceptable is a known
problem that is *undisclosed*, because the next person then rediscovers it as a wrong physics
number rather than as a documented limitation.

Each entry states: what it is, where it lives (`file:line`), what it affects, and whether it is
being left alone deliberately. An entry that says "known, deliberately not guarded, here is
what it would look like if it bit you" is a complete and acceptable entry.

The file starts populated, not empty — the surveys behind this plan already found nine, all
verified and all off the J50/J100 path, which is why they are disclosed rather than fixed here:

| Issue | Where |
|---|---|
| `SetSeed(0)` makes pseudo-data generation genuinely non-deterministic; the deterministic variant sits commented out on the line above | `python/generatePseudoData.py:66-67` |
| `setup_buildCombineFit.sh` does not exist, but is sourced by **eight** live call sites | `scripts/run_nloFit.sh:6` and 7 others |
| `install_quickFit_and_xmlAnaWSBuilder.sh` does not exist, but is sourced | `scripts/install_FrequentistFramework.sh:14` |
| `re.sub("PAR1", …)` runs before `PAR10`, corrupting any ten-parameter card. Harmless at five/six parameters | `python/run_anaFit.py:276-279` |
| XMLReader and quickFit only *warn* on failure and still return 0; nothing gates on their exit codes, so a failed fit looks like a successful one | `python/run_anaFit.py:44,71` |
| `gRand.SetSeed()` is a no-op — `TH1::FillRandom` samples from the global `gRandom`, so these are only accidentally reproducible | `python/InjectGaussian.py:67-68`, `python/InjectZprime.py:118-119` |
| Hardcoded personal checkout path, so the HTCondor path runs someone else's framework at an unknown version | `submission/condor_script.sh:19,24` |
| Absolute AFS/EOS paths in other people's accounts, live in tracked config | `config/dijetisrTLA/*`, `python/inject_zprime_dscblimits.sh` |
| Hardcoded input path returning *Permission denied*, and `--end` defaults to 1000 GeV | `python/createBinning.py` |

Issues this plan actively fixes — the dead `scripts/install_roofitext.sh`, the inert
`.gitmodules`, the unreachable GitLab URLs and the stale `requirements.txt` references — are
resolved rather than recorded, and belong in the CHANGELOG instead.

## Verification

1. `python3 tests/repro.py selfcheck` — pure logic, no ROOT, instant.
2. Confirm the repointed `install.sh` actually resolves: clone one dependency from its new
   GitHub URL into the scratch directory and check out its pinned SHA. If the branch-scope hook
   blocks it, run it by hand outside the agent. Do not skip this — an `install.sh` naming a
   reachable-looking but wrong remote is the exact failure this change exists to remove.
3. `python3 tests/repro.py env` on the current tree → all pins green. Before any baseline
   exists it must say it has no version record to compare against, and must not write one.
   After step 4, hand-edit a version in a baseline's provenance, re-run `env`, and confirm it
   warns with both values, still exits 0, and leaves the baseline exactly as it found it —
   `git diff` on the baseline must be empty afterwards. A record the tool can silently rewrite
   is not a record.
4. Record both baselines from the existing `run/` directories. Eyeball against the CHANGELOG:
   `minNll` 1259.1119375388664 and `p6` 0.0478363 for J100; rebinned `pval` 0.0024417, BH
   window 582–662, `global_Pval` 0.0322 for J50.
5. `python3 tests/repro.py check` end to end (~6 min) → both PASS against baselines cut from
   the *previous* run. This is the real proof — not that the tool round-trips its own output.
6. **Prove it can fail.** Perturb one background parameter range in
   `config/dijetTLA/background_dijetTLA_J100yStar06_sixPar.template`, re-run J100, confirm a
   readable mismatch, revert. A checker that has only ever printed PASS has not been tested.
7. Confirm `run/run_481_3000_sixPar/` is untouched and `git status` shows `run/` still
   untracked, with only the intended files staged.

## Risks

- **Whether the drivers survive being run as a subprocess is the one real unknown — settle it
  first, before writing anything else.** They source `scripts/setup_buildAndFit.sh` themselves,
  but `lsetup` comes from `atlasLocalSetup.sh` and if it is a shell *alias* it will not expand
  non-interactively. Probe with `OUT_DIR=/tmp/lockprobe bash scripts/run_anaFit_run2.sh`.
  Fallbacks, in order: `bash -c '. script'`; or document "source `setup.sh` first" and rely on
  the drivers' `if [[ -z $_DIRFIT ]]` guards.
- **`global_Pval` will be the first number to move on any LCG bump.** numpy reaches
  pyBumpHunter by leaking from the LCG view, and 10 000 pseudo-experiments are drawn from it.
  `seed=666` makes it deterministic for a fixed numpy, but it is quantised at 1e-4, so any
  shift will exceed the tolerance by far. Say so in the README, so such a failure is read as
  "numpy changed", not "the fit changed".
- **Cross-machine drift.** Different CPU, glibc or ROOT build shifts the last ULPs of the NLL,
  and quickFit's 8-round MIGRAD retry loop amplifies that. The 1e-6 tolerance absorbs normal
  drift; a rebuild that moves numbers further is a finding, not a bug in the harness.

## Out of scope

**Only the files that participate in a J50 or J100 run.** The other drivers
(`run_nloFit.sh`, `run_anaFit_syst.sh`, `run_anaFitLoop.sh`, `run_swiftFit.py`), the HTCondor
toy studies, the `bbyy` / `ttHyy` / `high_mass_diphoton` / `dijetisrTLA` flavours and the ~290
input spectra these two fits never open are all deliberately uncovered. No test is written for
any of them. If one of those paths is revived later it gets its own
baseline; bolting them on now would mean maintaining checks for code nobody runs, which fail
for reasons unrelated to these two analyses and train people to ignore a red result.

Two known problems are recorded and deliberately left alone, both off the J50/J100 path:
`python/generatePseudoData.py:67` uses `SetSeed(0)` and is genuinely non-deterministic, and
`scripts/setup_buildCombineFit.sh` is referenced by eight call sites but does not exist.
