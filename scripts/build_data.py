#!/usr/bin/env python3
"""Build prs.json + README + homepage from GitHub PRs and local entries/.

Source of truth has two layers:

1. GitHub search API — every PR ever authored by the bot account
   (AGENT_GH_LOGIN, defaults to fabgpt-coder). This guarantees the full
   history is tracked from the very first PR, regardless of whether the
   agent wrote a diary entry for it.

2. entries/*.md frontmatter — when present, enriches the matching PR row
   with the agent's own diary: model, endpoint, plan source, subtasks,
   guards, verdict. The (repo, pr_number) pair is the join key.

Outputs:
- docs/public/prs.json
- docs/index.md     (VitePress homepage)
- README.md         (GitHub front door)

Auth: uses GITHUB_TOKEN if set (always set inside GitHub Actions),
otherwise calls the API unauthenticated (60 req/hour rate limit).

Run from repo root:  python3 scripts/build_data.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "entries"
DOCS_DIR = ROOT / "docs"
DATA_OUT = DOCS_DIR / "public" / "prs.json"
INDEX_OUT = DOCS_DIR / "index.md"
README = ROOT / "README.md"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

AGENT_LOGIN = os.environ.get("AGENT_GH_LOGIN", "fabgpt-coder")
SITE_URL = os.environ.get("SITE_URL", "https://fabgpt-coder.github.io/log/")
LOG_REPO = os.environ.get("LOG_REPO", "fabgpt-coder/log")
GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


# ---------------------------------------------------------------------------
# GitHub fetch
# ---------------------------------------------------------------------------

def fetch_prs_from_github(author: str) -> list[dict]:
    """Search every PR ever opened by `author`. Public repos only."""
    items: list[dict] = []
    per_page = 100
    page = 1
    while True:
        params = urllib.parse.urlencode(
            {
                "q": f"type:pr author:{author} is:public",
                "per_page": per_page,
                "page": page,
                "sort": "created",
                "order": "desc",
            }
        )
        url = f"https://api.github.com/search/issues?{params}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"fabgpt-coder-log-builder/{author}",
        }
        if GH_TOKEN:
            headers["Authorization"] = f"Bearer {GH_TOKEN}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:400]
            print(f"error: GitHub search failed: {e.code} {e.reason} — {body}",
                  file=sys.stderr)
            raise
        batch = payload.get("items", [])
        items.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
        if page > 20:  # 2000 PRs cap, well above any realistic backlog
            print(f"warn: stopping pagination at page {page} (cap reached)",
                  file=sys.stderr)
            break
    return items


def normalize_gh_item(item: dict) -> dict | None:
    """Project a GitHub search result into our PR record shape."""
    html_url = item.get("html_url") or ""
    # repository_url = https://api.github.com/repos/owner/name
    repo_full = ""
    repo_api = item.get("repository_url") or ""
    if repo_api.startswith("https://api.github.com/repos/"):
        repo_full = repo_api[len("https://api.github.com/repos/"):]
    if not repo_full and "/pull/" in html_url:
        # fallback: parse from html_url
        m = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/\d+", html_url)
        if m:
            repo_full = m.group(1)
    if not repo_full:
        return None

    pr_num = item.get("number")
    if not isinstance(pr_num, int):
        return None

    created_at = item.get("created_at")
    if not created_at:
        return None
    try:
        date = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return None

    pr_info = item.get("pull_request") or {}
    merged_at = pr_info.get("merged_at")
    state_raw = item.get("state") or "open"
    if merged_at:
        state = "merged"
    elif state_raw == "closed":
        state = "closed"
    else:
        state = "open"

    owner, _, name = repo_full.partition("/")
    return {
        "date": date.isoformat(),
        "ts": int(date.timestamp()),
        "repo": repo_full,
        "owner": owner,
        "repo_short": name,
        "pr": pr_num,
        "pr_url": html_url,
        "title": item.get("title") or "",
        "state": state,
        "merged_at": merged_at,
        "closed_at": item.get("closed_at"),
        "is_draft": bool(item.get("draft")),
        # entry-overridable fields (defaults)
        "branch": "",
        "model": "",
        "model_full": "",
        "endpoint": "",
        "plan_source": "",
        "subtasks_done": "",
        "subs_num": 0,
        "subs_den": 0,
        "subs_pct": None,
        "guards": [],
        "verdict": "",
        "verdict_class": _state_to_verdict_class(state),
        "entry_path": "",
        "entry_url": "",
        "source": "github",
    }


def _state_to_verdict_class(state: str) -> str:
    return {"merged": "merged", "closed": "closed", "open": "open"}.get(state, "other")


# ---------------------------------------------------------------------------
# Entry parsing
# ---------------------------------------------------------------------------

def parse_entry(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        print(f"warn: yaml error in {path.name}: {e}", file=sys.stderr)
        return None
    if not isinstance(fm, dict):
        return None

    pr_url = str(fm.get("pr_url") or "").strip()
    repo = str(fm.get("repo") or "").strip()
    pr = fm.get("pr")
    pr_num = int(pr) if isinstance(pr, int) or (isinstance(pr, str) and str(pr).isdigit()) else None

    # Need repo + pr_num to be useful for the merge.
    if not repo or pr_num is None:
        # Hand-written narrative without a PR — skip entirely.
        return None

    subs = str(fm.get("subtasks_done") or "").strip()
    subs_num, subs_den = _parse_subtasks(subs)
    verdict_raw = str(fm.get("verdict") or "").strip()

    return {
        "repo": repo,
        "pr": pr_num,
        "pr_url": pr_url,
        "branch": str(fm.get("branch") or "").strip(),
        "model": _short_model(str(fm.get("model") or "")),
        "model_full": str(fm.get("model") or "").strip(),
        "endpoint": str(fm.get("endpoint") or "").strip(),
        "plan_source": str(fm.get("plan_source") or "").strip(),
        "subtasks_done": subs,
        "subs_num": subs_num,
        "subs_den": subs_den,
        "subs_pct": (round(100 * subs_num / subs_den, 1) if subs_den else None),
        "guards": _parse_guards(fm.get("guards_fired")),
        "verdict": _normalize_verdict(verdict_raw),
        "verdict_class": _classify_verdict(verdict_raw),
        "entry_path": f"entries/{path.name}",
        "entry_url": f"https://github.com/{LOG_REPO}/blob/main/entries/{path.name}",
    }


def _short_model(s: str) -> str:
    return s.split("/")[-1] if s else ""


def _parse_subtasks(s: str) -> tuple[int, int]:
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _parse_guards(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        stripped = raw.strip().strip("[]")
        return [x.strip() for x in stripped.split(",") if x.strip()] if stripped else []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


_LEADING_DECOR = re.compile(r"^(?:[★✅◐❌·⚠️\s]+)")


def _normalize_verdict(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return _LEADING_DECOR.sub("", s).strip() or "—"


def _classify_verdict(raw: str) -> str:
    low = raw.lower()
    if "★" in raw:
        return "milestone"
    if low.startswith("clean") or "clean baseline" in low or "clean win" in low:
        return "clean"
    if "❌" in raw or low.startswith("unusable") or low.startswith("dead"):
        return "failed"
    if low.startswith("partial") or "partial" in low.split("—")[0] or "pr opened" in low:
        return "partial"
    if "⚠" in raw:
        return "partial"
    return ""  # let the GH state fill in


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_entries(gh_records: list[dict], entries: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, int], dict] = {(r["repo"], r["pr"]): r for r in gh_records}
    for ent in entries:
        key = (ent["repo"], ent["pr"])
        rec = by_key.get(key)
        if rec is None:
            # entry references a PR we didn't see from the API (private? deleted?
            # author mismatch?) — synthesize a minimal record so it still shows.
            owner, _, name = ent["repo"].partition("/")
            rec = {
                "date": "",
                "ts": 0,
                "repo": ent["repo"],
                "owner": owner,
                "repo_short": name,
                "pr": ent["pr"],
                "pr_url": ent.get("pr_url") or "",
                "title": "",
                "state": "unknown",
                "merged_at": None,
                "closed_at": None,
                "is_draft": False,
                "verdict_class": "",
                "source": "entry-only",
            }
            by_key[key] = rec
        # Overlay entry fields (only non-empty ones win)
        for field in (
            "branch", "model", "model_full", "endpoint", "plan_source",
            "subtasks_done", "subs_num", "subs_den", "subs_pct",
            "guards", "verdict", "entry_path", "entry_url",
        ):
            val = ent.get(field)
            if val:
                rec[field] = val
        # Verdict class: prefer diary classification if non-empty
        if ent.get("verdict_class"):
            rec["verdict_class"] = ent["verdict_class"]
        rec["source"] = "entry+github" if rec.get("source") == "github" else rec.get("source", "entry")
    return list(by_key.values())


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(prs: list[dict]) -> dict:
    verdicts = Counter(p.get("verdict_class") or "open" for p in prs)
    states = Counter(p.get("state") or "unknown" for p in prs)
    subs_num = sum(p.get("subs_num", 0) for p in prs)
    subs_den = sum(p.get("subs_den", 0) for p in prs)
    guards = Counter()
    for p in prs:
        for g in p.get("guards", []):
            guards[g] += 1
    models = Counter(p["model"] for p in prs if p.get("model"))
    repos = Counter(p["repo_short"] for p in prs if p.get("repo_short"))
    days = sorted({p["date"][:10] for p in prs if p.get("date")})
    diary_count = sum(1 for p in prs if p.get("entry_path"))
    return {
        "prs_total": len(prs),
        "diary_count": diary_count,
        "states": dict(states),
        "verdicts": dict(verdicts),
        "subs_num": subs_num,
        "subs_den": subs_den,
        "subs_pct": round(100 * subs_num / subs_den, 1) if subs_den else None,
        "guard_firings": sum(guards.values()),
        "distinct_repos": len(repos),
        "distinct_models": len(models),
        "top_models": models.most_common(5),
        "top_repos": repos.most_common(5),
        "top_guards": guards.most_common(5),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "active_days": len(days),
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_stats_table(s: dict) -> str:
    st = s["states"]

    def pill(name: str, label: str) -> str:
        n = st.get(name, 0)
        return f"{label} {n}" if n else ""

    state_line = " · ".join(
        x for x in (pill("merged", "merged"), pill("open", "open"),
                    pill("closed", "closed"), pill("unknown", "unknown"))
        if x
    ) or "—"

    subs = f"{s['subs_num']}/{s['subs_den']} ({s['subs_pct']}%)" if s["subs_den"] else "—"
    span = (
        f"{s['active_days']} active days ({s['first_day']} → {s['last_day']})"
        if s["first_day"] else "—"
    )

    def top(items, label: str) -> str:
        if not items:
            return f"_no {label} yet_"
        return " · ".join(f"`{k}` ({v})" for k, v in items)

    return (
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| PRs total | **{s['prs_total']}** |\n"
        f"| State mix | {state_line} |\n"
        f"| Distinct repos | {s['distinct_repos']} |\n"
        f"| Distinct models | {s['distinct_models']} |\n"
        f"| Subtasks completed | {subs} |\n"
        f"| Guard firings | {s['guard_firings']} |\n"
        f"| Diary entries | {s['diary_count']} / {s['prs_total']} |\n"
        f"| Activity span | {span} |\n"
        "\n"
        f"**Top repos** — {top(s['top_repos'], 'repos')}\n\n"
        f"**Top models** — {top(s['top_models'], 'models')}\n\n"
        f"**Top guards** — {top(s['top_guards'], 'guard firings')}\n"
    )


def render_readme(stats: dict, today: str) -> str:
    return f"""# fabgpt-coder — operations log

