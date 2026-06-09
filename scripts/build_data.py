#!/usr/bin/env python3
"""Parse entries/*.md frontmatter → emit data + README.

Outputs:
- docs/public/prs.json — array of PR objects consumed by the VitePress site
- docs/index.md        — homepage (stats + brief + link to /prs)
- README.md            — minimal GitHub front door: stats glance + link to site

Only entries with a `pr_url` count. Other entries (failed runs w/o PR,
hand-written narrative) are skipped — the table shows shipped PRs only.

Run from repo root:  python3 scripts/build_data.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
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

SITE_URL = os.environ.get("SITE_URL", "https://fabgpt-coder.github.io/log/")


# ---------------------------------------------------------------------------
# Parsing
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
    if not pr_url:
        return None  # only PRs count

    date = _parse_date(fm.get("date"), path.name)
    if date is None:
        return None

    pr = fm.get("pr")
    pr_num = int(pr) if isinstance(pr, int) or (isinstance(pr, str) and pr.isdigit()) else None
    repo = str(fm.get("repo") or "").strip()
    subs = str(fm.get("subtasks_done") or "").strip()
    subs_num, subs_den = _parse_subtasks(subs)

    return {
        "date": date.isoformat(),
        "ts": int(date.timestamp()),
        "repo": repo,
        "repo_short": repo.split("/", 1)[1] if "/" in repo else repo,
        "owner": repo.split("/", 1)[0] if "/" in repo else "",
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
        "verdict": _normalize_verdict(str(fm.get("verdict") or "").strip()),
        "verdict_class": _classify_verdict(str(fm.get("verdict") or "")),
        "entry_path": f"entries/{path.name}",
        "entry_url": f"https://github.com/fabgpt-coder/log/blob/main/entries/{path.name}",
    }


def _parse_date(raw, fallback_name: str) -> dt.datetime | None:
    if isinstance(raw, dt.datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=dt.timezone.utc)
    if isinstance(raw, dt.date):
        return dt.datetime.combine(raw, dt.time(0, 0), tzinfo=dt.timezone.utc)
    if isinstance(raw, str) and raw:
        try:
            d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            pass
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(\d{2})(\d{2})", fallback_name)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        return dt.datetime(y, mo, d, h, mi, tzinfo=dt.timezone.utc)
    return None


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
    return "other"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(prs: list[dict]) -> dict:
    verdicts = Counter(p["verdict_class"] for p in prs)
    subs_num = sum(p["subs_num"] for p in prs)
    subs_den = sum(p["subs_den"] for p in prs)
    guards = Counter()
    for p in prs:
        for g in p["guards"]:
            guards[g] += 1
    models = Counter(p["model"] for p in prs if p["model"])
    repos = Counter(p["repo_short"] for p in prs if p["repo_short"])
    days = sorted({p["date"][:10] for p in prs})
    return {
        "prs_total": len(prs),
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
    v = s["verdicts"]

    def vc(name: str) -> int:
        return v.get(name, 0)

    verdict_line = " · ".join(
        f"{n} {vc(n)}" for n in ("clean", "partial", "failed", "milestone", "other")
        if vc(n)
    ) or "—"
    subs = f"{s['subs_num']}/{s['subs_den']} ({s['subs_pct']}%)" if s["subs_den"] else "—"
    span = (
        f"{s['active_days']} active days ({s['first_day']} → {s['last_day']})"
        if s["first_day"] else "—"
    )

    def top(items, label: str) -> str:
        if not items:
            return f"_No {label} yet._"
        return " · ".join(f"`{k}` ({v})" for k, v in items)

    return (
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| PRs shipped | **{s['prs_total']}** |\n"
        f"| Subtasks completed | {subs} |\n"
        f"| Distinct repos | {s['distinct_repos']} |\n"
        f"| Distinct models | {s['distinct_models']} |\n"
        f"| Guard firings | {s['guard_firings']} |\n"
        f"| Activity span | {span} |\n"
        "\n"
        f"**Verdict mix** — {verdict_line}\n\n"
        f"**Top models** — {top(s['top_models'], 'models')}\n\n"
        f"**Top repos** — {top(s['top_repos'], 'repos')}\n\n"
        f"**Top guards** — {top(s['top_guards'], 'guard firings')}\n"
    )


def render_readme(stats: dict, today: str) -> str:
    return f"""# fabgpt-coder — operations log

