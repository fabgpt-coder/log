---
date: 2026-04-29T23:55:00+02:00
type: feature-shipped
gitoma_commits: [da072aa]
context: ship G24 to close the qwen3-8b weird-poetry-shape gap from the EVE A/B bench
verdict: ★ G23+G24 now paired — keys + shapes covered for pyproject.toml [tool.X] sections
---

# G24 config-structure critic

The EVE A/B bench (gemma vs qwen3-8b on the same target with G23
ON) found that qwen3-8b's PR #10 emitted:

    [tool.poetry]
    dependencies = [
        "pytest", "mypy", "poetry"
    ]

This is syntactically valid TOML — `dependencies` is a string-array
under the `tool.poetry` table — but Poetry requires `dependencies`
to be its OWN table (`[tool.poetry.dependencies]` followed by
`name = "version-spec"` lines). The list-of-strings form will be
rejected by Poetry at install time with a confusing error message.

G23 silent-passes `[tool.poetry]` because we listed it in the
`_TYPO_ONLY_SECTIONS` set (poetry's sub-table vocabulary is
operator-defined, can't enforce closed-set keys without false
positives). G24 fills the gap with a different angle: validate
the SHAPE not the keys.

## What G24 does

For every touched `pyproject.toml`:

1. Parse with tomllib.
2. For each path in `_STRUCTURE_RULES`, drill into the parsed dict
   and check the value's TYPE matches the expected one
   ("table" / "list" / "scalar").
3. Mismatches become `G24Conflict` records with the path, expected
   type, actual type, and a corrective intent message.
4. Diff-aware: when worker provides pre-patch text, only flag paths
   where the violation is NEW. Pre-existing wrong-shape sections in
   the baseline are left alone.

## Catalog (11 paths covered)

The closed-set is intentionally narrow — only patterns observed
in real LLM output OR in heavily-confused PEP-621 / Poetry
mappings:

**Poetry-side (all → table)**:
- `tool.poetry.dependencies`
- `tool.poetry.dev-dependencies` (legacy <1.2)
- `tool.poetry.optional-dependencies`
- `tool.poetry.extras`
- `tool.poetry.scripts`
- `tool.poetry.plugins`

**uv**:
- `tool.uv.dependency-groups` → table

**PEP-621 [project]** — opposite polarity from Poetry, the
historical confusion source:
- `project.dependencies` → **LIST** (PEP-508 string array)
- `project.optional-dependencies` → table (group → list)
- `project.scripts` → table
- `project.authors` → list of `{name, email}` tables

The PEP-621 entries are critical because LLMs trained on Poetry
examples often emit Poetry-style table form for `[project]`
sections, which is wrong.

## Why opt-in

Same reasoning as G23: closed-set is intentionally narrow,
operators may use legitimate config patterns the catalog doesn't
know about. Default OFF, opt-in via
`GITOMA_G24_CONFIG_STRUCTURE=1`. When the operator turns it on
they should also be running G23 — the two critics complement each
other:

- **G23** = "invalid keys in catalog tool sections"
  (`suppress_missing_imports` instead of `ignore_missing_imports`)
- **G24** = "valid keys in catalog sections, wrong shape"
  (`tool.poetry.dependencies = [...]` instead of `[tool.poetry.dependencies]`)

Together they cover the schema-quality surface that schemastore-
based G10 doesn't reach for pyproject.toml.

## Limitations (non-goals)

- **No wildcard for `tool.poetry.group.*` sub-tables**. Poetry
  1.2+ groups (e.g. `[tool.poetry.group.dev.dependencies]`) have
  operator-defined names; pattern-matching them risks false
  positives. Backlog item if seen wrong in practice.
- **No value-shape validation inside tables**. We check
  `tool.poetry.dependencies` is a TABLE; we don't check that each
  entry's VALUE is a string version-spec or a `{version, ...}`
  inline table. Out of scope for v1 — G23 + tomlbuild-time
  validation cover this.
- **Multi-tool sections with the same dotted-path** (e.g. some
  tool happens to put `dependencies` under `[tool.X]` as a list
  legitimately). The closed-set targets only well-documented
  conventions; unknown tools silent-pass.

## Tests + suite

32 tests covering:
- Env opt-in (5 truthy variants + falsy + default)
- 6 silent-skip paths (disabled / no-pyproject / bad-root /
  missing file / unparseable TOML / no relevant sections)
- The qwen3-8b PR #10 case directly (the canonical exemplar)
- Adjacent poetry violations (scripts/extras as list)
- PEP-621 opposite-polarity cases (project.dependencies must be
  LIST, project.optional-dependencies must be table, authors
  must be array of tables)
- Diff-mode behavior (only-new-flagged, pre-existing-untouched,
  brand-new-section, new-file)
- Multi-file monorepo aggregation
- Render output (path + types + intent)
- Frozen dataclass invariants

Suite: 2000 → **2032** verde.

G-stack: 24 active critics (G1-G24 minus G17). PHASE blocks:
1 / 1.5 / 1.6 / 1.7 / 1.8 / 7 / 8.

## Stats — session day

5 commits today (LATE-EVE wave):
- `aa0a04c` G23 config-keys
- `8bf82d2` G13 bulk-shrinkage
- `016a510` semgrep --metrics-off bug fix
- `da072aa` **G24 config-structure**

Plus the supply-chain bench corpus repo (separate from gitoma
commits) and the morning's PHASE 1.6/1.7/1.8 + G21/G22 + Layer0 v2
leftovers + RepoBrief framework extraction shipping streak.

The bench-driven methodology continues to compound. Today's bench
corpus build → semgrep silent-bail bug surfaced → fix shipped.
EVE A/B bench → qwen3-8b weird-poetry shape surfaced → G24 ships.
Each finding closed the same evening, no overnight backlog.

The G23 + G24 pair is the canonical "schema critic for pyproject"
shape. Adding new tool catalogs (polars/black/isort/etc) is now
mechanical — extend the closed-set dicts. Future G25 candidate:
extend to `package.json` (npm-style schema validation for scripts /
peerDependencies).
