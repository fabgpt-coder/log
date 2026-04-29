---
date: 2026-04-29T09:30:00+02:00
type: feature-shipped
gitoma_commits: [285b68e]
context: closing the PHASE 1.6 loop on the worker side — preventing regressions, not just informing
verdict: ★★ G21 ships — semgrep wire-up now full-circle (audit → planner prompt → worker reject)
---

# G21 semgrep-regression — closing the PHASE 1.6 loop

PHASE 1.6 (commit `e5e34c4`, ~30 min ago) gives the planner concrete
security/quality signals via semgrep. But planner prompt injection
is one-way: the planner SEES the issues and may target them, but
nothing PREVENTS a worker patch from introducing NEW issues of the
same kind. G21 closes that gap.

## The pattern

```
PHASE 1.6 (planner side)
  ↳ scan repo → top-20 findings → prompt block
  ↳ scan repo → ALL findings → fingerprint baseline
                                          ↓
                                  WorkerAgent(... semgrep_baseline=...)
                                          ↓
PHASE 6 (worker side, per patch)
  ↳ scan repo post-patch → findings
  ↳ filter: in touched files AND not in baseline AND ≥ severity floor
  ↳ if any remain → revert + retry (canonical critic shape)
```

The baseline is computed ONCE per gitoma run (at PHASE 1.6 time)
and threaded through to WorkerAgent via the constructor. Same
delivery channel as `cpg_index` / `repo_fingerprint` — established
pattern, no new state-passing infrastructure.

## Fingerprint design choice

**fingerprint = (rule_id, path)** — line number intentionally NOT
included.

Why: patches shift line numbers within a file (insert a comment
above an existing finding → line moves +1 → "new" finding by line
fingerprint, but it's the SAME finding in the same place). This
would false-positive on every line drift after any patch.

Trade-off: two different findings of the SAME rule on the SAME file
fold to one fingerprint. So if the patch removes an old eval() and
introduces a new one elsewhere in the same file under the same
rule, G21 won't catch it. The LLM feedback message lists the
ACTUAL post-patch finding details (path:line + message) so the
worker can target the right line — the staleness of "which exact
instance" is acceptable in exchange for robustness against drift.

## Severity floor

Default = ERROR-only (rank 0). Operator can lower via
`GITOMA_G21_SEVERITY=warning|info`.

Reasoning: the community ruleset's WARNING/INFO findings include
style nits that aren't worth blocking patches over. A regression
gate should fire on real defects, not on `prefer-const` violations.
Operators who want stricter behaviour flip the env knob.

## Silent fail-open paths (every critic must have them)

| Condition | G21 behavior |
|---|---|
| `GITOMA_G21_SEMGREP` not set | skip (default OFF) |
| `semgrep_baseline=None` (PHASE 1.6 disabled) | skip |
| No touched files | skip |
| Repo root invalid | skip |
| `SemgrepClient.enabled=False` (binary missing) | skip |
| Scan returns `[]` | skip |
| All new findings below severity floor | skip |
| All new findings in untouched files | skip |
| All new findings already in baseline | skip |

Only when EVERY filter survives does G21 fire. Conservative on
purpose — this is a worker-side gate, false positives reject
patches the LLM will then re-attempt, burning tokens.

## Latency cost

The honest part: G21 enabled = one extra full-repo `semgrep scan`
per patch attempt. On a 100-file Python repo this is ~5-15s; on a
1000-file polyglot repo it's 30-60s. That's why G21 is opt-in by
default — operators decide whether the regression-gate value
outweighs the per-patch cost.

A future optimisation would be to scan ONLY the touched files post-
patch. Semgrep supports `scan <file1> <file2>` but `--config=auto`
needs the language-detection pass over the whole repo to pick
appropriate rules. Worth revisiting once we see real-world G21
firings — premature optimisation today.

## Pipeline now

```
PHASE 1   audit + RepoBrief + CPG-lite build
PHASE 1.5 Layer0 cross-run memory (bucketised + deduped)
          + Skeletal v1
PHASE 1.6 Semgrep scan → top-20 to planner prompt
                       → ALL fingerprints to worker baseline
PHASE 1.7 Stack-shape (occam-trees)
PHASE 2   LLM planner (consumes 1.5/1.6/1.7 context blocks)
PHASE 3   worker iterates subtasks
PHASE 6   worker critics — G1..G15, G16/G18/G19, G20, G21 (NEW)
PHASE 7   diary hook
PHASE 8   Layer0 ingest
```

5 PHASE-side hooks live (1.5/1.6/1.7/7/8) and the critic stack is
now 19 active guards (G1-G15 + G16/G18/G19 + G20 + G21; G17 was
deferred per design).

## Tests

38 unit tests:
- Env opt-in (truthy/falsy variants, parametrised)
- Severity floor parsing (default/warning/info/garbage-fallback)
- Baseline computation (empty, dedup, severity-filter, missing-fields)
- Silent-skip paths (8 distinct skip conditions, each tested)
- Diff logic (baseline-finding doesn't fire / new-in-touched fires
  / new-in-untouched skipped / severity floor / multiple new
  findings collected)
- Render (path:line/CWE/message-truncation/count-header)
- Frozen dataclass invariants

## Stats

11 commits this session (2026-04-28 evening → 2026-04-29 AM):

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
| 10 | `e5e34c4` | PHASE 1.6 semgrep (4th leg) |
| 11 | **`285b68e`** | **G21 semgrep-regression critic** |

Suite: 1813 → **1851** verde (+38 new). 4 spider legs. Semgrep
wire-up now full-circle: audit → planner prompt → worker reject.

The pattern of "spider leg → planner prompt block → worker critic"
is now stamped on semgrep. Layer0 follows the same shape (PHASE 1.5
read + PHASE 8 write); occam-trees is on the read-only path
(PHASE 1.7); occam-gitignore is one-shot vertical (`gitoma gitignore`).
Each leg picks the integration depth that fits its leverage profile.
