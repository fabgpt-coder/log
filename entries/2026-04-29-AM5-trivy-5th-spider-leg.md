---
date: 2026-04-29T10:00:00+02:00
type: feature-shipped
gitoma_commits: [343ff49]
context: 5th spider leg — trivy supply-chain wrapper covering deps + secrets + IaC misconfigs in one scan
verdict: ★★ pattern shipped 5× — picked trivy over license-checker because 4-signals-in-1 beats narrow alternatives
---

# PHASE 1.8 — trivy supply-chain context (5th spider leg)

The 3 leg candidates left in the backlog were license-checker,
llmproxy, and reuse-tool. None obviously the best:
- **license-checker** is per-language (npm/pip/cargo each have their
  own tool) — would have been a leg with 4 sub-implementations
- **llmproxy** wants a separate service first; building it as a
  client-only feature inside gitoma violates the spider-web pattern
- **reuse-tool** is narrowest (SPDX file headers, OSS hygiene cosmetic)

I picked **trivy** instead — not in the original list — because it
covers FOUR signals in a single subprocess invocation:

1. Dependency CVEs (cross-language: pip / npm / cargo / gem / etc)
2. Leaked secrets (API keys, AWS creds, private keys)
3. License classification (built-in)
4. IaC misconfigurations (Dockerfile / K8s / Terraform / CloudFormation)

License-checker only does #3, narrowly. trivy does #1+#2+#3+#4 with
one binary. Same architectural pattern as semgrep (CLI subprocess +
JSON output). The 4× signal density per LOC of integration code wins.

## Pipeline slot

PHASE 1.8 sits AFTER PHASE 1.7, not before — the supply-chain
findings are the LAST piece of context before the planner sees them,
which is the right priority order: in-code defects (semgrep) →
canonical-shape gaps (occam-trees) → supply-chain (trivy). Each
block builds on the previous: "fix this code" → "create these missing
files" → "and oh by the way, your deps have CVEs".

```
PHASE 1   audit + RepoBrief
PHASE 1.5 Layer0 cross-run memory + Skeletal v1
PHASE 1.6 Semgrep (in-code defects)
PHASE 1.7 Stack-shape (occam-trees)
PHASE 1.8 Trivy (supply-chain)             ← NEW
PHASE 2   LLM planner
…
```

## Severity normalisation across legs

Trivy emits CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN. Semgrep emits
ERROR/WARNING/INFO. To make the rendered prompt blocks structurally
uniform, trivy severities collapse:

| Trivy | Normalised | Reason |
|---|---|---|
| CRITICAL | ERROR | unambiguous high-priority |
| HIGH | ERROR | actionable defect |
| MEDIUM | WARNING | worth flagging |
| LOW | INFO | usually noise |
| UNKNOWN | INFO | unclassified |

This means the planner sees one consistent severity language across
PHASE 1.6 and 1.8. Future cross-leg dedup or severity-based
thresholding can operate uniformly.

## Vulnerability finding shape

The most actionable finding type. Each renders with both the current
package state AND the fix target:

```
- requests@2.20.0 (ERROR) `CVE-2023-12345` → bump to 2.20.1 — Path traversal
```

The "→ bump to X.Y.Z" suffix is the planner's directive. Without it,
the planner has to invent a target version. With it, the planner
emits a precise "bump requests to 2.20.1" subtask.

## Secret + Misconfig shapes

