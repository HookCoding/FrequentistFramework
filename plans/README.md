# Plans

Implementation plans written before the work they describe, kept so the reasoning behind a
change can be found later. Each file is archived **as it was written**, not edited to match
what happened afterwards — a plan is a record of intent, and quietly rewriting it to look
correct destroys the only thing it is good for.

What actually happened is in [CHANGELOG.md](../CHANGELOG.md), the work notebook. Where a plan
and the notebook disagree, the notebook is right.

## Index

| Plan | Written | Branch | Status |
|---|---|---|---|
| [Run 2 dijet TLA, 481–3000 GeV, six parameters](2026-09-15-run2-dijet-tla-481-3000-sixpar.md) | 2026-09-15 | `claude-skills` | Approved and implemented |
| [Repository-relative output directory](2026-09-15-repo-relative-output-dir.md) | 2026-09-15 | `claude-skills` | Approved and implemented |

### Run 2 dijet TLA, 481–3000 GeV, six parameters

Wiring the framework up to the Run 2 J100 mjj spectrum with the tile gap veto, added
2026-07-22 but unreferenced by anything in the repository. Covers de-hardcoding the postfit
channel name, making the chi2 rebinning configurable, and adding a Run 2 driver.

Implemented the same day. Two of its predictions were contradicted by the actual run and are
flagged at the top of the file.

### Repository-relative output directory

Every shell driver hardcodes an absolute EOS output path belonging to whoever last ran it, so
a fresh clone writes nowhere useful until that line is edited by hand. Replaces those with a
default derived from the repository location, plus an `OUT_DIR` override that the HTCondor toy
studies need because the repository sits on a nearly-full AFS volume.

Implemented the same day. Verified end to end: `scripts/run_anaFit_run2.sh` with no `OUT_DIR`
set now lands output at `run/run_481_3000_sixPar/` inside the repository.

## Adding a plan

Name the file `YYYY-MM-DD-short-slug.md`, add a row to the index above and a short paragraph
saying what it is for. Links inside a plan are relative to this folder, so repository paths
need a `../` prefix.

**Only plans for the branch that is checked out belong here.** Plans live in a personal
`~/.claude/plans/` directory that spans every project and branch, so they are not
interchangeable: a plan written against another branch describes files that may not exist here,
and copying one in imports that branch's state through the back door. Archive a plan in this
folder only when it was written for this branch.
