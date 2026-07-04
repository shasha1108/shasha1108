#!/usr/bin/env python3
"""
Sync profile README's '✦ 最新作品' section with the 5 most recent works
from healing-visual-lab/works.json.

Run: python3 scripts/sync-latest-works.py [--dry-run]
Cron: 10:07 every Wednesday (see CLAUDE.md or CronCreate config)
"""
import json, re, sys, subprocess
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
PAGES_BASE = "https://shasha1108.github.io/healing-visual-lab"
TOP_N = 5


def fetch_works():
    """Fetch works.json from healing-visual-lab via gh api."""
    result = subprocess.run(
        ["gh", "api", "repos/shasha1108/healing-visual-lab/contents/works.json",
         "--jq", ".content"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api failed: {result.stderr}")
    import base64
    return json.loads(base64.b64decode(result.stdout.strip()))


def build_table(works):
    """Build the HTML table rows for the top N works."""
    rows = []
    for w in works[:TOP_N]:
        slug = w["slug"]
        title_zh = w.get("title_zh", "")
        title_en = w.get("title_en", "")
        tagline = (w.get("tagline", "") or "")[:70]
        url = f"{PAGES_BASE}/{slug}/{slug}.html"
        rows.append(
            f'<tr><td><b><a href="{url}">{title_zh} / {title_en}</a></b></td>'
            f'<td>{tagline}</td></tr>'
        )
    return (
        '<table width="100%">\n'
        '<tr><th width="30%">作品</th><th  width="70%">一句话</th></tr>\n'
        + "\n".join(rows)
        + "\n</table>"
    )


def update_readme(table_html):
    """Replace content between LATEST_WORKS_START and LATEST_WORKS_END markers."""
    readme_path = ROOT / "README.md"
    content = readme_path.read_text()

    pattern = r"(<!-- LATEST_WORKS_START -->).*?(<!-- LATEST_WORKS_END -->)"
    replacement = f"\\1\n{table_html}\n\\2"

    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
    if count == 0:
        print("ERROR: LATEST_WORKS_START/END markers not found in README.md")
        return False
    if new_content == content:
        print("No changes — already up to date.")
        return False

    readme_path.write_text(new_content)
    return True


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print("Fetching works from shasha1108/healing-visual-lab ...")
    data = fetch_works()
    works = data["works"]
    print(f"  {len(works)} works total, top {TOP_N}:")

    for i, w in enumerate(works[:TOP_N], 1):
        print(f"  {i}. [{w['date']}] {w['slug']} — {w.get('tagline','')[:50]}")

    table = build_table(works)

    if dry_run:
        print("\n[dry-run] Would write:\n")
        print(table)
        sys.exit(0)

    if update_readme(table):
        print("\nREADME.md updated ✓")
    else:
        sys.exit(0)

    # Show diff
    import subprocess
    subprocess.run(["git", "-C", str(ROOT), "diff", "--stat"], check=False)
