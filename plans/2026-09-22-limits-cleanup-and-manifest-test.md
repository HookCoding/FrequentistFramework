# Close the two defects in the stale-output fix

**Written** 2026-09-22. **Branch** `claude-skills`. Resolves
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issues 52 and 53.

## The problem

Both were raised by the Copilot review of 2026-09-22 10:44Z against the previous day's commit, and
both are defects in the fix for issue 49 rather than in the framework it repaired.

**52.** `derived_outputs()` names the `Limits_*.root` path only `if dolimit`, so a folder reused
without `--dolimit` keeps the previous run's limit file — the failure issue 49 exists to prevent,
one line below the comment explaining why the masked twins are cleared unconditionally.

**53.** `tests/test_run_outputs.py` says a product added to `run_anaFit.py` without being added to
`run_outputs.py` "makes these fail". It does not: both sides of the comparison are static, so
neither moves and the tests pass. The same claim sits in `run_outputs.py`'s module docstring and in
the changelog.

They are one plan because they are one mistake in two forms. The manifest is a hand-maintained
duplicate of what the producer writes, and the only thing that was supposed to hold the duplicate
honest turns out not to. 52 is what happens when nothing does.

## Scope, and what is deliberately not attempted

**Not attempted: making `run_anaFit.py` write through the manifest.** The review's comment offers
this as one option — "the production writes need to share the same manifest". It is the real
single-source-of-truth fix and it is the right shape in the abstract, but it means rewriting the
output-path expressions inside `build_fit_extract()`, which is the function that produces every
physics number this repository emits, to close a defect that has so far cost one stale file in a
driver that cannot run. The cost is not proportionate. This plan makes the *check* real instead, so
the duplicate is verified rather than trusted, and records the option here rather than losing it.

**Not attempted: the `mR{sigmean}` cards.** `_cards()` is also mode-conditional — in Z′ mode
(`sigwidth == -999`) the top and category cards are named after the mass point, so a folder used in
one mode keeps the other mode's cards. Unlike the Limits file this cannot be fixed by dropping a
condition: the mass points are unbounded, so the set of names a *previous* run might have written
is not knowable from this run's arguments. It is also the mildest case in the family — those cards
are XMLReader inputs, not results, and nothing reads a stale one. Recorded here as a known
limitation of the manifest rather than fixed.

## Sections

### §1 — Clear the Limits file unconditionally (issue 52)

Drop the condition in `python/run_outputs.py`, and with it the `dolimit` parameter: once the
answer does not depend on it, a parameter that could reintroduce this is worse than no parameter.
Update the call site in `run_anaFit.py`.

Three unit tests move, because the J50 baseline's recorded run has no Limits file while the derived
set will now name one:

- the J50 exact-equality test becomes an explicit difference of `{Limits_anaFit_sixPar_bkgOnly.root}`,
  which is as strong a statement and names the reason;
- the J100 difference set gains the same name;
- `test_limits_file_only_when_limits_are_requested` is replaced by its opposite,
  `test_limits_is_cleared_even_when_this_run_does_not_request_it`, which is the property the fix
  is for.

**Verification.** `python3 -m pytest tests/test_run_outputs.py`. Then the real check: plant a
`Limits_anaFit_sixPar_bkgOnly.root` in a scratch J100 run folder, re-run the driver, confirm it is
gone — the same shape of demonstration used for issue 49, and the one that shows the fix acts on a
file no test can reach.

### §2 — Make the claim true (issue 53)

Move the guarantee to where the producer actually runs. `_check_one()` in `tests/repro.py` already
computes `sorted(os.listdir(folder))` for a live run; assert that every name in it is one
`derived_outputs()` would delete, and fail the check naming any that are not. `ANALYSES` gains a
`wsname` entry per analysis, the one argument that cannot be derived from `stem`.

This is the assertion the docstring described:

- it runs against a **real run**, not a snapshot;
- it **survives a baseline re-cut**, which is what kills the protection that exists today;
- it is one-directional by design — every produced file must be in the manifest, but the manifest
  may name files this run did not produce, which is exactly what the masked twins and the Limits
  file are.

Then correct the claims, in the same section as the code:

- `tests/test_run_outputs.py`'s docstring — what these tests prove is that the manifest agrees with
  two recorded runs, without ROOT.
- `python/run_outputs.py`'s module docstring — point at `repro.py check` for the producer
  guarantee.
- `KNOWN_ISSUES.md` 52 and 53 → Fixed; `doc/IMPROVEMENTS.md`'s harness section gains the new
  assertion; a `CHANGELOG.md` entry, with a pointer added to the 2026-09-21 17:20 entry whose claim
  this corrects, per this repository's append-only rule.

**Verification, and this is the part that matters.** A net that has never been shown to catch
anything is what issue 53 is about, so the new assertion is tested by breaking the thing it
watches:

1. Add a throwaway writer to `run_anaFit.py` — one line dropping a file into `folder` — and leave
   `run_outputs.py` alone.
2. Run `tests/repro.py check --quick`. It must **FAIL**, naming that file as produced but not in
   the manifest. Today it would fail on `directory_listing` instead; the new message must be the
   one that appears, and must say which file and which manifest.
3. Revert the writer. `check` must pass again.
4. Full `check` on both analyses, both baselines untouched and not re-cut.

Run everything with the system `python3` and an unset `VIRTUAL_ENV`, per the trap recorded in
`doc/IMPROVEMENTS.md`.

## What this does not do

- **Issue 44, 47, 50, 51** — open and recorded, untouched.
- **No baseline re-cut**, under any outcome. If a listing moves, stop and report.
- **No change to what `check` compares.** The new assertion is an addition; the existing exact
  `directory_listing` comparison stays, because it catches the case where a file *stops* being
  produced, which the subset assertion by construction cannot.
