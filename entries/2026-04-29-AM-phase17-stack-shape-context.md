---
date: 2026-04-29T08:00:00+02:00
type: feature-shipped
gitoma_commits: [e46752d]
context: composing the 3 spider-web legs (RepoBrief + occam-trees + planner) into a single pre-PHASE-2 context block
verdict: ★★ PHASE 1.7 ships — planner now sees what the canonical scaffold says SHOULD be in the repo, not just what IS
---

# PHASE 1.7 — stack-shape context (occam-trees → planner)

Yesterday evening shipped `gitoma scaffold` (third spider leg) and
the Layer0 amnesia loop. Both are mature legs that solve the
"from-zero" gap and the "amnesia" gap respectively. What was still
missing: a way to use the canonical-tree knowledge from occam-trees
WITHOUT requiring the operator to run `gitoma scaffold` first.

PHASE 1.7 closes that gap by composing the legs we already have:

```
RepoBrief.stack signals  →  occam-trees catalog match
        +
file_tree size           →  archetype level inference
        +
canonical scaffold       →  delta vs current repo
        ↓
"REPO CANONICAL SHAPE" block injected into planner prompt
```

The planner now sees, in addition to what files already exist
(file_tree) and what their structure looks like (Skeletal v1),
**what canonical paths the inferred (stack, level) pair says the
repo SHOULD have but doesn't yet**. Treated as additive-only hints.

## Pipeline slot

```
PHASE 1   (audit + RepoBrief)
PHASE 1.5 (Layer0 cross-run memory query — bucketised)
PHASE 1.7 (stack-shape context from occam-trees)         ← NEW
          (Skeletal v1 — CPG-lite signatures)
PHASE 2   (LLM planner)
```

PHASE 1.7 sits between PHASE 1.5 and Skeletal because:
- It needs RepoBrief from PHASE 1
- It's another **additive context block** (like Skeletal); both feed
  PHASE 2 without mutating the repo
- Order within the prompt = canonical-shape AFTER skeleton because
  "missing files" is more directive than "existing structure"

Skipped automatically when:
- `--plan-from-file` is in use (operator already curated the plan)
- `OCCAM_TREES_URL` not reachable / empty catalog returned
- RepoBrief has zero or one stack signal (below match threshold)
- `GITOMA_PHASE17_OFF=1`

## Inference details

**Stack inference** = component-set intersection scoring.
- Score each stack by `len(brief.stack ∩ stack.components)`
- Default threshold = 2 matches (1 was tested, too many false-positive
  Python hits — every Python framework would tie)
- Tie-break: lower rank wins (popularity proxy)
- Returns top-3 candidates for explainability

Example on gitoma's own repo (test only — RepoBrief.stack hardcoded
to `["Python", "FastAPI"]`):
- 4 stacks tied at 2 matches: farm, fastapi-vue, pytorch-fastapi,
  langchain-fastapi
- Tie-break by rank → **farm** (rank 14)

**Level inference** = source-file count tiers (1-10).
Excludes: tests/, node_modules, dist, build, target, .venv,
__pycache__, .next, .nuxt, vendor, out, coverage, docs (.md/.rst),
images (.png/.jpg/.svg), locks (.lock), logs.

| Files     | Level |
|-----------|-------|
| <5        | 1     |
| 5-15      | 2     |
| 15-40     | 3     |
| 40-120    | 4     |
| 120-300   | 5     |
| 300-700   | 6     |
| 700-1500  | 7     |
| 1500-3500 | 8     |
| 3500-8000 | 9     |
| ≥8000     | 10    |

## The additive-only contract

This is the same contract `gitoma scaffold` enforces at the
materialisation layer. The planner sees:

```
== REPO CANONICAL SHAPE (occam-trees — additive hints only) ==
Inferred stack: FARM (farm) · level 9 · matched components: Python, FastAPI

Canonical paths missing from the repo:
  (root)/
    - requirements.txt [dependencies]
    - docker-compose.yml [local-services]
  agents/
    - agents/orchestrator/graph.py [state-machine]
    - agents/orchestrator/state.py [memory-schema]
    …
You MAY emit subtasks that create them when they address a metric
in the report. You MUST NOT propose removing files just because
they don't appear above — the absence of a path here means "no
opinion", not "unwanted".
```

Why the hard rule: gitoma is a **polish-agent**, not a generation-agent
(established yesterday). The planner is not trusted to remove files.
The "no opinion" framing matters because most repos diverge from any
canonical scaffold in ways that are intentional and not something the
planner should second-guess.

## Why composition over a new feature

The temptation was to build a "scaffold-aware planner" — a separate
PHASE 2 mode. The cleaner solution turned out to be: just give PHASE 2
one more **context block**, exactly like the 5 it already consumes
(brief, fingerprint, prior_runs, skeleton, vertical_addendum). The
shape of the planner stays the same; the prompt gets richer.

Three-leg composition pattern, in code:
```python
brief = extract_brief(repo)        # leg 1: deterministic signals
ot = OccamTreesClient()            # leg 2: scaffold catalog
inf = infer_stack(brief, ot.list_stacks())
resolved = ot.resolve(inf.stack_id, infer_level(file_tree))
delta = compute_delta(resolved.flatten(), file_tree)
block = render_shape_context(...)  # leg 3 (planner) consumes
```

Each leg already exists. PHASE 1.7 = ~80 LOC of glue + 31 unit tests.

## Stats by end of this update

8 commits over the last ~12h (2026-04-28 evening → 2026-04-29 AM):

| Commit | Cosa |
|--------|------|
| `bc18a95` | --plan-from-file |
| `e95f658` | CPG-staleness fix |
| `abf1cff` | PHASE 7 diary |
| `6655038` | Layer0 client v1 |
| `ca6562c` | PHASE 1.5 + 8 wire-in |
| `83690cc` + `3a8e160` | gitoma scaffold |
| `353dfc6` | Layer0 v2 (grouped + pinned + tag_all_of) |
| **`e46752d`** | **PHASE 1.7 stack-shape context** |

Suite: 1745 + 5 + 31 = **1781 tests** verde.

The amnesia loop has structure (Layer0 v2 buckets), the from-zero
gap is closed (gitoma scaffold), and now the planner has explicit
canonical-shape context whenever (stack, level) can be inferred from
the repo's manifests. Three legs, all wire-compatible-additive,
composing through PHASE 1/1.5/1.7/2/8 of the run pipeline.

Next backlog: Layer0 v2 leftovers (`expires_at_ms` TTL, GetMemoryById,
search_dedupe), more spider legs (semgrep / license-checker / reuse-tool).