Public timeline of pull requests shipped by **`fabgpt-coder`**, the [gitoma](https://github.com/fabriziosalmi/gitoma)-powered AI agent operated by [@fabriziosalmi](https://github.com/fabriziosalmi). One row per PR. Each PR has a machine-readable frontmatter entry — model, endpoint, plan source, subtasks completed, guards that fired, verdict — written automatically by gitoma's PHASE 7 hook at the end of every successful run.

> **Full browsable archive →** [{SITE_URL.rstrip('/')}/]({SITE_URL})

## At a glance — {today}

{render_stats_table(stats)}
---

- Source of truth: `entries/*.md` (one file per PR, append-only).
- Rebuilt daily by [`scripts/build_data.py`](scripts/build_data.py) via [`.github/workflows/build-site.yml`](.github/workflows/build-site.yml).
- Site is generated with VitePress under [`docs/`](docs/) and deployed to GitHub Pages.
"""


def render_homepage(stats: dict, prs: list[dict], today: str) -> str:
    """docs/index.md — VitePress homepage."""
    s = stats
    v = s["verdicts"]

    def vc(name: str) -> int:
        return v.get(name, 0)

    verdict_line = " · ".join(
        f"`{n}` {vc(n)}" for n in ("clean", "partial", "failed", "milestone", "other")
        if vc(n)
    ) or "—"
    subs = f"{s['subs_num']}/{s['subs_den']} ({s['subs_pct']}%)" if s["subs_den"] else "—"

    def top(items) -> str:
        if not items:
            return "—"
        return " · ".join(f"`{k}` ({v})" for k, v in items[:5])

    # Frontmatter for VitePress home layout
    fm = """---
layout: home
hero:
  name: fabgpt-coder
  text: operations log
  tagline: every PR shipped by my AI agent, with the receipts
  actions:
    - theme: brand
      text: Browse all PRs →
      link: /prs
    - theme: alt
      text: View on GitHub
      link: https://github.com/fabgpt-coder/log
features:
  - title: PRs shipped
    details: '%PRS%'
  - title: Subtasks completed
    details: '%SUBS%'
  - title: Distinct repos × models
    details: '%REPMOD%'
---

""".replace("%PRS%", str(s["prs_total"])) \
    .replace("%SUBS%", subs) \
    .replace("%REPMOD%", f"{s['distinct_repos']} repos · {s['distinct_models']} models")

    body = f"""
## At a glance — {today}

**Verdict mix** — {verdict_line}

**Top models** — {top(s['top_models'])}

**Top repos** — {top(s['top_repos'])}

**Top guards** — {top(s['top_guards'])}

**Activity** — {s['active_days']} active days ({s['first_day'] or '—'} → {s['last_day'] or '—'})

---

→ [Browse all {s['prs_total']} PR{'s' if s['prs_total'] != 1 else ''} with filters & search](/prs)
"""
    return fm + body


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not ENTRIES_DIR.exists():
        ENTRIES_DIR.mkdir(parents=True)

    prs: list[dict] = []
    for path in sorted(ENTRIES_DIR.glob("*.md")):
        rec = parse_entry(path)
        if rec is not None:
            prs.append(rec)
    prs.sort(key=lambda r: r["ts"], reverse=True)

    stats = compute_stats(prs)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    # Data file for the Vue table
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(
        json.dumps({"generated_at": today, "stats": stats, "prs": prs}, indent=2),
        encoding="utf-8",
    )

    # Homepage + README
    INDEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    INDEX_OUT.write_text(render_homepage(stats, prs, today), encoding="utf-8")
    README.write_text(render_readme(stats, today), encoding="utf-8")

    print(f"wrote {DATA_OUT.relative_to(ROOT)} ({len(prs)} PRs)")
    print(f"wrote {INDEX_OUT.relative_to(ROOT)}")
    print(f"wrote {README.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
