# Reconcile the documentation with the code after the decomposition

**Written** 2026-09-22. **Branch** `claude-skills-2`. Written before any of the work it describes.

## The problem

A review of the completed ten-section decomposition
([plans/2026-09-18-decompose-j100-j50-fit-path.md](2026-09-18-decompose-j100-j50-fit-path.md),
committed as `dc004e4` … `04257e6`) checked every documentation claim against the code it
describes. Six disagreements came out of it. None of them can put a wrong number in front of
anyone — every one is either a record that is wrong about what the code does, or a pointer that
now lands on unrelated code. That is precisely why they are worth closing: this repository's
defence against a silent physics error is that its written record is trustworthy, and six places
where it is not is how that defence stops being believed.

One of them is a fix the previous plan specified and nobody carried out, which a later entry then
recorded as done. That is the only one with a code change behind it, and it goes first.

**The reason this happened is worth naming, because it is structural.** `CLAUDE.md`'s rule that a
section's documentation belongs in `README.md` and `CLAUDE.md` — not only in `CHANGELOG.md` — was
added *during* §9, near the end of the work. Findings 2 and 6 below both predate it and are exactly
what it exists to catch. Findings 4 and 5 postdate it and slipped through anyway, because the rule
says to document what a section *changed* and says nothing about the references a section
*invalidated*. §4 of this plan proposes the convention that closes that gap.

## Scope

The six findings, each as its own section, ordered by how badly a reader is misled.

Only §1 changes code, and it deletes three lines. Everything else edits `README.md`, `CLAUDE.md`,
`KNOWN_ISSUES.md`, `CHANGELOG.md`, `plans/README.md` and four comments in `tests/`.

## Standing rules for this work

1. **No defect found here is fixed as code**, beyond §1's deletion, which a previously approved
   plan already called for. Issues 23, 41, 44, 47, 49, 50, 53, 55, 56, 57 and the PAR1/PAR10 table
   row stay open. This plan corrects the *record*, not the behaviour.
2. **`CHANGELOG.md` is append-only**, per its own header: a correction is a new entry plus a
   one-line pointer added to the entry being corrected, never a rewrite of it.
3. **`KNOWN_ISSUES.md` is corrected in place**, with the correction recorded in `CHANGELOG.md`.
   Precedent: issue 24, which was itself a stale claim in this file.
4. **No plan in `plans/` is edited to match what happened.** Where a plan was wrong, the correction
   lives in `CHANGELOG.md`. That rule is what makes finding 1 visible at all.
5. **No baseline is re-cut**, and `tests/repro.py check` must be green at §1's boundary.

---

## §1 — Delete the `locals()` dump, and correct the two records that disagree about it

### The finding

The 2026-09-18 plan's §3 says, in terms:

> **Deleted first, as its own commit:** the `locals()` dump at lines 250–252. It prints whatever
> local names happen to exist at that point, so it makes every later reordering a visible diff in
> the log for no benefit.