Public timeline of every pull request shipped by **[`{AGENT_LOGIN}`](https://github.com/{AGENT_LOGIN})**, an AI coding agent operated by [@fabriziosalmi](https://github.com/fabriziosalmi). Each row is a real PR — merged, closed, or in-flight — across every public repo the agent has ever touched.

When the agent ships a richer diary entry alongside a PR (model, endpoint, subtasks completed, guards that fired, verdict), it gets surfaced too.

> **Full browsable archive → [{SITE_URL.rstrip('/')}/]({SITE_URL})**

## At a glance — {today}

{render_stats_table(stats)}
---

- Source of truth: GitHub PRs by [`{AGENT_LOGIN}`](https://github.com/{AGENT_LOGIN}) + diary entries under `entries/`.
- Rebuilt daily by [`scripts/build_data.py`](scripts/build_data.py) via [`.github/workflows/build-site.yml`](.github/workflows/build-site.yml).
- Site generated with VitePress under [`docs/`](docs/) and deployed to GitHub Pages.
"""


def render_homepage(stats: dict, today: str) -> str:
    s = stats
    st = s["states"]
    subs = f"{s['subs_num']}/{s['subs_den']} ({s['subs_pct']}%)" if s["subs_den"] else "—"

    def top(items) -> str:
        if not items:
            return "—"
        return " · ".join(f"`{k}` ({v})" for k, v in items[:5])

    fm = f"""---
layout: home
hero:
  name: fabgpt-coder
  text: operations log
  tagline: every pull request shipped by the agent, with the receipts
  actions:
    - theme: brand
      text: Browse all PRs →
      link: /prs
    - theme: alt
      text: View on GitHub
      link: https://github.com/{LOG_REPO}
features:
  - title: PRs shipped
    details: '{s["prs_total"]}'
  - title: Repos × models
    details: '{s["distinct_repos"]} repos · {s["distinct_models"]} models'
  - title: Diary coverage
    details: '{s["diary_count"]} / {s["prs_total"]} runs documented'
---

"""

    state_line = " · ".join(
        f"`{name}` {st.get(name, 0)}"
        for name in ("merged", "open", "closed", "unknown")
        if st.get(name, 0)
    ) or "—"

    body = f"""
## At a glance — {today}

**PR state mix** — {state_line}

**Top repos** — {top(s['top_repos'])}

**Top models** — {top(s['top_models'])}

**Top guards** — {top(s['top_guards'])}

**Subtasks completed** — {subs}

**Activity** — {s['active_days']} active days ({s['first_day'] or '—'} → {s['last_day'] or '—'})

---

→ [Browse all {s['prs_total']} PR{'s' if s['prs_total'] != 1 else ''} with filters & search](/prs)
"""
    return fm + body


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"fetching PRs by author '{AGENT_LOGIN}'…", file=sys.stderr)
    raw = fetch_prs_from_github(AGENT_LOGIN)
    gh_records: list[dict] = []
    for item in raw:
        rec = normalize_gh_item(item)
        if rec is not None:
            gh_records.append(rec)
    print(f"  got {len(gh_records)} PRs from GitHub", file=sys.stderr)

    if not ENTRIES_DIR.exists():
        ENTRIES_DIR.mkdir(parents=True)
    entries: list[dict] = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        rec = parse_entry(path)
        if rec is not None:
            entries.append(rec)
    print(f"  got {len(entries)} diary entries from entries/", file=sys.stderr)

    merged = merge_entries(gh_records, entries)
    merged.sort(key=lambda r: r.get("ts", 0), reverse=True)

    stats = compute_stats(merged)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(
        json.dumps({"generated_at": today, "agent": AGENT_LOGIN,
                    "stats": stats, "prs": merged}, indent=2),
        encoding="utf-8",
    )

    INDEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    INDEX_OUT.write_text(render_homepage(stats, today), encoding="utf-8")
    README.write_text(render_readme(stats, today), encoding="utf-8")

    print(f"wrote {DATA_OUT.relative_to(ROOT)} ({len(merged)} PRs)", file=sys.stderr)
    print(f"wrote {INDEX_OUT.relative_to(ROOT)}", file=sys.stderr)
    print(f"wrote {README.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
