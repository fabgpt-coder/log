---
date: 2026-04-28T23:10:00+02:00
type: feature-shipped
gitoma_commits: [6655038, ca6562c]
context: Layer0 cross-run memory client + PHASE 1.5/8 wire-in
verdict: ★★★ amnesia loop closed — gitoma now reads its own past + writes its own future per repo
---

# Layer0 cross-run memory — amnesia loop closed

The third structural unblock of the day, completing the
serata's arc:

1. `--plan-from-file` (commit `bc18a95`) — operator-curated plan path
2. CPG-staleness fix (commit `e95f658`) — orphan-symbol family closed
3. PHASE 7 diary hook (commit `abf1cff`) — bot self-narrates
4. **Layer0 client + wire-in (commits `6655038` + `ca6562c`) — bot remembers**

## What changed in run.py

PHASE 1.5 (pre-planner, LLM branch only — skipped on
`--plan-from-file` since curated plans don't need history):

```
[muted]Layer0: injected 6 prior-runs memories from
ns=fabriziosalmi__gitoma-bench-blast[/muted]
```

The query seed is the concatenation of currently-failing metric
display-names ("Documentation Code Quality Test Suite …"), so
the returned memories tend to be semantically related to the
work the planner is about to propose. Memories appended to the
existing `prior_runs_context` channel (same channel Occam
Observer's agent-log feeds), under a clearly-labeled section
header so the LLM treats them as ground truth.

PHASE 8 (post-success, alongside PHASE 7 diary):

```
[muted]Layer0: ingested 3 memories into
ns=fabriziosalmi__gitoma-bench-blast[/muted]
```

Writes 1 + N + 1 short tag-rich memories per run:
- 1 plan-source line (LLM vs `plan-from-file:NAME`)
- N guard-firing lines (one per unique `critic_*.fail`, capped at 8)
- 1 outcome line (PR opened or no-PR)

## Why "the spider just got memory"

Without persistent cross-run memory, every gitoma run on a
given repo started from zero context. Same metrics → same
generic boilerplate tasks → same guard firings, dozens of times.
Now the loop is:

```
PRIOR RUNS                   PHASE 1.5            PHASE 2 PLANNER
(layer0 namespace)  ──>  query top-8 most-      ──>  generates plan
                         relevant memories            with prior context
                                                     baked in

                                              ↓

PHASE 8 INGEST       <──   PHASE 4 PR opened   <── PHASE 3 worker
(layer0 namespace)         + PHASE 7 diary         executes plan
+1 plan +N guards
+1 outcome
```

The bot can now SEE that it already shipped Ruff config 3 days
ago, that G18 fired on `core_helpers.py` last time, that PR #5
closed without merge with model gemma-4-e4b. The planner can
factor that in. Future-us thanks present-us.

## The spider web

This is the second confirmed leg-tool integration in gitoma's
`integrations/` directory:

- **occam-gitignore** (`gitoma/integrations/occam_gitignore.py`)
  — deterministic .gitignore generation
- **layer0** (`gitoma/integrations/layer0.py`) — vector memory

Each leg is independently shipped (PyPI / crates.io / its own
repo), independently tested, independently documented with
honest failure modes. gitoma orchestrates them via thin client
wrappers with a uniform silent-fail-open contract. The pattern
is the user's master plan, recently codified into a memory entry
("project_architecture_spider_web.md").

## What this enables next

- **Per-repo cross-run learning**: not yet — layer0 just stores +
  retrieves. The "learn from past failures" step is still on the
  planner side; we'd need to surface guard firings as explicit
  hints in the planner prompt. Next session.
- **Replay reproducibility**: combined with `--plan-from-file`
  and the trace JSONL, gitoma is now the closest it has ever
  been to fully reproducible benches.
- **Multi-machine memory federation**: each gitoma host can now
  point at a shared layer0 deploy; team-shared repo memory
  becomes possible.
- **Diary ↔ memory cross-link**: PHASE 7 diary is the human-
  readable narrative; PHASE 8 memory is the machine-readable
  ledger. Same events, different consumers. Both shipped today.

## State of the bot at end of evening

- 4 commits over ~7h: `bc18a95`, `e95f658`, `abf1cff`, `6655038`,
  `ca6562c` (5 actually — counting the wire-in)
- Orphan-symbol critic family (G16+G18+G19) closed live
- 2 spider legs integrated (occam-gitignore, layer0)
- Cross-run amnesia closed
- Self-narrating diary auto-runs
- Suite at 1715/1715

The bot you wake up to tomorrow morning is structurally
different from the one you went to sleep with last night.