It was never deleted. It is live at [python/run_anaFit.py:571-573](../python/run_anaFit.py#L571-L573):

```python
    args_names = locals()
    for key, value in args_names.items():
      print(f"{key}: {value}")
```

The §3 CHANGELOG entry does not mention it — neither doing it nor deciding against it. Then the
§10 entry, [CHANGELOG.md:3192](../CHANGELOG.md#L3192), asserts it as settled fact: *"unlike the
`locals()` dump removed in §3"*.

This is the only place in the whole body of work where the record claims an outcome the code
contradicts.

### What changes

Delete the three lines. Two things were checked during the review and are restated here as the
justification, not re-derived during implementation:

- Nothing in the repository reads `args_names`; the only occurrences are its own two lines.
- `tests/repro.py` compares ROOT file contents, the run-directory listing and the baseline JSON.
  It reads no driver log text at all — its only `stdout` reads are `git rev-parse`/`status` and the
  version probes. Removing three `print` calls therefore cannot move its verdict, which is what the
  original plan claimed and what makes the deletion free.

Then the record, per standing rule 2: a new `CHANGELOG.md` entry saying what was found and done,
plus a one-line pointer on the §3 entry (the section that should have done it) and on the §10 entry
(which states it was done).

### Decision for review

The alternative is to keep the dump and correct only §10's claim. Deletion is the default here
because the 2026-09-18 plan chose it and that plan was approved — but it was approved as one line
inside a large plan and never separately discussed, so it is offered again rather than treated as
settled. The dump's only effect is roughly twenty-five lines of stdout per run; if it is wanted as
a provenance record of what `run_anaFit()` was called with, say so and §1 becomes a
correction-only section.

### Test

None. The dump is stdout that nothing parses, and a test pinning its *absence* would be brittle
for no benefit. Stated here rather than left as a gap.

### Verification

`bash tests/run_all.sh` — the unit suite, then `repro.py check` on both analyses, **not**
`--quick`. This is the only section that needs it, and it needs the full run because it is the only
one that touches code the drivers execute.

---

## §2 — Correct the XMLReader/quickFit exit-code claim in `README.md` and `CLAUDE.md`

### The finding

Three places still carry a claim that `KNOWN_ISSUES.md` explicitly retracted on 2026-09-18:

| Where | What it says |
|---|---|
| [README.md:184-185](../README.md#L184-L185) | "XMLReader and quickFit only warn on failure — they do not return a non-zero exit code. Check `quickFitLog_*.log`, not the exit status." |
| [CLAUDE.md:58-59](../CLAUDE.md#L58-L59) | "Both are called with `subprocess` and only *warn* on non-zero exit — check the log, not the return code." |
| [CLAUDE.md:115-116](../CLAUDE.md#L115-L116) | "XMLReader and quickFit warn on failure and still return 0, so a failed fit looks like a successful one" |

`KNOWN_ISSUES.md`'s own table row is struck through, marked **Fixed 2026-09-18**, and goes further
— it says the original wording was wrong even about the *old* behaviour: a nonexistent card makes
XMLReader exit 139, not 0.

These are the two files a newcomer and the next agent session read first, and they currently
instruct both to ignore an exit status that now stops the run.

### What is actually true

- `execute_checked()` ([python/run_anaFit.py:54-66](../python/run_anaFit.py#L54-L66)) raises
  `RuntimeError` on any non-zero exit. XMLReader ([:163](../python/run_anaFit.py#L163)), quickFit
  ([:173](../python/run_anaFit.py#L173)) and quickLimit ([:522](../python/run_anaFit.py#L522)) all
  go through it.
- The hole that remains is the **soft** failure: a fit that runs, does not converge and exits 0.
  `report_fit_quality()` → `_require_covqual()` ([:138-160](../python/run_anaFit.py#L138-L160))
  raises when `covQual` is below `--mincovqual`; that is what catches those, not the exit code.
- Two calls do still discard their status deliberately: `plot_edm.py`
  ([:179](../python/run_anaFit.py#L179)) and `createBinning.py`
  ([:221](../python/run_anaFit.py#L221)). The second is the open half of the 2026-09-17 rebin-pair
  plan's §2 — see §6.

### What changes

`README.md`'s bullet and `CLAUDE.md`'s Architecture §3 sentence are rewritten to the above: the
exit code is now checked and stops the run, and the log is where the *non-convergence* case shows
up. Both point at issue 40 rather than at the retracted row.

`CLAUDE.md:115-116` is different in kind: it is an *example illustrating the triage principle*, not
a description of the code, and the principle it illustrates is correct. It is rewritten rather than
deleted — the soft-failure case is a better example of "a fit that succeeds with a silently wrong
number" than the retracted one ever was, and it is true.

### Not a regression from the decomposition

The fix that made these claims false landed 2026-09-18 10:05; §1 of the decomposition began 17:40
the same day. This is inherited, and it is in this plan because §9's documentation rule would catch
it today and did not exist then.

### Verification

No code change, so no `check`. Each rewritten claim is read back against the code it describes and
against the `KNOWN_ISSUES.md` row that retracts the old one.

---

## §3 — Correct issue 56's failure mode, and record the null-`TFile` dereference behind it

### The finding

Issue 56 — and the §10 CHANGELOG entry, which says the same thing — describes a missing
`FitParameters_*_bkgOnly.root` as something that *"reaches the drawing loop instead of the guard's
clear error, and crashes on the params page instead."*

Measured 2026-09-22, by running the macro against a directory holding only
`PostFit_anaFit_sixPar_bkgOnly.root`: it does not reach the drawing loop. It segfaults inside
`load_histograms()`, root exits 129, and the `exit(1)` guard, the `BHresults.json` read and the
drawing loop are all never reached.

The cause is a different defect from the one issue 56 describes. The params file is dereferenced
under the *postfit* file's guard:

- [plot_postfit.cpp:82](../plot_postfit.cpp#L82) — `inputs.native_params->Get<TH1D>(...)` sits
  inside `if (inputs.native)`
- [plot_postfit.cpp:92](../plot_postfit.cpp#L92) — the masked twin, inside `if (inputs.masked)`

So a null `TFile*` is dereferenced whenever the postfit file opens and its params file does not.
Issue 56 describes a null *histogram* reaching the drawing loop; that is a real second-order
consequence, but it is unreachable because the crash happens two steps earlier.

**Preserved, not introduced.** The pre-§10 code has the identical structure — `in_file_native` and
`in_file_native_params` guarded together in exactly the same way. §10's split is faithful here.

### What changes

Issue 56's **What**, **Where** and **Affects** are rewritten to the measured behaviour, covering
both the native and the masked site. A one-line pointer goes on the §10 CHANGELOG entry, which
repeats the wrong description. `README.md`'s §10 bullet refers to issues 56 and 57 by number only
and needs no change.

**Issue 57 is confirmed correct as written and is not touched.** It was reproduced the same way — a
`BHresults.json` present with no masked ROOT files — and behaves exactly as the entry says: the PDF
is opened, and the crash comes in `draw_panel()`'s `h_second->Draw()` on the params page.

### Decision for review

Whether to *fix* the guard rather than only document it. It is one condition, twice.

Recommendation: document only. It fails closed — a segfault, never a wrong number — which on
`CLAUDE.md`'s triage rule is the lower tier; neither locked baseline reaches it, so a fix cannot be
verified against either; and it would leave 56 and 57 in inconsistent states, one fixed and one
recorded, for the same class of defect on the same file. Offered because it is two lines and the
counter-argument is real: `plot_postfit.cpp` has no test that would notice either way.

### Verification

No code change under the recommendation. The measurement is recorded in the new `CHANGELOG.md`
entry with its exact reproduction, so it can be re-run rather than taken on trust.

---

## §4 — Repoint the cross-file references the decomposition moved

Two halves, separately committable if the second runs long.

### §4a — the four references inside `tests/`

These are the only written record of four cross-file contracts that nothing else in the repository
checks, and §10 rewrote the file all four point into.

| Reference | Says | Where it actually is now |
|---|---|---|
| [tests/test_run_anafit_commands.py:115](../tests/test_run_anafit_commands.py#L115) | `plot_postfit.cpp:34` | `open_inputs()`, `plot_postfit.cpp:43` |
| [tests/test_extract_fit_parameters.py:6](../tests/test_extract_fit_parameters.py#L6) | `plot_postfit.cpp:64` | `load_histograms()`, `plot_postfit.cpp:82` and `:92` |
| [tests/test_find_bh_window.py:313](../tests/test_find_bh_window.py#L313) | "the regex `plot_postfit.cpp:119` builds" | `get_val()` — the regex changed **file** in §10, to `plot_postfit_utils.h:12` |
| [tests/test_find_bh_window.py:319](../tests/test_find_bh_window.py#L319) | `plot_postfit.cpp:127-130` | `plot_postfit()`, `plot_postfit.cpp:300-303` |

The assertions are unaffected and stay exactly as they are — these are comments explaining why each
assertion exists. Only the comments change.

**The convention this section proposes, and the evidence for it.** Name the function, not the line.
The issues filed *during* the decomposition — 53, 55, 56 and 57 — cite function names and came
through ten sections of rewriting untouched; every reference that cited a line number did not. A
line number into a file someone else may split is a pointer with a short half-life. If this is
agreed, it goes into `CLAUDE.md`'s Conventions and traps as one line, so the next session writes
references that survive the next refactor.

### §4b — the references in `KNOWN_ISSUES.md`

Every reference into a decomposed file is stale. Two different treatments, because the entries are
two different kinds of thing.

**Open issues — repoint by function name.** These describe code that exists now, and a reader
follows the pointer to go and look at it.

| Issue | Says | Actually |
|---|---|---|
| 23 | `FindBHWindow.py:88`, `:91` | `_run_scan()` |
| 41 | "the bin loop in `getChi2` (lines 59–76)" | `_compute_chi2_terms()` — the loop left `getChi2` in §2 |
| 44 | `plot_postfit.cpp:29` (correct), `:238` (the draw) | `:238` is now the mask-range text; the lumi draw is in `draw_panel()` |
| 47 | "the `if [[ -n $anafit_failed ]]` block" in both drivers | `_report_failure()` in `scripts/lib/anafit_driver.sh`, moved there by §9 |
| 49 | `ExtractPostfitFromWS.py:270`, working version `:234` | `Extract()`'s background-only block |
| 50 | `PreFit.py:106-119`, limits `:92-93` | `_find_best_parameter_sets()`; limits in `_select_fit_function()` |
| table row | `run_anaFit.py:276-279` (PAR1/PAR10) | `_substitute_prefit_parameters()` |

**Closed issues — mark the references historical, do not repoint them.** Issues 39, 42, 43, 45, 46,
48, 51 and 54 describe code that no longer exists in the shape they describe. Repointing them would
be a fiction; saying "at the time, `run_anaFit.py:88`" is true. Issue 54 already does exactly this
("the `else` at the old lines 433–439") and is the model to follow.

### Verification

No code change in either half. `python3 -m pytest tests -q` after §4a, to confirm the comment edits
left the suite at 253 green. Each repointed reference in §4b is followed and confirmed to land on
what its entry describes.

---

## §5 — Correct two counts in `CHANGELOG.md`

Both are small, both are append-only corrections (standing rule 2), and they share one new entry.

**§7's entry says `_run_scan` "is an addition to the plan's list of six".** The plan's §7 names
**five** functions — `_load_histograms`, `_crop_data_to_bkg_range`, `_configure_hunter`,
`_mask_window`, `_write_results`. `_build_parser` is a second, undisclosed addition, so the module
has seven where the plan specified five. Both additions are good ones; only the accounting is
wrong.

**§10's entry says "One inert local deleted"**, of `bool is_rebinned{false}`. A second pair was
inert and was *kept*: the original's `native_nbkg` and `masked_nbkg` are computed and never drawn,
and survive the split as `FitSummary::nbkg` — declared at
[plot_postfit.cpp:110](../plot_postfit.cpp#L110), written at
[:128](../plot_postfit.cpp#L128), read nowhere. Keeping it is defensible and is faithful
preservation; the entry as written reads as though nothing dead is left in the file.

**Not in scope: removing `FitSummary::nbkg`.** It would be a behaviour-neutral tidy on the one file
whose only verification is a raster diff against a pre-change PDF, for no reader's benefit.

---

## §6 — Bring `plans/README.md`'s index up to date

Three rows still read "Approved, implementation in progress".

- **The decomposition plan.** All ten sections are implemented, tested, documented and committed.
  Its narrative paragraph also stops at what the plan intended and never records an outcome, unlike
  every other completed plan's. It gains one in the same shape as the others: what was built, where
  the plan was contradicted by measurement and where those corrections live, and what was found and
  left recorded.
- **The J50 plan.** Implemented 2026-09-15, with a recorded baseline and a driver `repro.py check`
  exercises on every full run.
- **The rebin-pair guard.** §1 was fixed 2026-09-17 19:15 (issue 46). §2, "Make the fallback
  audible", is **verified unimplemented**: `_resolve_binning()`
  ([python/run_anaFit.py:203-224](../python/run_anaFit.py#L203-L224)) still discards
  `createBinning.py`'s return code and still prints no warning that it is falling back to a binning
  that stops at 1000 GeV. The row should say which half is done rather than leave the whole plan
  looking unfinished — or looking finished, depending on which way the reader guesses.

**Not in scope: implementing that §2.** It is a live, unimplemented section of an approved plan and
deserves its own decision, not a footnote in a documentation pass. §6 records its status; acting on
it is separate.

---

## Verification

Per section, before stopping for review:

```bash
. setup.sh
bash tests/run_all.sh                         # §1 only - unit suite, then both analyses
python3 -m pytest tests -q                    # §4a - confirm 253 still green after comment edits
```

Sections 2, 3, 5 and 6 change no code and no test, so neither command can say anything about them.
Their verification is reading each corrected claim back against the code or the file it describes,
and that is stated per section rather than implied.

## Effort

About half a day. §4b is the bulk of it; §1 is the only section whose verification costs minutes
rather than seconds.

## What this does not do

- It does not fix any defect it repoints. Issues 23, 41, 44, 47, 49, 50, 53, 55, 56, 57 and the
  PAR1/PAR10 row stay open and unfixed.
- It does not add the null-`TFile` guard in `plot_postfit.cpp`, unless §3's decision goes the other
  way.
- It does not implement the rebin-pair plan's §2, or remove `FitSummary::nbkg`.
- It does not touch `tests/repro.py`, either baseline, or any archived plan.
- It re-cuts nothing.

## Files

**Changed:** `python/run_anaFit.py` (§1 only, three lines deleted), `README.md`, `CLAUDE.md`,
`KNOWN_ISSUES.md`, `CHANGELOG.md`, `plans/README.md`, `tests/test_run_anafit_commands.py`,
`tests/test_extract_fit_parameters.py`, `tests/test_find_bh_window.py`.

**Added:** this file.

**Untouched:** `tests/repro.py`, `tests/baseline_J100.json`, `tests/baseline_J50.json`,
`plot_postfit.cpp`, every archived plan, and the four pinned sub-framework clones.
