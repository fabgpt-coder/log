---
date: 2026-04-29T10:30:00+02:00
type: feature-shipped
gitoma_commits: [c49a0e3]
context: closing the PHASE 1.8 loop on the worker side — same shape as G21 for the supply-chain leg
verdict: ★ G22 ships — trivy wire-up now full-circle (audit → planner prompt → worker reject)
---

# G22 trivy-regression — closing the PHASE 1.8 loop

PHASE 1.8 (commit `343ff49`, ~30 min ago) gives the planner concrete
supply-chain signals via trivy. G22 closes the gap on the worker
side: when a patch introduces a NEW vulnerable dep, leaked secret,
or IaC misconfig, reject + retry instead of letting it through.

## Same pattern as G21 (semgrep)

```
PHASE 1.8 (planner side)
  ↳ scan repo → top-20 findings → prompt block
  ↳ scan repo → ALL findings → fingerprint baseline
                                          ↓
                          WorkerAgent(... trivy_baseline=...)
                                          ↓
PHASE 6 (worker side, per patch)
  ↳ scan repo post-patch → findings
  ↳ filter: not in baseline AND ≥ severity floor (AND in touched, opt-in)
  ↳ if any remain → revert + retry
```

Identical wire-shape to G21 from yesterday morning. The pattern of
"every spider leg can grow a planner-prompt block + an optional
worker-side critic" is now stamped twice (semgrep+G21, trivy+G22).
Future legs can skip either, both, or do both as they mature.

## Fingerprint design — same idea, different specifics

For G21: `(rule_id, path)` where path = source file with the in-code
finding.

For G22: `(rule_id, target)` where target depends on kind:
- **vuln**: target = manifest file (Pipfile.lock, package-lock.json,
  go.sum, Cargo.lock). rule_id = CVE id. A new (CVE, manifest)
  tuple means the patch added a vulnerable dep to that manifest.
- **secret**: target = file containing the secret. rule_id = secret
  rule (aws-access-key-id / github-pat / private-key / …). A new
  pair = the patch leaked a credential into that file.
- **misconfig**: target = IaC file (Dockerfile / *.tf / *.yaml).
  rule_id = misconfig id (DS001 / AVD-DS-... / KSV...). A new pair
  = the patch introduced a misconfig in that file.

Same coarse-but-robust trade-off as G21 — line numbers shift, but
`(rule_id, target)` is stable across patches.

## Scope policy difference vs G21

This is the one place G22 deviates intentionally. G21 only checks
TOUCHED files because semgrep is intra-file (a finding in
`unrelated.py` can't be caused by a patch to `auth.py`).

But trivy's vuln scanner reads manifests and resolves the dep tree.
A patch that adds an `import aiohttp` line in `client.py` could
trigger pip / poetry to add `aiohttp==X.Y.Z` to the lockfile on the
next install — and if Z is vulnerable, the new finding would be in
`Pipfile.lock`, NOT in `client.py`. G21's intra-file scope would
miss this.

Default policy:
- **G22 default** = scan WHOLE repo, compare against baseline
- **G22 touched-only** = `GITOMA_G22_TOUCHED_ONLY=1` (operator
  opt-in for speed)

The price of correctness: G22 is slower than G21 because trivy
re-resolves the dep tree on every invocation. But correctness >
latency for a regression gate.

## Trace event

```json
{
  "event": "critic_g22_trivy.fail",
  "subtask_id": "T002-S03",
  "attempt": 2,
  "conflict_count": 1,
  "rules": ["CVE-2024-12345"],
  "kinds": ["vuln"]
}
```

The `kinds` field is new vs G21's trace shape — operators inspecting
trace JSONL can quickly filter "G22 fired because of a SECRET" vs
"G22 fired because of a VULN" without re-parsing the conflict list.

## Latency cost (the honest part)

G22 enabled = one extra `trivy fs --scanners vuln,secret,misconfig`
per patch attempt. Trivy DB cache hits help (subsequent runs in the
same session ~5-10s on small repos), but the first run downloads
the vulnerability DB (~30s).

Cost profile:
- Small Python repo, DB cached: ~5-10s/patch
- Large polyglot repo, DB cached: ~30-60s/patch
- First run (DB download): +30s on top

G22 is opt-in by default for the same reason as G21 — operators
decide whether the regression-gate value outweighs per-patch cost.
For runs that touch dep manifests, G22 is essential. For pure
docstring fixes, G22 is wasted work.

A future optimisation: skip G22 when the patch doesn't touch any
manifest file OR IaC file OR potentially-secret file (.env, .yaml,
config files). But that requires extra logic and adds false-negative
risk; defer until we see real-world G22 firings.

## Pipeline now

```
PHASE 1   audit + RepoBrief + CPG-lite
PHASE 1.5 Layer0 cross-run memory + Skeletal v1
PHASE 1.6 Semgrep (in-code)
PHASE 1.7 Stack-shape (occam-trees)
PHASE 1.8 Trivy (supply-chain)
PHASE 2   LLM planner (consumes 1.5/1.6/1.7/1.8)
PHASE 3   worker iterates subtasks
PHASE 6   critic stack — G1..G15 + G16/G18/G19 + G20 + G21 + G22 (NEW)
PHASE 7   diary hook
PHASE 8   Layer0 ingest
```

20 active critics now (G1-G22 minus G17). 6 PHASE-side hooks. 5
spider legs (6 counting occam-observer).

## Tests

42 unit tests:
- Env opt-in (truthy/falsy/default/severity floor parsing/touched-only)
- Baseline computation (empty, dedup, severity-filter, missing-fields,
  unknown-severity)
- Silent-skip paths (8 distinct conditions, each tested)
- Diff logic per kind (vuln-with-bump, secret-with-line, misconfig-
  with-line, baseline-finding skipped, severity floor filters,
  default scope includes untouched manifests, touched-only filters
  untouched, all 3 kinds aggregate)
- Render per kind (vuln bump-target format, secret/misconfig
  path:line, count header)
- Frozen dataclass invariants

## Stats

13 commits this session (2026-04-28 evening → 2026-04-29 AM):

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
| 11 | `285b68e` | G21 semgrep-regression |
| 12 | `343ff49` | PHASE 1.8 trivy (5th leg) |
| 13 | **`c49a0e3`** | **G22 trivy-regression** |

Suite: 1888 → **1930** verde (+42 new). Both static-analysis legs
now have full-circle wire-up: audit → planner prompt → worker reject.
The "leg + planner block + critic" pattern is the canonical
3-touchpoint shape. Adding a 6th leg (license-checker, gitleaks,
…) gets the planner-block automatically and the critic optionally.
