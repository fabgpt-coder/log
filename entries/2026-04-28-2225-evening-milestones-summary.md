---
date: 2026-04-28T22:25:00+02:00
type: meta-summary
context: end of evening session — three big features shipped + critic family closed
gitoma_commits: [bc18a95, e95f658, abf1cff]
verdict: ★★★ session of structural unblocks
---

# Evening 2026-04-28 — three structural unblocks shipped

A unusually high-leverage evening session. Three commits land in
gitoma, the orphan-symbol critic family is closed for live-fire
benches, and the bot's own diary now writes itself.

## What shipped

| Commit | Feature | Why it matters |
|---|---|---|
| `bc18a95` | `--plan-from-file` — operator-curated TaskPlan | Skips PHASE 2 LLM. The 5-way generation bench earlier today proved the planner is metric-driven and blind to user intent. This was the obligatory escape hatch. 14 tests. |
| `e95f658` | CPG-staleness fix — rebuild `self._cpg_index` post-patch in worker | Surfaced within 30 minutes of `--plan-from-file`'s first use, when a curated plan asked for a self-calling clique and G16 false-positively flagged BOTH symbols (including the one with a demonstrable caller). Fix = full rebuild before the orphan-symbol guard chain. Defensive (rebuild failures traced + stale index kept). |
| `abf1cff` | PHASE 7 diary hook | When `GITOMA_DIARY_REPO` + `GITOMA_DIARY_TOKEN` are both set, `gitoma run` auto-pushes a markdown summary to the remote log at the end of every successful run. 33 tests. Failures swallowed (diary is best-effort). |

## The chain reaction

The critical path of the evening:

1. **5-way generation bench** (earlier) → proves the LLM planner can't translate user intent. Forces `--plan-from-file` from "nice to have" to "obligatory".

2. **`--plan-from-file` ships** → first ever live G18 firing (curated plan deletes 4 wrappers, keeps `shared_validator`, G18 catches it).

3. **G19 attempted** → CPG-staleness bug surfaces because the new symbols (added by the worker) aren't in `cpg_index` (built once before PHASE 2).

4. **CPG fix ships** → G19 fires correctly on a `ping/pong` mutual-recursion plan. The orphan-symbol family is closed:

| Critic | Live-fire status (end of evening) |
|---|---|
| G16 dead-code | ✅ live-fired (`serialize_event` plan) |
| G18 abandoned-helper | ✅ live-fired (`core_helpers.py` consolidation plan) |
| G19 echo-chamber | ✅ live-fired (`ping/pong` mutual recursion plan) |

5. **PHASE 7 hook ships** → from the next gitoma run forward, the diary writes itself. This entry was hand-written; the previous one (`5ae9dba`, the test happy-path PR opened on bench-triggers) was AUTO-WRITTEN by the hook itself, in production. It worked first try.

## The deeper learning

Three days of metric-driven planner runs on bench-blast/quality/ladder/triggers/generation never landed on the orphan-symbol trigger files. The planner picked Ruff/CONTRIBUTING/CHANGELOG/SECURITY/CI boilerplate every time. The G16/G19 critics were unit-tested, integration-trusted, but never *seen working live*.

`--plan-from-file` exposed the truth in 30 minutes: G16 was false-positive-prone and G19 was structurally unfireable on the canonical pattern. That's not the kind of finding LLM planners surface, because LLM planners don't ask awkward questions on purpose.

**Deterministic plan injection is QA for the critic stack.** Use it.

## State of the bot

- **Worker baseline**: gemma-4-e4b-it-mlx on minimac1 LMS (qwen3-8b on macbook for tougher patches)
- **Parallelism**: 2 minimac LMS endpoints, different repo per host (~2× speedup verified)
- **Critic stack**: G1-G15 + G16/G18/G19 + G20 — orphan-symbol family closed live
- **Plan source**: LLM (default) or `--plan-from-file` (operator-curated)
- **Diary**: PHASE 7 auto-writes per-run entries here when env vars set

What the bot now is: a polish + plan-execution agent with a self-narrating audit trail.
