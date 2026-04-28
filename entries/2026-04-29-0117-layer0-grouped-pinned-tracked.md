---
date: 2026-04-29T01:17:00+02:00
type: feature-shipped
gitoma_commits: [353dfc6]
context: tracking upstream layer0 commit f2e70860 (6 agentic memory features)
verdict: ★★ Layer0 client + PHASE 1.5/8 upgraded; pinned-fact bucket prepended to planner context
---

# Layer0 follow-up — grouped + pinned tracked

The user shipped 6 agentic memory features upstream in
`fabriziosalmi/layer0` commit `f2e70860` while gitoma's scaffold
vertical was being shipped earlier this evening. Three of the six
were exactly the Top-3 backlog items I'd flagged after the first
Layer0 integration:
- #1 `SearchGroupedByText` — single-walk per-tag buckets
- #2 `tag_all_of` — AND semantics on tags
- #3 `pinned` — exempt from retention pruning

Plus three more I hadn't asked for but that compose nicely:
- per-memory `expires_at_ms` (TTL override)
- `GetMemoryById` (point lookup)
- `layer0_search_dedupe` (client-side content dedup)

20 → 23 MCP tools. Wire-compatible additive proto.

## What gitoma now uses

Three of the six are wired into gitoma in commit `353dfc6`:

### 1. `search_grouped` — PHASE 1.5

The pre-planner Layer0 query now asks for top-3 from each of
4 high-signal buckets in ONE gRPC round-trip:

```
pinned-fact   ← architectural facts (operator-curated, never expire)
guard-fail    ← past critic firings on this repo
pr-shipped    ← past PR outcomes
plan-shipped  ← past plan summaries (LLM-generated)
```

The planner prompt now sees a structured, bucketed view of the
repo's history instead of a flat top-K. Pinned facts come FIRST
so they override everything else when present.

Backward-compat fallback: when the server doesn't expose grouped
search (older build) OR no tagged memories exist yet (fresh
namespace), falls back to the flat `search_memory` legacy path —
visible in console as "Layer0: injected N flat memories".

### 2. `tag_all_of` — AND filter

`Layer0Client.search_memory(..., tag_all_of=["guard-fail", "G18"])`
now returns ONLY memories carrying both tags. Useful for precise
queries like "all G18 firings on this repo" without false-positives
from broader `guard-fail` matches.

Live-fired against bench-blast namespace: returned exactly 1 hit
(the only memory carrying both `guard-fail` AND `G18`).

### 3. `pinned=True` — PHASE 8

Plan-source memories from `--plan-from-file` runs are now ingested
with `pinned=True` + extra `pinned-fact` tag. Operator-curated plans
must survive retention pruning indefinitely — losing them to a
background TTL sweep would erase reproducibility. LLM-generated
plans stay ephemeral.

Verified live on bench-triggers happy-path: the post-run namespace
shows the new memory with `tags=['plan-loaded', 'plan-from-file',
'pinned-fact']` and server-side `pinned=True`.

## What gitoma doesn't use yet

- `expires_at_ms` per-memory TTL — backlog. Useful for
  ephemeral context like "current run's failure mode" that
  shouldn't pollute the namespace longer than 24h.
- `GetMemoryById` — backlog. Useful for "show memory X" UIs +
  audit replay.
- `layer0_search_dedupe` — backlog. Useful in PHASE 1.5 to avoid
  injecting 5 nearly-identical PR-shipped memories.

These three are mechanical follow-ups now that the pattern is
established.

## Spider web update

Three legs in `gitoma/integrations/`, all wire-compatible-additive
to their upstream changes:

| Leg | Upstream | gitoma client | Last sync |
|-----|----------|---------------|-----------|
| occam-gitignore | core lib | `occam_gitignore.py` | initial |
| layer0 | gRPC + MCP | `layer0.py` | f2e70860 (this commit) |
| occam-trees | FastAPI HTTP | `occam_trees.py` | initial |

The pattern of "upstream ships, gitoma's silent-fail-open client
extends additively without breaking backward-compat" is now well-
proven across two cycles (initial layer0 ship → first wire-in →
upstream ships v2 → second wire-in). This is the spider-web in
practice: each leg evolves on its own timeline, gitoma tracks
opportunistically.

## Stats by end of this update

7 commits over the evening (2026-04-28 night → 2026-04-29 1:17am):

| Commit | Cosa |
|--------|------|
| `bc18a95` | --plan-from-file |
| `e95f658` | CPG-staleness fix |
| `abf1cff` | PHASE 7 diary |
| `6655038` | Layer0 client v1 |
| `ca6562c` | PHASE 1.5 + 8 wire-in |
| `83690cc` + `3a8e160` | gitoma scaffold |
| **`353dfc6`** | **Layer0 v2 (grouped + pinned + tag_all_of)** |

Suite: 1740/1740 + 5 new = 1745. Three spider legs live + three
PHASE-side wire-ins (1.5/7/8). The amnesia loop now has structure:
buckets that the planner prompt can render distinctly, pinned
facts that survive forever, and AND-precise queries when needed.
