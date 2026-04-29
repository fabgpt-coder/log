---
date: 2026-04-29T08:30:00+02:00
type: feature-shipped
gitoma_commits: [7079216]
context: closing the 3 backlog items from yesterday's Layer0 v2 ship (commit 353dfc6)
verdict: ★ mechanical pattern follow-up — closes Layer0 v2 leftovers, no surprises
---

# Layer0 v2 leftovers — get_by_id + dedupe + guard TTL

Yesterday's `353dfc6` diary tracked 3 leftovers from the upstream
`f2e70860` ship that were "mechanical follow-ups". Today's commit
`7079216` lands them in one batch.

## What ships

### 1. `Layer0Client.get_by_id(*, id, namespace) → Layer0Hit | None`

Wraps the `GetMemoryById` RPC that came in upstream f2e70860. Point
lookup, no semantic ranking — `distance` is always 0.0 for the
returned hit. `tags` and `created_at_ms` come back from the
server-side metadata.

Returns `None` when:
- client disabled (LAYER0_GRPC_URL unset)
- empty namespace or negative id
- slot exists but content is empty (server returns id=0 + empty
  content for unused slots)
- transport error

Use case: audit / replay — if a memory id surfaces in a trace event
or a UI, fetch its current state without re-running a search.

### 2. `dedupe_hits(hits, prefix_len=80)` — module-level pure function

Folds hits whose `text` shares the first `prefix_len` characters.
The hit with lower `distance` (= better match) wins; ties broken
by earlier position in the input. Order otherwise preserved.

Why prefix instead of full string: every gitoma-ingested memory
shape today (plan summaries, guard firings, PR outcomes) has a
stable discriminator in its first ~80 chars. A prefix fold collapses
the noise without false positives on legitimately-different texts
that happen to start the same way (the discriminator differentiates).

Wired into PHASE 1.5:
- per-bucket on `search_grouped` (collapses near-identical bucket
  hits without crossing bucket boundaries — the planner still sees
  the bucket structure even when one fact is tagged twice)
- on the flat-search fallback path (which collides way more often
  because there's no tag separation)

Caller can disable with `prefix_len=0` (no-op for testing). Operating
on `Layer0Hit` makes it usable on grouped or flat results uniformly.

### 3. `LAYER0_GUARD_TTL_DAYS` env knob — PHASE 8

When `LAYER0_GUARD_TTL_DAYS > 0`, guard-fail memories get
`ttl_ms = days × 86400000` (passed through to the existing
`ingest_one(ttl_ms=...)` kwarg from the v2 ship). Default 0 means
"forever" — existing behaviour preserved, additive backward-compat.

Pinned + plan-source + outcome memories untouched. Only guard-fail
gets the TTL because that's the high-volume noise category — a
flaky-test G14 firing pattern can flood the namespace within
weeks. Outcomes ("PR shipped #N") are low volume and worth keeping;
plan-source memories carry their own pinned-when-curated logic.

## Pattern proven

Three categories of layer0 server features have now been wired up
in 3 successive commits:

| Commit | Server features | Wire-in |
|--------|-----------------|---------|
| `6655038` | base IngestMemories / SearchByText / ListNamespaces | initial PHASE 1.5/8 |
| `353dfc6` | search_grouped + tag_all_of + pinned + ttl_ms | bucketised search + pinned plan-source |
| **`7079216`** | **GetMemoryById + dedupe (client) + ttl wire** | **PHASE 1.5 dedup + PHASE 8 guard TTL** |

`6655038`→`353dfc6` proved the additive-extension pattern works
upstream → client. `353dfc6`→`7079216` proves the same pattern
works for **internal** maturation: a client method (dedupe) added
without server changes, plus full use of v2 server features
deferred at v2 ship time. The leg is no longer "tracking upstream"
— it's now self-contained operational maturity.

## Stats

10 new tests:
- 3 × `get_by_id` (disabled returns None, empty-ns returns None,
  negative-id returns None — silent fail-open path)
- 7 × `dedupe_hits` (empty input, all-unique pass-through,
  same-prefix collapse keeps closer, short-text full-string fold,
  order preservation, zero-prefix no-op, custom prefix len)

Suite: 1771 → **1781** verde. PHASE 1.7 ships earlier this morning
(commit `e46752d`) brought us to 1781; this commit replaces the
previous 5 layer0-tests count with 15 (+10 net).

## Cumulative session count

9 commits over the last ~13h (2026-04-28 evening → 2026-04-29 AM):

| # | Commit | Cosa |
|---|--------|------|
| 1 | `bc18a95` | --plan-from-file |
| 2 | `e95f658` | CPG-staleness fix |
| 3 | `abf1cff` | PHASE 7 diary |
| 4 | `6655038` | Layer0 client v1 |
| 5 | `ca6562c` | PHASE 1.5 + 8 wire-in |
| 6 | `83690cc` + `3a8e160` | gitoma scaffold |
| 7 | `353dfc6` | Layer0 v2 (grouped + pinned + tag_all_of) |
| 8 | `e46752d` | PHASE 1.7 stack-shape context |
| 9 | **`7079216`** | **Layer0 v2 leftovers (get_by_id + dedupe + guard TTL)** |

Layer0 leg is now feature-complete relative to the current upstream
proto surface: every f2e70860 RPC that gitoma can use is wired in.
Next backlog: 4th spider leg (semgrep / license-checker / reuse-tool).
