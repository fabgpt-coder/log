---
date: 2026-04-29T09:00:00+02:00
type: feature-shipped
gitoma_commits: [e5e34c4]
context: 4th spider leg — semgrep CLI wrapper + planner-prompt injection
verdict: ★★ pattern proven at 4 legs — same shape, same contract, same effort
---

# PHASE 1.6 — semgrep static-analysis context (4th spider leg)

The architecture memo (`project_architecture_spider_web.md`) listed
semgrep as a "likely future leg" since 2026-04-28. This morning it
ships, taking the spider count from 3 to **4 confirmed legs**.

## Why semgrep was the right 4th leg

Three options were on the backlog:
1. **semgrep** — multi-language static analysis (security + smells),
   2000+ community rules, JSON CLI output
2. license-checker — narrow (license compliance only)
3. reuse-tool — narrowest (SPDX file headers, OSS hygiene)

semgrep wins on **leverage per LOC**:
- Multi-language coverage (30+ languages out of the box)
- High-signal output: every finding has `rule_id` + `path:line` +
  CWE — the planner can act on it without inferring intent
- Uniform JSON shape across all rule families
- Free / no auth needed for community ruleset
- Composes naturally with the existing critic stack (could feed a
  G21 "no new findings introduced" critic later)

## Pipeline slot

```
PHASE 1   audit + RepoBrief
PHASE 1.5 Layer0 cross-run memory (bucketised + deduped)
          CPG-lite Skeletal v1
PHASE 1.6 Semgrep findings                        ← NEW
PHASE 1.7 Stack-shape (occam-trees)
PHASE 2   LLM planner
PHASE 6   worker critic stack (G1-G20)
PHASE 7   diary hook
PHASE 8   Layer0 ingest
```

PHASE 1.6 sits between Skeletal and PHASE 1.7 because all three are
pre-PHASE-2 context blocks for the planner. Order within the prompt:
findings come AFTER skeleton (so the planner has structural context
first) but BEFORE scaffold-shape (so security/quality issues take
priority over canonical-file completion).

## What gets injected

A compact block grouped by severity:

```
== SEMGREP STATIC-ANALYSIS FINDINGS (concrete actionable issues) ==
### ERROR (3)
- src/auth.py:42 `python.lang.security.dangerous-eval` [CWE-95] — Found eval() call
- src/db.py:88 `python.lang.security.sql-injection` [CWE-89] — Possible SQL injection
- src/api.py:15 `python.flask.csrf` [CWE-352] — Missing CSRF protection
### WARNING (5)
- ...

Prefer subtasks that target the ERROR-severity findings above
over generic security/quality work — these are real, locatable
defects with rule ids you can cite in commit messages.
```

The instruction at the bottom is explicit: "use these instead of
generic security boilerplate". The planner's main failure mode
historically has been emitting "improve security" tasks that don't
target anything concrete (rung-0 pattern from
`project_backlog_planner_focus_real_bug.md`). Semgrep findings give
it concrete locations to actually fix.

## Silent-fail-open contract (4th iteration)

| Failure mode | Handling |
|---|---|
| `semgrep` not on PATH | `SemgrepConfig.enabled=False` set at `from_env()`, no subprocess attempt |
| Scan timeout (default 60s) | Return `[]`, no block injected |
| Subprocess OSError | Return `[]` |
| Non-JSON output | Return `[]` |
| Exit code 2+ (semgrep itself errored) | Return `[]` even if stdout looks valid |
| Repo has no findings | Return `[]`, no block injected |

Operator opt-out via `GITOMA_PHASE16_OFF=1`.

## Env knobs

- `SEMGREP_BIN` — path to semgrep binary (default `semgrep` on PATH)
- `SEMGREP_CONFIG` — `--config` value (default `auto` = registry's
  language-appropriate ruleset; can pin to e.g. `p/security-audit`)
- `SEMGREP_TIMEOUT_S` — per-scan deadline in seconds (default 60s,
  clamped to minimum 5s to avoid pathological 0.1s configs)

## What's NOT in this commit

- **G21 "no new semgrep findings"** worker-side critic — would need
  baseline diffing (semgrep before vs after patch) and adds latency
  to every patch attempt. Worth doing later as a focused commit;
  the leg is ready for it.
- **--autofix** — semgrep's autofix is unreliable across rule
  families; gitoma's worker is the safer mutation path
- **SARIF output** — JSON is enough for prompt injection
- **Custom rule authoring** — operator concern, not a gitoma concern

## Tests

32 tests covering:
- Env config: binary detection, timeout clamping, default+custom config
- Silent-fail-open paths: missing binary, timeout, OSError, non-JSON,
  non-dict root, exit-code-2 (errors), zero max_findings, missing dir
- Result parsing: severity sort (ERROR>WARNING>INFO), path:line
  tie-break, CWE list+string normalisation, defensive against missing
  extra/start, max_findings cap
- Render: severity grouping, CWE inclusion, message truncation at
  100 chars, budget truncation marker, default budget constant

## Spider web — 4 legs

| # | Leg | Bus | Wrapper |
|---|-----|-----|---------|
| 1 | occam-observer | HTTP :29999 | `gitoma/context/occam_client.py` |
| 2 | occam-gitignore | Python lib | `gitoma/integrations/occam_gitignore.py` |
| 3 | layer0 | gRPC :50051 | `gitoma/integrations/layer0.py` |
| 4 | occam-trees | FastAPI HTTP :8420 | `gitoma/integrations/occam_trees.py` |
| **5** | **semgrep** | **CLI subprocess (JSON)** | **`gitoma/integrations/semgrep_scan.py`** |

Wait — that's actually 5 lines because occam-observer was the first
leg listed in the architecture memo even though it predates the
"spider web" phrasing. Counting strictly the ones documented under
the spider-web pattern: 4 (occam-gitignore + layer0 + occam-trees +
semgrep). Both counts are right depending on where you draw the
"first leg" line.

The pattern itself:
```
external CLI/service ←─ thin Python wrapper ←─ silent-fail-open
                       (Config.from_env, dataclasses, scan/query,
                        render-for-prompt helper)
                                ↓
                         pipeline integration
                       (one PHASE 1.X block, opt-in via env,
                        feeds planner via dedicated kwarg)
```

This pattern is now stamped 4 times. Adding a 5th (license-checker
or llmproxy or reuse-tool) is mechanical: ~80-150 LOC client +
~30 LOC wire-in + 25-35 unit tests. The leverage compounds: every
new leg adds independent signal to the planner without bloating
gitoma core.

## Stats

10 commits this session (2026-04-28 evening → 2026-04-29 AM):

| # | Commit | Cosa |
|---|--------|------|
| 1 | `bc18a95` | --plan-from-file |
| 2 | `e95f658` | CPG-staleness fix |
| 3 | `abf1cff` | PHASE 7 diary |
| 4 | `6655038` | Layer0 client v1 |
| 5 | `ca6562c` | PHASE 1.5 + 8 wire-in |
| 6 | `83690cc` + `3a8e160` | gitoma scaffold |
| 7 | `353dfc6` | Layer0 v2 |
| 8 | `e46752d` | PHASE 1.7 stack-shape |
| 9 | `7079216` | Layer0 v2 leftovers |
| 10 | **`e5e34c4`** | **PHASE 1.6 semgrep (4th leg)** |

Suite: 1781 → **1813** verde (+32 new). 5 PHASE-side hooks live
(1.5/1.6/1.7/7/8); 4 spider legs in `gitoma/integrations/`.
