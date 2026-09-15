# Repository-relative output directory

**Written** 2026-09-15 · **Branch** `claude-skills` · **Status** Approved and implemented

Replace the hardcoded personal EOS output paths in the shell drivers with a default derived
from the repository location, so a fresh clone produces output without editing anything.

## The problem

Every driver hardcodes an absolute output path belonging to whoever last ran it:

| File | Line | Value |
|---|---|---|
| [scripts/run_anaFit.sh](../scripts/run_anaFit.sh#L3) | 3 | `/eos/home-t/tofitsch/tlafits` — another account, not writable here |
| [scripts/run_anaFit_run2.sh](../scripts/run_anaFit_run2.sh#L10) | 10 | `/eos/user/h/hhook/tlafits` |
| [scripts/run_anaFit_syst.sh](../scripts/run_anaFit_syst.sh#L24) | 24 | `/eos/user/l/lbazzano/TLA/FreqFrameOutputs/...` — set inline on `folder`, no `out_dir` at all |

A clone therefore fails or writes nowhere useful until the user finds and edits that line.
Both [README.md:63](../README.md#L63) and [CLAUDE.md:26](../CLAUDE.md#L26) instruct the reader
to do exactly that, so the manual step is currently documented policy rather than an oversight.

## What already exists

Most of the target state is in place, which keeps this change small:

- **The drivers already require the repository root as cwd.**
  [scripts/setup_buildAndFit.sh:5-8](../scripts/setup_buildAndFit.sh#L5-L8) aborts unless
  `xmlAnaWSBuilder/` and `quickFit/` are in `$PWD`, and every config, `Input/` and
  `./python/` path in the drivers is relative. So `$PWD` *is* the repository root in any
  invocation that can work at all.
- **`run/` is already the convention.** [setup.sh:28](../setup.sh#L28) and
  [scripts/setup_buildAndFit.sh:22](../scripts/setup_buildAndFit.sh#L22) both `mkdir -p run`,
  [python/run_anaFit.py:467](../python/run_anaFit.py#L467) already defaults `--folder` to
  `run`, [scripts/run_nloFit.sh:13](../scripts/run_nloFit.sh#L13) already writes to
  `run/outOfTheBoxFit`, and [.gitignore:6](../.gitignore#L6) already ignores `run/`.

Nothing new has to be invented; the `anaFit` drivers simply do not use the convention the
rest of the repository already follows.

## The change

One assignment per driver:

```bash
out_dir=${OUT_DIR:-$PWD/run}
```

`$PWD` is the repository root by the invariant above. `OUT_DIR` preserves the existing
workflow of writing to EOS without editing a tracked file — see the quota note below, which
is the reason the override is part of the change and not a later refinement.

Per file:

1. **[scripts/run_anaFit.sh](../scripts/run_anaFit.sh)** — replace line 3; move the
   `mkdir -p $out_dir` on line 5 to *after* `. scripts/setup_buildAndFit.sh` on line 8, so the
   repository-root guard runs first. Today the `mkdir` happens before the guard, so running
   from the wrong directory would scatter a stray `run/` there before the script aborts.
2. **[scripts/run_anaFit_run2.sh](../scripts/run_anaFit_run2.sh)** — same two edits at lines
   10 and 13. Keep the `# not writable from this account` comment on line 11: it records why
   the path moved and that is worth more than the tidiness of deleting it.
3. **[scripts/run_anaFit_syst.sh](../scripts/run_anaFit_syst.sh)** — introduce `out_dir` the
   same way and rewrite line 24 as `folder=$out_dir/run_systematics_${rangelow}_${rangehigh}_${pars}Par`.
   The commented alternatives on lines 20-23 stay, per the convention in CLAUDE.md of
   preferring edits to the live line over deleting the record.
4. **[scripts/run_nloFit.sh](../scripts/run_nloFit.sh)** — line 13 becomes
   `folder=$out_dir/outOfTheBoxFit`, so `OUT_DIR` works uniformly across drivers. Already
   repo-relative, so this is consistency rather than a fix.
5. **Docs** — [README.md:63-64](../README.md#L63-L64) and
   [CLAUDE.md:26-27](../CLAUDE.md#L26-L27) change from "set `out_dir` first" to "defaults to
   `<repo>/run/`, override with `OUT_DIR`". [README.md:116](../README.md#L116) keeps the
   `$out_dir/run_<rangelow>_<rangehigh>_<n>Par/` shape, which is unchanged.
6. **[CHANGELOG.md](../CHANGELOG.md)** — a line recording what actually happened.

## The AFS quota caveat

This is the one thing that could make the change a regression, so it is settled up front
rather than discovered later.

The repository lives on AFS home (`/afs/cern.ch/user/h/hhook/FrequentistFramework`), and
`fs lq` currently reports **9,831,245 of 10,485,760 KB used — 94%, with a quota warning**.
Defaulting output into the repository therefore writes into a nearly-full volume.

Measured against that: one completed run directory is **793 KB**
(`/eos/user/h/hhook/tlafits/run_481_3000_sixPar`). A handful of interactive fits is
comfortably affordable; the danger is the toy studies, where
[submission/condor_handler.py](../submission/condor_handler.py) fans hundreds of fits out over
HTCondor (the spurious-signal, injection-linearity, background-stability and F-test chains
documented in [python/README.md](../python/README.md)).

So: **repo-relative `run/` is the right default for interactive single fits, and toy studies
must keep setting `OUT_DIR` to EOS.** Both README.md and CLAUDE.md need to say that
explicitly — otherwise this change trades an annoying manual step for a quota failure
partway through a long condor campaign, which is a strictly worse failure mode.

## Out of scope

Hardcoded paths that are **inputs**, not the analysis output location, and so are a separate
piece of work:

- [python/createBinning.py:10](../python/createBinning.py#L10) — reads `resolutionFits.root`
  from `tofitsch`'s AFS work area. This one is a live dependency of the rebinning path and is
  the most likely of these to bite someone.
- [python/pfe.py](../python/pfe.py) lines 27-43 — a personal scratch driver pointing entirely
  at `tofitsch`'s AFS and EOS areas.
- [python/InterpolateZPrime.py:8-9](../python/InterpolateZPrime.py#L8-L9) — reads
  `agekow`'s work area.

## Verification

`bash -n` on each edited script catches syntax, but does not show the output landing in the
right place, so it is not sufficient on its own.

The real check is one end-to-end run of
[scripts/run_anaFit_run2.sh](../scripts/run_anaFit_run2.sh), which is the driver known to work
(implemented and run 2026-09-15, per
[the Run 2 plan](2026-09-15-run2-dijet-tla-481-3000-sixpar.md)) and whose output is only
793 KB. Success is `run/run_481_3000_sixPar/` appearing **inside the repository** with the
same `PostFit_*.root`, `FitParameters_*.root` and `postFit.pdf` contents as the existing EOS
copy. A second run with `OUT_DIR=/eos/user/h/hhook/tlafits` set confirms the override still
reaches EOS.

Both runs are needed: the first proves the new default works, the second proves the escape
hatch the toy studies depend on was not broken.

## Rejected alternatives

- **`repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)`** — resolves the repository
  from the script's own location and so is correct even from the wrong cwd. Rejected because
  the drivers cannot run from the wrong cwd anyway: every config and `Input/` path in them is
  relative, so a wrong-cwd run fails seconds later regardless. Moving the `mkdir` after the
  existing guard fixes the only real symptom for one line instead of two.
- **`git rev-parse --show-toplevel`** — adds a git dependency to a run path that has none, and
  the sub-frameworks are themselves git repositories, so it invites confusion for no gain.
- **Auto-deriving an EOS path such as `/eos/user/${USER:0:1}/$USER/tlafits`** — would dodge
  the quota concern, but guesses at a location outside the repository and contradicts the
  stated goal of output landing in `run/`. `OUT_DIR` covers this case explicitly instead.