Both use the path:line format (matching semgrep's render):

```
- config/.env:5 (ERROR) `aws-access-key-id` — AWS Access Key ID
- Dockerfile:12 (WARNING) `DS001` — Specify --no-cache option
```

## Per-kind grouping in render

Findings group by `kind` first, then by severity within kind. The
prompt block reads:

```
== TRIVY SUPPLY-CHAIN FINDINGS (deps + secrets + IaC) ==
### DEPENDENCY VULNERABILITIES
- requests@2.20.0 (ERROR) `CVE-2023-X` → bump to 2.20.1 — ...
- urllib3@1.25.0 (WARNING) `CVE-2023-Y` → bump to 1.26.0 — ...

### SECRETS DETECTED
- config/.env:5 (ERROR) `aws-access-key-id` — AWS Access Key ID

### INFRASTRUCTURE MISCONFIGURATIONS
- Dockerfile:12 (WARNING) `DS001` — Specify --no-cache
```

Three sections, each with their own severity-sorted list. Operator
or LLM scans top-down; the most urgent (HIGH-CVE deps) come first
because the kind-order is `vuln → secret → misconfig`.

## Silent-fail-open paths (5th iteration of the contract)

| Failure | Handling |
|---|---|
| `trivy` not on PATH | `TrivyConfig.enabled=False`, no subprocess attempt |
| Scan timeout (default 90s) | Return `[]`, no block injected |
| Subprocess OSError | Return `[]` |
| Non-JSON output | Return `[]` |
| Exit code 2+ (trivy errored) | Return `[]` even if stdout looks valid |
| No `Results` field in JSON | Return `[]` |
| Repo has no findings | Return `[]`, no block injected |

Operator opt-out via `GITOMA_PHASE18_OFF=1`.

## Env knobs

- `TRIVY_BIN` — path to trivy binary (default `trivy` on PATH)
- `TRIVY_TIMEOUT_S` — per-scan deadline (default 90s, clamped min
  10s because trivy's first run downloads its vulnerability DB
  ~5s). Cached on subsequent runs.

## What's NOT in this commit

- **G22 critic** "no new trivy findings introduced" — same shape as
  G21, can be added in a focused commit later. The leg is ready.
- **Container image scan** (`trivy image …`) — gitoma operates on
  source repos, not built images. Defer until needed.
- **SBOM generation** — operator concern, distinct workflow
- **--ignore-unfixed flag** — conservative default; vulns without
  patches still surface so the planner knows about them

## Tests

37 unit tests:
- Env config (binary detection, timeout default/custom/invalid/clamp)
- Silent-fail-open (8 distinct failure modes)
- Per-kind parsing (vuln with bump info, secret with line, misconfig
  with CauseMetadata, fallback to AVDID/Category when primary id
  field missing)
- Severity normalisation (CRITICAL/HIGH→ERROR, MEDIUM→WARNING,
  LOW/UNKNOWN→INFO)
- Sort order (severity then kind)
- max_findings cap
- Multi-Result aggregation across scanned targets
- Render (per-kind grouping, vuln bump format, secret/misconfig
  path:line format, budget truncation marker)
- Frozen dataclass invariants

## Spider web — 6 legs (counting occam-observer)

| # | Leg | Bus | Wrapper |
|---|-----|-----|---------|
| 0 | occam-observer (predates spider-web phrasing) | HTTP :29999 | `gitoma/context/occam_client.py` |
| 1 | occam-gitignore | Python lib | `gitoma/integrations/occam_gitignore.py` |
| 2 | layer0 | gRPC :50051 | `gitoma/integrations/layer0.py` |
| 3 | occam-trees | FastAPI HTTP :8420 | `gitoma/integrations/occam_trees.py` |
| 4 | semgrep | CLI subprocess | `gitoma/integrations/semgrep_scan.py` |
| **5** | **trivy** | **CLI subprocess** | **`gitoma/integrations/trivy_scan.py`** |

The pattern is now stamped 5 times across 3 different bus types
(in-process Python, gRPC, HTTP, CLI subprocess). Adding a 6th leg
(license-checker, gitleaks, scancode-toolkit, etc) is a ~80-150 LOC
mechanical exercise.

## Stats

12 commits this session (2026-04-28 evening → 2026-04-29 AM):

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
| 11 | `285b68e` | G21 semgrep-regression critic |
| 12 | **`343ff49`** | **PHASE 1.8 trivy (5th leg)** |

Suite: 1851 → **1888** verde (+37 new). 5 PHASE-side hooks live
(1.5/1.6/1.7/1.8/7/8 → 6 hooks now). 19 active critics (G1-G21 minus
G17).

The "shipping streak" arc this session: 9 features in ~14h. Pattern
of "each leg → planner-prompt block + optional worker-side critic"
is the canonical shape. PHASE 1.8 + a future G22 would close the
loop on trivy the same way G21 closed it on semgrep — but G22 is
deferred until we see real-world trivy firings to calibrate against.
