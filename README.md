# fabgpt-coder — operations log

Public timeline of what `fabgpt-coder` (the gitoma-powered AI agent
operated by `fabriziosalmi`) does across all repos. One entry per
gitoma run — including the runs that DIDN'T ship a PR, because
those tend to be where the most useful learnings live.

Each entry has machine-readable frontmatter (date, repo, PR url,
model, endpoint, subtasks done, wall, guard firings, verdict)
plus a human-readable summary.

This log is append-only. Entries are immutable once written.

---

## 2026-04-27 — opening day

Heavy bench day: 9 gitoma runs, 5 PRs landed, 4 runs that surfaced
runtime issues worth recording. Establishes the operational
baseline (LM Studio everywhere, exo dropped, gemma-4-e4b-it-mlx
default worker) and pins the reasoning-distilled trap + the
JIT-Model-Loading mandate for LM Studio Server API.

| When | Repo | PR | Model · Endpoint | Subtasks | Verdict |
|------|------|----|------|----------|---------|
| 14:17 | bench-blast | [#2](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/2) | Qwen3.6-35B-A3B-4bit · exo 2-node | 5/12 | exo eviction mid-run — [details](entries/2026-04-27-1417-bench-blast-qwen36-exo.md) |
| 20:31 | bench-blast | [#3](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/3) | qwen/qwen3-8b · LMS locale | 8/12 | clean baseline — [details](entries/2026-04-27-2031-bench-blast-qwen3-8b.md) |
| 20:48 | bench-blast | — | qwen3-4b-distilled · LMS | 0 | ❌ reasoning-baked timeout — [details](entries/2026-04-27-2048-bench-blast-qwen3-4b-distilled.md) |
| 21:09 | bench-blast | [#4](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/4) | gemma-4-e4b-it-4bit · exo single-node | **7/7 ★** | clean win — [details](entries/2026-04-27-2109-bench-blast-gemma-exo-single-node.md) |
| 21:34 | bench-blast | — | Qwen3.6-27B-4bit · exo cluster | 0 | ❌ planner empty response — [details](entries/2026-04-27-2134-bench-blast-qwen36-27b-exo-cluster.md) |
| 21:40 | bench-blast | — | gemma-4-e4b · exo TENSOR sharded | 0 | ❌ TCP/IP sync DOA — [details](entries/2026-04-27-2140-bench-blast-gemma-exo-tensor-sharded.md) |
| 22:27 (parallel A) | bench-blast | [#5](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/5) | gemma-4-e4b-it-mlx · LMS minimac1 | 4/7 | channel error mid-run — [details](entries/2026-04-27-2227a-bench-blast-gemma-lms-minimac1.md) |
| 22:27 (parallel B) | bench-quality | [#1](https://github.com/fabriziosalmi/gitoma-bench-quality/pull/1) | gemma-4-e4b-it-mlx · LMS minimac2 | **8/12 ★** | first quality PR + G15 live-fired — [details](entries/2026-04-27-2227b-bench-quality-gemma-lms-minimac2.md) |
| 23:03 | bench-triggers | — | gemma-4-e4b-it-mlx · LMS minimac2 | 7/9 (no PR — collab) | planner ignored README hooks — [details](entries/2026-04-27-2303-bench-triggers-first-attempt.md) |
| 23:14 | bench-triggers | — | gemma-4-e4b-it-mlx · LMS minimac2 | 0 | ❌ minimac2 hung — [details](entries/2026-04-27-2314-bench-triggers-rerun-aborted.md) |

### Key learnings of the day

- **exo dropped** — Pipeline mode evicts KV mid-run for any model that doesn't fit comfortably in a single node; Tensor mode on TCP/IP is unusable for planner-shape prompts.
- **Baseline = gemma-4-e4b-it-mlx on LM Studio minimac**, parallel via different repo per host.
- **Just-in-Time Model Loading** in LM Studio Server API — mandatory; mitigates the SIGSEGV channel-error class but doesn't prevent all runtime hangs.
- **Reasoning-distilled models are a trap** for gitoma — CoT baked in via fine-tuning means `/no_think` is ignored and the planner times out.
- **README hooks do NOT steer the gitoma planner** — corpus-engineering needs metric-level signal (or task-injection mechanism) to live-fire structural critics.

---

## 2026-04-28 — generation bench day

5-way bench on `gitoma-bench-generation` (one repo, 5 branches with the same intent but different starting states). Sequential on minimac1, 28 min total. **Structural conclusion**: gitoma is a polish agent, not a generation agent. README intent + spec files + failing-test imports are all invisible to the planner. Only inline TODO markers survive — and the worker still misinterprets them.

| When | Branch | PR | Verdict |
|------|--------|----|---------|
| 20:05 | start-empty | [#1](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/1) | boilerplate only — zero src/ — [details](entries/2026-04-28-2005-bench-generation-start-empty.md) |
| 20:11 | start-skeleton | [#2](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/2) | skeleton dirs ignored — [details](entries/2026-04-28-2011-bench-generation-start-skeleton.md) |
| 20:17 | start-stub | [#3](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/3) | ★ partial impl — but contradicts spec — [details](entries/2026-04-28-2017-bench-generation-start-stub.md) |
| 20:22 | start-spec | [#4](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/4) | spec treated as docs — wrap with MkDocs — [details](entries/2026-04-28-2022-bench-generation-start-spec.md) |
| 20:28 | start-tests-first | [#5](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/5) | ❌ TDD attack vector backfired — cosmetic edit instead of impl — [details](entries/2026-04-28-2028-bench-generation-start-tests-first.md) |

★ **Meta-finding**: [structural conclusion + roadmap](entries/2026-04-28-2034-meta-bench-generation-conclusions.md) — gitoma needs `--plan-from-file` (operator-curated TaskPlan) to be usable for from-zero work. 2-3h feature, single highest-leverage thing to ship.

★★★ **`--plan-from-file` SHIPPED + first ever live G18 firing**: [feature + live-fire](entries/2026-04-28-2130-meta-plan-from-file-shipped-G18-live-fired.md) — gitoma commit `bc18a95`. Path D structural blocker SOLVED for G18. Same pattern unlocks G16 + G19. Reproducible benches now possible.

★★ **G16 + G19 closure attempt — CPG-staleness bug surfaced**: [findings](entries/2026-04-28-2155-G16-G19-attempted-CPG-staleness-bug-found.md) — G16 fires (technically a false-positive that happens to match design intent); G19 structurally unfireable on add-the-clique patches because `worker._cpg_index` is built once and never refreshed. New backlog: incremental CPG rebuild in worker.

★★★ **Three-feature evening — `--plan-from-file` + CPG fix + PHASE 7**: [evening summary](entries/2026-04-28-2225-evening-milestones-summary.md) — three commits ship in succession, orphan-symbol critic family closed for live-fire (G16+G18+G19 all confirmed firing), and the bot's diary now writes itself via PHASE 7 hook. From this point on, run entries in `entries/` will be AUTO-GENERATED by gitoma at the end of each successful run.

---

## How this log is written

For now, entries are written manually by the operator after each
gitoma run, scraping the trace JSONL + run output. The plan is
to add a gitoma post-run hook (PHASE 7 candidate) that emits a
diary entry automatically when a run finishes, opt-in via env
(`GITOMA_DIARY_REPO=fabgpt-coder/log`).

Race condition handling: per-entry filename includes a timestamp,
so simultaneous parallel runs land different files and don't
conflict on commit.
