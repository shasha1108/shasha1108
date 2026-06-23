#!/usr/bin/env python3
"""
Sync content from README.md → index.html while preserving all CSS/styling.

Reads README.md, extracts section blocks, rebuilds corresponding HTML
content in index.html between marker comments: <!-- SYNC:start --> and <!-- SYNC:end -->.
"""

import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
INDEX  = ROOT / "index.html"

# ── Content extractors ──

def heading_block(text: str, heading_keyword: str) -> str:
    """Extract content under ## heading_keyword until next ## or --- or <!DOCTYPE."""
    pat = rf'##\s+.*?{re.escape(heading_keyword)}.*?\n(.*?)(?=\n##\s|\n---\s|\Z)'
    m = re.search(pat, text, re.DOTALL)
    return m.group(1).strip() if m else ""

def code_block(text: str) -> str:
    """Extract first fenced code block from text."""
    m = re.search(r'```\n(.*?)```', text, re.DOTALL)
    return m.group(1).strip() if m else ""

def md_paragraphs(text: str) -> list[str]:
    """Remove code blocks, split into paragraphs, strip > prefixes for blockquotes."""
    clean = re.sub(r'```.*?```', '', text, flags=re.DOTALL).strip()
    blocks = re.split(r'\n\n+', clean)
    result = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith('>'):
            lines = [l.lstrip('> ').strip() for l in b.split('\n') if l.strip()]
            result.append(('blockquote', '<br>\n      '.join(lines)))
        else:
            result.append(('p', md_inline(b)))
    return result

def md_inline(text: str) -> str:
    """Basic inline markdown → HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


# ── Section builders ──

def build_about(readme: str) -> str:
    section = heading_block(readme, "About Me")
    if not section:
        return ""
    career = code_block(section)
    paras  = md_paragraphs(section)
    html   = []
    if career:
        html.append(f'    <div class="career-path">{career}</div>')
    html.append('')
    for tag, content in paras:
        if tag == 'blockquote':
            html.append(f'    <blockquote>\n      {content}\n    </blockquote>')
        else:
            html.append(f'    <p>{content}</p>')
    return '\n'.join(html)

def build_tech(readme: str) -> str:
    section = heading_block(readme, "技术光谱")
    if not section:
        return ""
    spectrum = code_block(section)
    if spectrum:
        return f'    <div class="tech-spectrum">{spectrum}</div>'
    return ""

def build_hvl_description(readme: str) -> str:
    """Extract HVL description paragraph (not the table)."""
    section = heading_block(readme, "Healing Visual Lab")
    if not section:
        return ""
    # Get the paragraph before the first table or ### heading
    m = re.search(r'^([^|\n].*?)(?=\n\n\||\n###|\n\||\n<p)', section, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        html = []
        for block in re.split(r'\n\n+', desc):
            block = block.strip()
            if block.startswith('>'):
                lines = [l.lstrip('> ').strip() for l in block.split('\n') if l.strip()]
                html.append(f'    <blockquote>{"<br>".join(lines)}</blockquote>')
            elif block:
                html.append(f'    <p>{md_inline(block)}</p>')
        return '\n'.join(html) if html else ""
    return ""

def build_footer(readme: str) -> str:
    """Extract footer lines after the last --- separator."""
    parts = readme.split('\n---\n')
    if len(parts) < 2:
        return ""
    footer_section = parts[-1].strip()
    # Take the last few meaningful paragraphs
    paras = [p.strip() for p in footer_section.split('\n\n') if p.strip() and not p.strip().startswith('##')]
    html = []
    for p in paras[:3]:
        if p.startswith('<'):
            html.append(p)  # HTML as-is
        else:
            html.append(f'    <p><em>{md_inline(p)}</em></p>')
    return '\n'.join(html) if html else ""


# ── Section mapping: marker_id → builder ──
SECTIONS = {
    "about-section": build_about,
    "tech-section":  build_tech,
    "hvl-desc":      build_hvl_description,
    # footer-text excluded — index.html has its own footer with language toggle
}


def sync(readme_text: str, index_text: str) -> tuple[str, bool]:
    """Replace marked sections in index_text. Returns (new_text, changed)."""
    changed = False
    for marker, builder in SECTIONS.items():
        start_tag = f"<!-- SYNC:{marker} -->"
        end_tag   = f"<!-- /SYNC:{marker} -->"

        if start_tag not in index_text or end_tag not in index_text:
            continue

        new_content = builder(readme_text)
        if not new_content:
            continue

        pattern = rf'{re.escape(start_tag)}.*?{re.escape(end_tag)}'
        replacement = f'{start_tag}\n{new_content}\n      {end_tag}'
        new_text, count = re.subn(pattern, replacement, index_text, flags=re.DOTALL)
        if count:
            index_text = new_text
            changed = True
            print(f"  ✓ synced: {marker}")

    return index_text, changed


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Only check if README changed — used by GitHub Action
        pass

    readme = README.read_text(encoding='utf-8')
    html   = INDEX.read_text(encoding='utf-8')

    new_html, changed = sync(readme, html)

    if changed:
        INDEX.write_text(new_html, encoding='utf-8')
        print("✅ index.html synced from README.md")
    else:
        print("ℹ️  index.html already in sync")


if __name__ == "__main__":
    main()
