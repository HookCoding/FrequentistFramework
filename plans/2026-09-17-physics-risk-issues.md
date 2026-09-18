# Close the issues that can reach a physically wrong result

**Written** 2026-09-17. **Branch** `claude-skills`. Covers `KNOWN_ISSUES.md` issues **40**, **39**
and **48**, plus the unnumbered table entry *"XMLReader and quickFit only warn on failure and still
return 0"*.

Scope chosen by the repository owner: the set identified as able to lead to a physically wrong
result or a wrong conclusion. Issue 44 is excluded — it cannot be finished without luminosity values
that are nowhere in this repository. The fail-closed harness issues (23, 28–31) are excluded as the
lowest tier under [CLAUDE.md](../CLAUDE.md)'s triage rule.

## The through-line

The framework can currently finish a run, print `STATUS OK`, and hand over a result whose quality
nobody checked. Three of the four sections below are the same defect at different depths: a hard
failure that is only warned about (§2), a soft failure that is never looked at (§1), and a verdict
whose definition was never settled (§4). §3 is the one place where a correct result is displayed as
the wrong one.

**What protects the locked analyses and what does not.** For J50/J100 `tests/repro.py check` pins
the recorded outputs, including `status` and `covQual`, so a degradation fails. For any new
configuration nothing checks, and there is no baseline. Every section below is aimed at that gap.

## Sections

### §1 — Report fit status and covariance quality (issue 40)

Nothing in `python/` or `scripts/` reads `status()` or `covQual()`. Every recorded fit ran with a
covariance matrix MINUIT forced positive-definite (`covQual=2`, ~0.005 added to the diagonal) while
the log's last word is `Fit Summary of POIs (STATUS OK)`. Central values are sound — the minimum is
`Valid` and the retries land on the same FCN — but the **errors** come from that forced matrix, and
the errors are what the spurious-signal, injection-linearity and limit studies consume.

Read `status()` and `covQual()` from the `fitResult` in `FitResult_*.root` after each fit and print
them on one clear line.

**The refusal must be opt-in and permissive by default.** All three recorded fits are `covQual=2`;
making that a refusal would break both locked analyses and `tests/repro.py check` on the first run.
So: always print, and add a flag (defaulting to accept `covQual=2`) that refuses below a chosen
quality. Whether `covQual=2` *should* be acceptable stays a physics judgement for the owner — this
section makes the property visible and the decision expressible, and deliberately does not make it.

**Verification.** The line appears for both analyses with the values the baselines already record;
`tests/repro.py check` passes unchanged; the refusal flag set to demand `covQual=3` refuses, and
that refusal is readable rather than a traceback.

### §2 — Stop on a failed workspace build or fit (the unnumbered table entry)

`build_fit_extract` runs `XMLReader` and `quickFit` and only prints `WARNING: Non-zero return code
… Check if tolerable` before carrying on into extraction.

**The recorded entry's wording is wrong and should be corrected as part of this section.** It says
the binaries "only warn on failure and still return 0". Tested directly: `XMLReader` on a
nonexistent card exits **139** (SIGSEGV), `quickFit` on a nonexistent workspace exits **139**.
`quickFit` with no arguments at all exits 0, but that is a usage no-op, not a failed fit. So hard
failures *are* signalled and are currently being ignored — which makes this fixable, where the entry
as written implies it is not.

Gate on the return codes: stop rather than warn. Hard failures are then caught here, and soft
failures — a fit that runs, does not converge and exits 0 — are caught by §1. The two sections are
complementary and neither covers the other.

**Verification.** `tests/repro.py check` passes, confirming both binaries exit 0 on the recorded
runs and that the gate does not fire on good input. A deliberately broken card is refused at the
build step instead of proceeding to extraction.

### §3 — Plot the fit that was accepted, and say which it is (issue 48)

Both drivers plot a fixed filename, so when a run is accepted only after masking, `postFit.pdf`
shows the fit that was **rejected**. This is live in the recorded J50 result: unmasked rebinned
p = 0.00248 (rejected), masked = 0.01906 (accepted), threshold 0.01.

Emit both, labelled, rather than substituting one for the other. Selecting the masked file when it
exists — the review comment's first suggestion — would make `postFit.pdf` mean one thing for J100
and another for J50 with nothing saying which, which is the same defect in a new place.
`plot_postfit.cpp`, which already loads both and labels the masked panel, is the working model.
Both drivers, not only J50's.

**Verification.** A J50 run produces a labelled plot for each fit and the accepted one is
identifiable without opening a ROOT file; a J100 run, which writes no masked files, produces the
unmasked plot and no empty second one. `check` passes — it records `directory_listing`, so any new
plot filename must be reflected in the baselines, and **if it is, that is a baseline change and
needs the owner's explicit approval before `record` is re-run.**

### §4 — Settle which histogram the p(chi2) gate reads (issue 39) — **blocked on a decision**

The initial gate reads `<channel>_rebinned`; the masked accept/reject reads
`<channel>_bkgonly_rebinned`. They differ by 1–2% relative, and the code comment shows the choice
was never made.

**This section cannot be implemented until the owner picks one.** It is a statistics question, not
a bug with a correct patch — which is why issue 39 was filed rather than fixed.

What the plan can settle is that the change is *safe*: from the recorded baselines, every verdict is
unambiguous against the 0.01 threshold under either choice (J100 unmasked 0.0148562 / 0.0148783;
J50 unmasked 0.0024417 / 0.0024813; J50 masked 0.0188064 / 0.0190617). So unifying on either
histogram preserves all three recorded verdicts and `check` should pass either way — the risk is in
future fits landing between the two values, which is exactly the case the current code decides by
accident.

Once chosen: use it in both branches, delete the unresolved comment, and state the reason in a
sentence. If the switch turns out to be deliberate — the masked fit's normalisation differs, which
the comment above it hints at — then documenting that is the whole fix.

**Verification.** `check` passes; the recorded verdicts are unchanged; the comment no longer asks a
question.

## Order, and why

§1 and §2 first: together they close "the framework finished and nobody checked", and neither needs
a decision from anyone. §3 next — it is the only one that changes what a reader sees, and it may
touch the baselines, which needs approval. §4 last, and only if the owner settles it.

## What this does not do

It does not fix issue 44 (no luminosity values in the repository), issue 47 (recorded, trivial, out
of this scope), issue 41 (latent, verified untriggered), or the fail-closed harness issues. It does
not re-cut any baseline: if §3 requires one, that stops for approval rather than proceeding.
