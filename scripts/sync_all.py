#!/usr/bin/env python3
"""
sync_all.py — Generate all display files from README.md (single source of truth).

Usage:
    python3 scripts/sync_all.py              # sync all files
    python3 scripts/sync_all.py --check      # check-only, exit 1 if dirty

Reads:  README.md, scripts/template.html
Writes: index.html, index_en.html, README_EN.md

Template markers: <!-- SYNC:name --> content <!-- /SYNC:name -->
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "template.html"


# ═══════════════════════════════════════════════
# Translation map (longest-match first)
# ═══════════════════════════════════════════════
T = [
    # ── Hero ──
    ("让每个说不清的情绪，都能被看见、被理解。",
     "Giving every unspoken emotion a shape that can be seen and understood."),
    ("产品经理 · Agent/Skill 开发 · 内容创作",
     "Product Manager · Agent/Skill Dev · Content Creation"),
    ("小红书", "Xiaohongshu"),

    # ── About Me ──
    ("开发 → 自动化测试 → 数据产品经理 → AI 创作者。",
     "Developer → QA Automation → Data PM → AI Creator."),
    ("这些年，我看过无数的代码和数据。最复杂的系统，都可以被建模、被呈现、被优化。",
     "I've spent years reading code and data. The most complex systems can all be modeled, rendered, and optimized."),
    ("但人的内心不行。",
     "But the human heart cannot."),
    ("那些堵在胸口、卡在喉咙、说又说不清的感受——没有接口、没有日志、没有任何调试工具能告诉你它卡在哪一行。",
     "Those feelings stuck in your chest, caught in your throat — indescribable, yet so real — have no API, no logs, no debugging tool to tell you where they're stuck."),
    ("所以现在的我，用了更多的时间去做这件事：",
     "So now, this is what I spend my time on:"),
    ("创作情绪插图、文案、和交互式数字体验。",
     "Creating emotional illustrations, copywriting, and interactive digital experiences."),
    ("把那些无形的、无名的、无处安放的情绪，",
     "Translating the formless, nameless, homeless emotions"),
    ("翻译成可以被看见、被触碰、被释放的形状。",
     "into shapes that can be seen, touched, and released."),
    ("让每一个说不清的情绪，都有一个具体的表达。",
     "Giving every unspoken emotion a concrete expression."),

    # ── Gallery ──
    ("🖱️ 左右滑动浏览更多 →", "🖱️ Scroll to explore →"),

    # ── HVL ──
    ("### ✦ 精选作品", "### ✦ Featured Works"),
    ("## 🌀 Healing Visual Lab · 视觉疗愈实验室", "## 🌀 Healing Visual Lab"),
    ("方向", "Category"),
    ("作品", "Work"),
    ("一句话", "In One Line"),
    ("粒子", "Particles"),
    ("流体", "Fluid"),
    ("音频", "Audio"),
    ("国风", "Shanshui"),
    ("像素", "Pixel"),
    ("墨池心境 / Inkmeditation", "Inkmeditation"),
    ("息流幻镜 / Breath Mirror", "Breath Mirror"),
    ("释·茧 / Unbound Mind", "Unbound Mind"),
    ("青绿层峦 / Layered Mountains", "Layered Mountains"),
    ("像素水族箱 / Pixel Aquarium", "Pixel Aquarium"),
    ("十万粒子如墨入水，随呼吸节律沉浮",
     "100K particles like ink in water, breathing with your rhythm"),
    ("摄像头将你的影像化为 GPU 流体雾面，呼吸即镜像",
     "Camera turns your reflection into GPU fluid fog — breathing is the mirror"),
    ("150K 粒子如茧被指尖抚开，432Hz 颂钵，4-7-8 呼吸循环",
     "150K particle cocoon dissolves under your fingertips, 432Hz singing bowl, 4-7-8 breathing"),
    ("250K 粒子堆叠青绿山水，触之即散，聚散随缘",
     "250K particles form layered Chinese landscape — touch scatters, time gathers"),
    ("像素小鱼在毛玻璃水箱游动，点击投食、双击敲玻璃",
     "6 pixel fish in a frosted glass tank — tap to feed, double-tap to knock"),
    ("探索全部作品 →", "Explore All Works →"),
    ("如果某件作品触动了你，⭐ Star 让更多人也能找到它。",
     "If a piece touched you, ⭐ Star helps others find it too."),

    # ── Skills ──
    ("## 🛠️ 能力光谱", "## 🛠️ Skills"),
    ("能力", "Skill"),
    ("说明", "Description"),
    ("🔀 系统化拆解", "🔀 Systematic Decomposition"),
    ("🤖 Agent & Skill 开发", "🤖 Agent & Skill Dev"),
    ("🎬 AI 内容创作", "🎬 AI Content Creation"),
    ("🎯 创作判断力", "🎯 Creative Judgment"),
    ("🧬 知识工程化", "🧬 Knowledge Engineering"),
    ("把混乱需求拆成闭环 —— 输入 → 判断 → 输出 → 反馈 → 迭代",
     "Breaking chaotic requirements into closed loops — input → judgment → output → feedback → iteration"),
    ("从规则定义到兜底逻辑，让 AI 真的能替人干活。不是写 prompt，是设计系统",
     "From rule definition to fallback logic, building AI that actually does the work. Not writing prompts — designing systems"),
    ("图文 · 视频 · 文案 · 应用。用什么工具不重要，能准确表达就行",
     "Images · Video · Copy · Apps. The tool doesn't matter — precise expression does"),
    ("知道什么内容能打动人，什么形式适合什么情绪，什么不值得做",
     "Knowing what resonates, what form suits what emotion, what's not worth making"),
    ("把个人经验变成结构化规则。系统越用越聪明，人不在了规则还在",
     "Turning personal experience into structured rules. The system gets smarter, and the rules outlast you"),

    # ── More Projects ──
    ("## 🎯 更多作品 @shasha1108", "## 🎯 More from @shasha1108"),
    ("仓库", "Repo"),
    ("简介", "About"),
    ("交互式数字疗愈作品集——15 件 Three.js/WebGL 交互实验",
     "Interactive digital healing experiments — 15 Three.js/WebGL works"),
    ("触觉驱动的交互式疗愈 H5 生成器——GPU 流体、WebGL 着色器",
     "Touch-driven healing H5 generator — GPU fluid, WebGL shaders"),
    ("像素艺术 × 毛玻璃美学——赛博养宠、电子水族箱",
     "Pixel art × Frutiger Aero — cyber pets, digital aquariums"),
    ("小红书情绪内容创作——隐喻挖掘、场景写作、视觉叙事",
     "Xiaohongshu emotional content creation — metaphor mining, scene writing, visual storytelling"),
    ("一键发布 H5 到 GitHub Pages——拖入文件夹即上线",
     "One-command H5 publishing to GitHub Pages — drop folder to live site"),

    # ── Footer ──
    ("网站源代码采用 MIT 协议", "MIT License"),
]


def tr(text: str) -> str:
    """Apply all translations, longest-match first."""
    for cn, en in T:
        text = text.replace(cn, en)
    return text


# ═══════════════════════════════════════════════
# Content extraction from README.md
# ═══════════════════════════════════════════════

def section(text: str, heading_kw: str) -> str:
    """Extract section between `## ... heading_kw ...` and next `##` or `---`."""
    pat = rf'##\s+[^\n]*{re.escape(heading_kw)}[^\n]*\n(.*?)(?=\n##\s|\n---\n|\n<div\s|\Z)'
    m = re.search(pat, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_block(text: str, start: str, end: str) -> str:
    """Extract text between start and end markers."""
    i = text.find(start)
    j = text.find(end, i + len(start)) if i >= 0 else -1
    return text[i + len(start):j].strip() if i >= 0 and j >= 0 else ""


def badges_html(readme: str) -> str:
    """Extract badge links as-is."""
    m = re.search(r'(<p>\s*\n(?:.*<img[^>]*/>\s*\n)*\s*</p>)', readme, re.DOTALL)
    return m.group(1).strip() if m else ""


def about_html(readme: str) -> str:
    """Build about section HTML."""
    sec = section(readme, "关于我")
    if not sec:
        return ""

    lines = sec.strip().split('\n')
    html = []

    # Career path (first line until period)
    career = lines[0].strip()
    html.append(f'<div class="career-path">{career}</div>')

    # Remaining paragraphs
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Collect paragraph
        para_lines = []
        while i < len(lines) and lines[i].strip():
            para_lines.append(lines[i].strip())
            i += 1
        para = ' '.join(para_lines)
        para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
        html.append(f'<p>{para}</p>')
        i += 1

    return '\n    '.join(html)


def gallery_header_html(readme: str) -> str:
    """Extract gallery header."""
    sec = section(readme, "画廊")
    m = re.search(r'<h3[^>]*>(.*?)</h3>', sec)
    if m:
        inner = m.group(1)
        return f'<p style="text-align:center;font-size:15px;color:#4493f8;letter-spacing:2px;font-weight:600;">{inner}</p>'
    return ""


def first_table(readme: str, heading_kw: str) -> str:
    """Extract first HTML table from a section."""
    sec = section(readme, heading_kw)
    m = re.search(r'(<table[^>]*>.*?</table>)', sec, re.DOTALL)
    return m.group(1).strip() if m else ""


def hvl_html(readme: str) -> str:
    """Build HVL section HTML: heading + table + button + close quote + star."""
    sec = section(readme, "Healing Visual Lab")
    if not sec:
        return ""

    table = first_table(readme, "Healing Visual Lab")
    btn = ""
    m = re.search(r'(<h3[^>]*>.*?</h3>)', sec)
    if m:
        btn = m.group(1).strip()

    # Closing quote + star (everything after button until end of section)
    rest = sec
    if btn:
        rest = sec[sec.find(btn) + len(btn):].strip()
    close_html = rest if rest else ""

    return f"""<h3>✦ 精选作品</h3>

    {table}

    {btn}

    {close_html}"""


def more_html(readme: str) -> str:
    """Build more projects HTML."""
    tbl = first_table(readme, "更多作品")
    return tbl if tbl else ""


def skills_html(readme: str) -> str:
    """Build skills HTML."""
    tbl = first_table(readme, "能力光谱")
    return tbl if tbl else ""


def footer_html(readme: str) -> str:
    """Extract footer line."""
    parts = readme.split('\n---\n')
    if len(parts) < 2:
        return ""
    last = parts[-1].strip()
    m = re.search(r'(<p[^>]*>.*?</p>)', last, re.DOTALL)
    return m.group(1).strip() if m else ""


# ═══════════════════════════════════════════════
# Build HTML from template
# ═══════════════════════════════════════════════

def build_html(readme_cn: str, lang: str) -> str:
    """Build complete HTML from README.md + template."""
    tpl = TEMPLATE.read_text(encoding='utf-8')

    def get(name, builder, *args):
        content = builder(readme_cn, *args) if args else builder(readme_cn)
        return tr(content) if lang == "en" else content

    # Extract all content blocks
    badges  = get("badges", badges_html)
    about   = get("about", about_html)
    gallery = get("gallery", gallery_header_html)
    hvl     = get("hvl", hvl_html)
    skills  = get("skills", skills_html)
    more    = get("more", more_html)
    footer  = get("footer", footer_html)

    # Apply content to template via SYNC markers
    replacements = {
        "badges": badges,
        "about": about,
        "gallery-header": gallery,
        "hvl": hvl,
        "skills": skills,
        "more": more,
        "footer": footer,
    }

    for name, content in replacements.items():
        start = f"<!-- SYNC:{name} -->"
        end   = f"<!-- /SYNC:{name} -->"
        if start in tpl and end in tpl:
            old = tpl[tpl.find(start):tpl.find(end) + len(end)]
            tpl = tpl.replace(old, f"{start}\n    {content}\n    {end}")
        else:
            print(f"  ⚠ marker not found: SYNC:{name}")

    # Language toggle
    if lang == "en":
        tpl = tpl.replace(
            '<a href="index_en.html" class="lang-toggle">EN</a>',
            '<a href="index.html" class="lang-toggle">中文</a>'
        )
        # Footer language link
        tpl = tpl.replace(
            '<a href="README_EN.md">English</a>',
            '<a href="README.md">中文</a>'
        )
    else:
        tpl = tpl.replace(
            '<a href="index_en.html" class="lang-toggle">EN</a>',
            '<a href="index_en.html" class="lang-toggle">EN</a>'
        )

    return tpl


# ═══════════════════════════════════════════════
# Generate README_EN.md
# ═══════════════════════════════════════════════

def build_en_readme(readme_cn: str) -> str:
    """Convert Chinese README to English."""
    en = readme_cn
    # Fix typing width for English
    en = en.replace(
        'width=750&pause=100000&lines=',
        'width=900&pause=100000&lines='
    )
    # Apply translations
    en = tr(en)
    # Language link
    en = en.replace('[English](README_EN.md)', '[中文](README.md)')
    # Clean license
    en = en.replace('| 网站源代码采用 MIT 协议', '')
    en = en.replace(' | 网站源代码采用 MIT 协议', '')
    return en


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════

def main():
    import sys
    check_only = "--check" in sys.argv

    readme_cn = (ROOT / "README.md").read_text(encoding='utf-8')

    files = {
        ROOT / "index.html": build_html(readme_cn, "cn"),
        ROOT / "index_en.html": build_html(readme_cn, "en"),
        ROOT / "README_EN.md": build_en_readme(readme_cn),
    }

    if check_only:
        dirty = False
        for path, content in files.items():
            if not path.exists():
                print(f"  ✗ {path.name} missing")
                dirty = True
            elif path.read_text(encoding='utf-8') != content:
                print(f"  ✗ {path.name} out of sync")
                dirty = True
            else:
                print(f"  ✓ {path.name}")
        if dirty:
            print("\nRun: python3 scripts/sync_all.py")
            sys.exit(1)
        return

    for path, content in files.items():
        path.write_text(content, encoding='utf-8')
        print(f"  ✓ {path.name}")

    print("\n✅ All files synced from README.md")


if __name__ == "__main__":
    main()
