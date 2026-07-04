#!/usr/bin/env python3
"""
Sync '最新作品 / Latest Works' section across all 4 profile pages
from healing-visual-lab/works.json.

Files updated:
  README.md     → CN table (作品 / 一句话)
  README_EN.md  → EN table (Work / In One Line)
  index.html    → CN table
  index_en.html → EN table

Run: python3 scripts/sync-latest-works.py [--dry-run]
Cron: GitHub Actions — Wed 10:00 Beijing time
"""
import json, re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKS_RAW_URL = "https://raw.githubusercontent.com/shasha1108/healing-visual-lab/main/works.json"
PAGES_BASE = "https://shasha1108.github.io/healing-visual-lab"
TOP_N = 5

# Which files get which table variant
CN_FILES = ["README.md", "index.html"]
EN_FILES = ["README_EN.md", "index_en.html"]


def fetch_works():
    """Fetch works.json via curl (public repo, no auth needed)."""
    result = subprocess.run(
        ["curl", "-sS", "--retry", "2", "-f", WORKS_RAW_URL],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    return json.loads(result.stdout)


def build_table(works, lang="cn"):
    """Build the HTML table for top N works."""
    if lang == "cn":
        h_title = "作品"
        h_tagline = "一句话"
    else:
        h_title = "Work"
        h_tagline = "In One Line"

    rows = []
    for w in works[:TOP_N]:
        slug = w["slug"]
        title_zh = w.get("title_zh", "")
        title_en = w.get("title_en", "")
        tagline = (w.get("tagline", "") or "")[:70]
        url = f"{PAGES_BASE}/{slug}/{slug}.html"

        if lang == "cn":
            if title_zh and title_zh != title_en:
                display_title = f"{title_zh} / {title_en}"
            else:
                display_title = title_en  # same text or no zh → just show once
            display_tagline = tagline
        else:
            # EN: only English title; use English title as tagline
            # (works.json has no English taglines — Chinese must NOT leak into EN pages)
            display_title = title_en
            display_tagline = title_en

        rows.append(
            f'<tr><td><b><a href="{url}">{display_title}</a></b></td>'
            f'<td>{display_tagline}</td></tr>'
        )
    return (
        f'<table width="100%">\n'
        f'<tr><th width="30%">{h_title}</th><th  width="70%">{h_tagline}</th></tr>\n'
        + "\n".join(rows)
        + "\n</table>"
    )


def update_file(filepath, table_html):
    """Replace content between LATEST_WORKS_START and LATEST_WORKS_END markers.
    Only touches the marked block — all other content is preserved exactly."""
    content = filepath.read_text()

    # ── Safety 1: verify exactly 1 marker pair exists ──
    start_count = content.count("<!-- LATEST_WORKS_START -->")
    end_count = content.count("<!-- LATEST_WORKS_END -->")
    if start_count != 1 or end_count != 1:
        return f"BAD_MARKERS (START={start_count}, END={end_count})"

    # ── Safety 2: generated table must not contain marker strings ──
    if "LATEST_WORKS" in table_html:
        return "TABLE_CONTAINS_MARKER (refusing to write)"

    # ── Replace ONLY between markers ──
    pattern = r"(<!-- LATEST_WORKS_START -->).*?(<!-- LATEST_WORKS_END -->)"
    replacement = f"\\1\n{table_html}\n\\2"
    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if count != 1:
        return "REGEX_FAILED"  # should not happen since we validated counts

    if new_content == content:
        # ── Safety 3: verify markers intact in unchanged file ──
        if new_content.count("<!-- LATEST_WORKS_START -->") != 1:
            return "MARKERS_CORRUPTED"
        return "UNCHANGED"

    # ── Safety 4: post-write marker count ──
    if new_content.count("<!-- LATEST_WORKS_START -->") != 1 or \
       new_content.count("<!-- LATEST_WORKS_END -->") != 1:
        return "MARKERS_LOST_ON_WRITE (aborted)"
    if new_content.count("LATEST_WORKS_START") != start_count:
        return "MARKER_COUNT_CHANGED (aborted)"

    filepath.write_text(new_content)
    return "UPDATED"


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print("Fetching works from healing-visual-lab ...")
    data = fetch_works()
    works = data["works"]
    print(f"  {len(works)} works total, top {TOP_N}:")
    for i, w in enumerate(works[:TOP_N], 1):
        print(f"  {i}. [{w['date']}] {w['slug']} — {w.get('tagline','')[:50]}")

    cn_table = build_table(works, "cn")
    en_table = build_table(works, "en")

    if dry_run:
        print("\n[dry-run] Would write:\n")
        print("── CN table (README.md, index.html) ──")
        print(cn_table)
        print("\n── EN table (README_EN.md, index_en.html) ──")
        print(en_table)
        sys.exit(0)

    any_updated = False
    errors = []
    results = {}

    for fname in CN_FILES:
        status = update_file(ROOT / fname, cn_table)
        results[fname] = status
        if status == "UPDATED":
            any_updated = True
        elif status.startswith("BAD_MARKERS") or status.startswith("TABLE_CONTAINS") \
             or status.startswith("MARKERS_LOST") or status.startswith("MARKER_COUNT") \
             or status.startswith("REGEX_FAILED"):
            errors.append(f"{fname}: {status}")

    for fname in EN_FILES:
        status = update_file(ROOT / fname, en_table)
        results[fname] = status
        if status == "UPDATED":
            any_updated = True
        elif status.startswith("BAD_MARKERS") or status.startswith("TABLE_CONTAINS") \
             or status.startswith("MARKERS_LOST") or status.startswith("MARKER_COUNT") \
             or status.startswith("REGEX_FAILED"):
            errors.append(f"{fname}: {status}")

    # ── Report ──
    print(f"\n{'─'*40}")
    print("Sync scope: ONLY content between LATEST_WORKS markers")
    print("Files touched vs untouched:")
    for fname, status in sorted(results.items()):
        marker = "✏️" if status == "UPDATED" else ("❌" if "BAD" in status or "LOST" in status or "CONTAINS" in status or "FAILED" in status else "✓")
        print(f"  {marker} {fname}: {status}")
    print(f"{'─'*40}")

    if errors:
        print(f"\n❌ FATAL: {len(errors)} safety violation(s) — sync ABORTED, no files written:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    if not any_updated:
        print("\nAll files already up to date — nothing to commit.")
        sys.exit(0)

    print(f"\n✓ {sum(1 for s in results.values() if s == 'UPDATED')} file(s) updated.")
    print("  Other sections (About Me, Gallery, Skills, banners, badges) were NOT touched.")
    print("\nDiff:")
    subprocess.run(["git", "-C", str(ROOT), "diff", "--stat"], check=False)
    subprocess.run(["git", "-C", str(ROOT), "diff"], check=False)
