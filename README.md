# fabgpt-coder — operations log

Public timeline of what **`fabgpt-coder`** — the [gitoma](https://github.com/fabriziosalmi/gitoma)-powered agent operated by [@fabriziosalmi](https://github.com/fabriziosalmi) — does across all repos. One entry per gitoma run, including runs that **didn't** ship a PR (those are where the learnings live).

Each entry has machine-readable frontmatter (date, repo, PR, model, endpoint, subtasks, guards, verdict) plus a short body. Append-only — entries are immutable once written.

> This file is auto-generated from `entries/` by `scripts/build_readme.py`. Do not edit by hand.

## Snapshot — 2026-06-09

| Metric | Value |
|---|---|
| Runs logged | **29** |
| PRs opened | **24** |
| Subtasks completed | 138/204 (68%) |
| Distinct repos | 5 |
| Distinct models | 7 |
| Guard firings | 41 |
| Milestones | 19 |
| Active days | 4 (2026-04-27 → 2026-04-30) |

**Verdict mix** — clean 6 · partial 15 · failed 5

**Top models** — `gemma-4-e4b-it-mlx` (20) · `qwen3-8b` (3) · `gemma-4-e4b-it-4bit` (2) · `qwen3.5-9b` (1) · `Qwen3.6-27B-4bit` (1)

**Top repos** — `gitoma-bench-blast` (13) · `gitoma-bench-triggers` (5) · `gitoma-bench-generation` (5) · `gitoma-bench-supply-chain` (3) · `gitoma-bench-quality` (3)

**Top guards fired** — `critic_schema_check.fail` (4) · `critic_g23_config_keys.fail` (4) · `G2` (4) · `critic_test_regression.fail` (3) · `critic_ast_diff.fail` (3)

## Latest runs (showing 25 of 29)

| When | Repo | PR | Model | Subs | Guards | Verdict | · |
|---|---|---|---|---|---|---|---|
| 2026-04-30 20:59 | `gitoma-bench-blast` | [#12](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/12) | `qwen3.5-9b` | 2/2 | — | ✅ clean | [entry](entries/2026-04-30-2059-fabriziosalmi-gitoma-bench-blast-qwen35-mm2-worker-203225.md) |
| 2026-04-30 00:33 | `gitoma-bench-supply-chain` | [#3](https://github.com/fabriziosalmi/gitoma-bench-supply-chain/pull/3) | `gemma-4-e4b-it-mlx` | 12/15 | `critic_test_regression.fail` | ◐ partial | [entry](entries/2026-04-30-0033-fabriziosalmi-gitoma-bench-supply-chain-gitoma-improve-20260429-222120-659918.md) |
| 2026-04-30 00:09 | `gitoma-bench-supply-chain` | [#2](https://github.com/fabriziosalmi/gitoma-bench-supply-chain/pull/2) | `qwen3-8b` | 5/8 | `critic_schema_check.fail` | ◐ partial | [entry](entries/2026-04-30-0009-fabriziosalmi-gitoma-bench-supply-chain-gitoma-improve-20260429-213037-981705.md) |
| 2026-04-29 23:12 | `gitoma-bench-supply-chain` | [#1](https://github.com/fabriziosalmi/gitoma-bench-supply-chain/pull/1) | `gemma-4-e4b-it-mlx` | 9/14 | `critic_test_regression.fail` +4 | ◐ partial | [entry](entries/2026-04-29-2312-fabriziosalmi-gitoma-bench-supply-chain-gitoma-improve-20260429-210146-715353.md) |
| 2026-04-29 22:33 | `gitoma-bench-blast` | [#11](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/11) | `gemma-4-e4b-it-mlx` | 6/11 | `critic_g23_config_keys.fail` | ◐ partial | [entry](entries/2026-04-29-2233-fabriziosalmi-gitoma-bench-blast-gitoma-improve-20260429-202501-204958.md) |
| 2026-04-29 22:08 | `gitoma-bench-blast` | [#10](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/10) | `qwen3-8b` | 3/5 | `critic_g23_config_keys.fail` +2 | ◐ partial | [entry](entries/2026-04-29-2208-fabriziosalmi-gitoma-bench-blast-gitoma-improve-20260429-194802-688280.md) |
| 2026-04-29 21:54 | `gitoma-bench-quality` | [#3](https://github.com/fabriziosalmi/gitoma-bench-quality/pull/3) | `gemma-4-e4b-it-mlx` | 5/11 | `critic_syntax_check.fail` +2 | ◐ partial | [entry](entries/2026-04-29-2154-fabriziosalmi-gitoma-bench-quality-gitoma-improve-20260429-194803-506827.md) |
| 2026-04-29 21:41 | `gitoma-bench-blast` | [#9](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/9) | `gemma-4-e4b-it-mlx` | 3/7 | `critic_g23_config_keys.fail` +2 | ◐ partial | [entry](entries/2026-04-29-2141-fabriziosalmi-gitoma-bench-blast-gitoma-improve-20260429-193511-457768.md) |
| 2026-04-29 21:12 | `gitoma-bench-quality` | [#2](https://github.com/fabriziosalmi/gitoma-bench-quality/pull/2) | `gemma-4-e4b-it-mlx` | 8/12 | `critic_sibling_config.fail` +1 | ◐ partial | [entry](entries/2026-04-29-2112-fabriziosalmi-gitoma-bench-quality-gitoma-improve-20260429-190532-109772.md) |
| 2026-04-29 21:04 | `gitoma-bench-blast` | [#8](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/8) | `gemma-4-e4b-it-mlx` | 5/5 | `critic_ast_diff.fail` | ✅ clean | [entry](entries/2026-04-29-2104-fabriziosalmi-gitoma-bench-blast-gitoma-improve-20260429-185917-398255.md) |
| 2026-04-29 20:48 | `gitoma-bench-blast` | [#7](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/7) | `gemma-4-e4b-it-mlx` | 6/8 | — | ◐ partial | [entry](entries/2026-04-29-2048-fabriziosalmi-gitoma-bench-blast-gitoma-improve-20260429-184133-970572.md) |
| 2026-04-28 22:58 | `gitoma-bench-triggers` | [#3](https://github.com/fabriziosalmi/gitoma-bench-triggers/pull/3) | `gemma-4-e4b-it-mlx` | 1/1 | — | ✅ clean | [entry](entries/2026-04-28-2258-fabriziosalmi-gitoma-bench-triggers-fullloop-r2-225719.md) |
| 2026-04-28 22:54 | `gitoma-bench-triggers` | [#2](https://github.com/fabriziosalmi/gitoma-bench-triggers/pull/2) | `gemma-4-e4b-it-mlx` | 1/1 | — | ✅ clean | [entry](entries/2026-04-28-2254-fabriziosalmi-gitoma-bench-triggers-fullloop-225356.md) |
| 2026-04-28 22:19 | `gitoma-bench-triggers` | [#1](https://github.com/fabriziosalmi/gitoma-bench-triggers/pull/1) | `gemma-4-e4b-it-mlx` | 1/1 | `critic_panel.review.start` +2 | ✅ clean | [entry](entries/2026-04-28-2219-fabriziosalmi-gitoma-bench-triggers-diary-happy2-221830.md) |
| 2026-04-28 20:28 | `gitoma-bench-generation` | [#5](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/5) | `gemma-4-e4b-it-mlx` | 6/7 | `G2 sensitive-path` | ❌ TDD attack vector backfired — worker DELETED whitespace from… | [entry](entries/2026-04-28-2028-bench-generation-start-tests-first.md) |
| 2026-04-28 20:22 | `gitoma-bench-generation` | [#4](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/4) | `gemma-4-e4b-it-mlx` | 7/10 | `G2 sensitive-path (×3)` | ◐ PR opened — JSON Schema + CLI contract markdown were entirely… | [entry](entries/2026-04-28-2022-bench-generation-start-spec.md) |
| 2026-04-28 20:17 | `gitoma-bench-generation` | [#3](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/3) | `gemma-4-e4b-it-mlx` | 6/8 | `G2 sensitive-path (×2)` | ★ ONLY branch where the worker actually touched src/ — but the… | [entry](entries/2026-04-28-2017-bench-generation-start-stub.md) |
| 2026-04-28 20:11 | `gitoma-bench-generation` | [#2](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/2) | `gemma-4-e4b-it-mlx` | 6/10 | `G2 sensitive-path (×2)` +1 | ◐ PR opened — added 4 lines to tests/__init__.py, ZERO lines to… | [entry](entries/2026-04-28-2011-bench-generation-start-skeleton.md) |
| 2026-04-28 20:05 | `gitoma-bench-generation` | [#1](https://github.com/fabriziosalmi/gitoma-bench-generation/pull/1) | `gemma-4-e4b-it-mlx` | 7/9 | `G2 sensitive-path` +1 | ◐ PR opened — but ZERO files in src/ touched, no implementation… | [entry](entries/2026-04-28-2005-bench-generation-start-empty.md) |
| 2026-04-27 23:14 | `gitoma-bench-triggers` | — | `gemma-4-e4b-it-mlx` | — | — | ❌ minimac2 LM Studio became unresponsive — APITimeoutError in P… | [entry](entries/2026-04-27-2314-bench-triggers-rerun-aborted.md) |
| 2026-04-27 23:03 | `gitoma-bench-triggers` | — | `gemma-4-e4b-it-mlx` | 7/9 | `G2 (×2)` | ◐ planner ignored README hooks; PR push 403 (collab not yet) | [entry](entries/2026-04-27-2303-bench-triggers-first-attempt.md) |
| 2026-04-27 22:27 | `gitoma-bench-blast` | [#5](https://github.com/fabriziosalmi/gitoma-bench-blast/pull/5) | `gemma-4-e4b-it-mlx` | 4/7 | `G2` +2 | ◐ parallel-A clean (PR opened), but channel error after run | [entry](entries/2026-04-27-2227a-bench-blast-gemma-lms-minimac1.md) |
| 2026-04-27 22:27 | `gitoma-bench-quality` | [#1](https://github.com/fabriziosalmi/gitoma-bench-quality/pull/1) | `gemma-4-e4b-it-mlx` | 8/12 | `G2` +4 | ★ parallel-B clean — first PR on bench-quality | [entry](entries/2026-04-27-2227b-bench-quality-gemma-lms-minimac2.md) |
| 2026-04-27 21:40 | `gitoma-bench-blast` | — | `gemma-4-e4b-it-4bit` | — | — | ❌ TENSOR sharding TCP/IP — dead on arrival | [entry](entries/2026-04-27-2140-bench-blast-gemma-exo-tensor-sharded.md) |
| 2026-04-27 21:34 | `gitoma-bench-blast` | — | `Qwen3.6-27B-4bit` | — | — | ❌ exo cluster planner empty response | [entry](entries/2026-04-27-2134-bench-blast-qwen36-27b-exo-cluster.md) |

**Older runs** — page 1 (here) · [2](pages/PAGE_002.md)

## Milestones (latest 15 of 19)

| When | What | Verdict | · |
|---|---|---|---|
| 2026-04-29 23:55 | G24 config-structure critic | ★ G23+G24 now paired — keys + shapes covered for pyproject.toml… | [entry](entries/2026-04-29-NIGHT-G24-poetry-table-validator.md) |
| 2026-04-29 23:15 | bench-supply-chain corpus + semgrep bug fix + live-fire validation | ★ all PHASE blocks proven on real adversarial content; gemma ac… | [entry](entries/2026-04-29-LATE-EVE-supply-chain-bench-shipped.md) |
| 2026-04-29 22:10 | G23 config-keys + A/B model bench | ★ G23 ships AND validates in production; A/B reveals gemma=cons… | [entry](entries/2026-04-29-EVE2-G23-AB-bench.md) |
| 2026-04-29 21:25 | Live-fire production bench — evening session | ★ Layer0 read+write loop CLOSED in production; PHASE 1.7 fired… | [entry](entries/2026-04-29-EVE-livefire-production-bench.md) |
| 2026-04-29 11:30 | PHASE 7 allowlist + rotation scripts | ★ defense-in-depth on the public-diary surface | [entry](entries/2026-04-29-AM8-diary-allowlist-rotation-scripts.md) |
| 2026-04-29 11:00 | Live-fire bench → RepoBrief framework extraction | ★ honest bench, real gap, real fix — methodology > shipping streak | [entry](entries/2026-04-29-AM7-livefire-bench-revealed-gap.md) |
| 2026-04-29 10:30 | G22 trivy-regression — closing the PHASE 1.8 loop | ★ G22 ships — trivy wire-up now full-circle (audit → planner pr… | [entry](entries/2026-04-29-AM6-G22-trivy-regression.md) |
| 2026-04-29 10:00 | PHASE 1.8 — trivy supply-chain context (5th spider leg) | ★ pattern shipped 5× — picked trivy over license-checker becaus… | [entry](entries/2026-04-29-AM5-trivy-5th-spider-leg.md) |
| 2026-04-29 09:30 | G21 semgrep-regression — closing the PHASE 1.6 loop | ★ G21 ships — semgrep wire-up now full-circle (audit → planner… | [entry](entries/2026-04-29-AM4-G21-semgrep-regression.md) |
| 2026-04-29 09:00 | PHASE 1.6 — semgrep static-analysis context (4th spider leg) | ★ pattern proven at 4 legs — same shape, same contract, same ef… | [entry](entries/2026-04-29-AM3-semgrep-4th-spider-leg.md) |
| 2026-04-29 08:30 | Layer0 v2 leftovers — get_by_id + dedupe + guard TTL | ★ mechanical pattern follow-up — closes Layer0 v2 leftovers, no… | [entry](entries/2026-04-29-AM2-layer0-v2-leftovers.md) |
| 2026-04-29 08:00 | PHASE 1.7 — stack-shape context (occam-trees → planner) | ★ PHASE 1.7 ships — planner now sees what the canonical scaffol… | [entry](entries/2026-04-29-AM-phase17-stack-shape-context.md) |
| 2026-04-29 01:17 | Layer0 follow-up — grouped + pinned tracked | ★ Layer0 client + PHASE 1.5/8 upgraded; pinned-fact bucket prep… | [entry](entries/2026-04-29-0117-layer0-grouped-pinned-tracked.md) |
| 2026-04-29 00:50 | `gitoma scaffold` — third deterministic vertical | ★ from-zero generation gap closed via third spider leg | [entry](entries/2026-04-29-0050-scaffold-vertical-third-spider-leg.md) |
| 2026-04-28 23:10 | Layer0 cross-run memory — amnesia loop closed | ★ amnesia loop closed — gitoma now reads its own past + writes… | [entry](entries/2026-04-28-2310-layer0-amnesia-loop-closed.md) |

---

_Built by `scripts/build_readme.py` on 2026-06-09. Source-of-truth = `entries/*.md` frontmatter._
