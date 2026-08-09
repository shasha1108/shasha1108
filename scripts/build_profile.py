#!/usr/bin/env python3
"""Build the two profile READMEs and the two static profile pages from showcase.json."""

from __future__ import annotations

import argparse
import re
import sys
from html import escape
from pathlib import Path

from manage_showcase import ROOT, load_data, source_catalog, validate


TARGETS = {
    "README.md": "zh",
    "README_EN.md": "en",
    "index.html": "zh",
    "index_en.html": "en",
}


# GitHub derives these fragments from the corresponding Markdown headings.  Keep the
# rendered headings and the two top-of-README links in one explicit contract so a
# descriptive line below a heading cannot accidentally become its anchor again.
README_SECTION_CONTRACT = {
    "zh": {
        "gallery_heading": "01 / 画面档案",
        "gallery_fragment": "#01--画面档案",
        "flagship_heading": "02 / 三件旗舰",
        "flagship_fragment": "#02--三件旗舰",
    },
    "en": {
        "gallery_heading": "01 / Frame archive",
        "gallery_fragment": "#01--frame-archive",
        "flagship_heading": "02 / Three flagships",
        "flagship_fragment": "#02--three-flagships",
    },
}

UI = {
    "zh": {
        "lang": "zh-CN",
        "gallery_index": "01 / 画面档案",
        "gallery_title": "也许你从这些画面认识我。",
        "gallery_body": "21 张画面，按自己的速度经过。拖动这条长卷，或展开成完整网格；页面不会替你滚动，也不会替你解释。",
        "expand": "展开完整网格",
        "collapse": "收回长卷",
        "gallery_hint": "拖拽、触屏或用方向键移动；位置会被记住。",
        "gallery_alt": "画廊图像",
        "gallery_xhs": "小红书原帖",
        "gallery_work": "关联 H5",
        "flagship_index": "02 / 三件旗舰",
        "flagship_title": "不是展示页，是三种交互因果。",
        "flagship_body": "每件作品都要回答同一组问题：它接住什么、你必须做什么、系统如何判断、世界怎样回应、为什么只能这样交互。",
        "world_index": "03 / 会回应的小世界",
        "world_title": "可以占有，也可以回来。",
        "world_body": "它们不在主页里偷偷运行。只有在你点击进入时，才各自开始一段小小的天气。",
        "enter": "进入这件作品",
        "bench_index": "04 / 三张系统工作台",
        "bench_title": "系统只展示职责与脱敏流程。",
        "bench_body": "这些是私有工作台：公开的是工作如何被认真对待，不公开源码、客户资料或自动化捷径。",
        "private": "PRIVATE SYSTEM / NO SOURCE LINK",
        "members": "成员",
        "redacted_flow": "脱敏流程",
        "reject_index": "05 / 我拒绝自动化什么",
        "reject_title": "保留人的决定权。",
        "path_index": "06 / 个人路径与入口",
        "source_note": "作品事实来源：Healing Visual Lab 的本地只读快照（origin/main）。",
        "lightbox_close": "关闭画面",
        "open": "打开",
        "footer": "没有后台 iframe，没有自动播放的 H5；所有仪器都等一次明确的进入。",
        "readme_gallery": "静态横向识别画廊（与独立站同一配置、同一顺序）",
        "readme_flagship": "三件旗舰",
        "readme_worlds": "会回应的小世界",
        "readme_benches": "三张系统工作台",
        "readme_rejections": "我拒绝自动化什么",
        "readme_path": "个人路径与入口",
        "readme_source": "来源",
    },
    "en": {
        "lang": "en",
        "gallery_index": "01 / FRAME ARCHIVE",
        "gallery_title": "Perhaps these frames are how you come to know me.",
        "gallery_body": "Twenty-one frames, passed at your own pace. Drag the long reel or expand it into a full grid; the page will neither scroll nor explain for you.",
        "expand": "Expand full grid",
        "collapse": "Return to reel",
        "gallery_hint": "Drag, swipe, or use arrow keys; your position is remembered.",
        "gallery_alt": "Gallery image",
        "gallery_xhs": "Xiaohongshu post",
        "gallery_work": "Related H5",
        "flagship_index": "02 / THREE FLAGSHIPS",
        "flagship_title": "Not showpieces: three interaction causalities.",
        "flagship_body": "Each work answers the same five questions: what it holds, what you must do, how the system decides, how the world responds, and why it must work this way.",
        "world_index": "03 / RESPONSIVE SMALL WORLDS",
        "world_title": "Things to keep, and to return to.",
        "world_body": "They do not run secretly inside this homepage. Each begins a little weather system only after you choose to enter.",
        "enter": "Enter this work",
        "bench_index": "04 / THREE SYSTEM BENCHES",
        "bench_title": "Only roles and redacted flows are shown.",
        "bench_body": "These are private benches: public is the care in the work, not source code, client material, or an automation shortcut.",
        "private": "PRIVATE SYSTEM / NO SOURCE LINK",
        "members": "Members",
        "redacted_flow": "Redacted flow",
        "reject_index": "05 / WHAT I REFUSE TO AUTOMATE",
        "reject_title": "Keep decision-making human.",
        "path_index": "06 / PATH AND ENTRANCES",
        "source_note": "Work facts come from a local read-only Healing Visual Lab snapshot (origin/main).",
        "lightbox_close": "Close frame",
        "open": "Open",
        "footer": "No background iframes, no autoplaying H5: every instrument waits for an explicit entry.",
        "readme_gallery": "Static horizontal recognition gallery (same configuration and order as the site)",
        "readme_flagship": "Three flagships",
        "readme_worlds": "Responsive small worlds",
        "readme_benches": "Three system benches",
        "readme_rejections": "What I refuse to automate",
        "readme_path": "Path and entrances",
        "readme_source": "Source",
    },
}


SITE_CSS = r"""
:root {
  --paper: #f4efe4;
  --paper-deep: #e8decb;
  --ink: #1b1b18;
  --ink-soft: #4c4a43;
  --glass: #3d8892;
  --amber: #ae6d22;
  --moss: #4e6955;
  --signal: #a33a31;
  --rule: rgba(27, 27, 24, .22);
  --mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --serif: Iowan Old Style, Songti SC, STSong, Noto Serif CJK SC, Georgia, serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background:
    linear-gradient(90deg, transparent 0 49%, rgba(81, 70, 48, .025) 49% 51%, transparent 51%),
    var(--paper);
  font-family: var(--serif);
  line-height: 1.7;
}
button, a { font: inherit; }
a { color: inherit; }
a:focus-visible, button:focus-visible, [tabindex]:focus-visible { outline: 2px solid var(--signal); outline-offset: 4px; }
.page-shell { width: min(1180px, calc(100% - 36px)); margin: 0 auto; }
.topbar {
  display: flex; justify-content: space-between; align-items: center; gap: 18px;
  padding: 18px 0; border-bottom: 1px solid var(--rule);
}
.wordmark, .meta, .section-index, .instrument-code, .world-number, .bench-id, .private-tag {
  font-family: var(--mono); letter-spacing: .06em; text-transform: uppercase;
}
.wordmark { font-size: .78rem; text-decoration: none; }
.language-link { font-size: .82rem; text-underline-offset: .25em; }
.hero { min-height: 88vh; display: grid; grid-template-columns: minmax(0, 1fr) minmax(270px, .72fr); align-items: center; gap: clamp(36px, 7vw, 112px); padding: 62px 0 86px; }
.eyebrow, .section-index { margin: 0 0 18px; color: var(--moss); font-size: .73rem; }
.hero h1 { max-width: 760px; margin: 0; font-size: clamp(2.5rem, 6vw, 5.7rem); line-height: 1.05; font-weight: 500; letter-spacing: -.045em; }
.hero-role { margin: 17px 0 0; color: var(--signal); font: .74rem var(--mono); letter-spacing: .08em; text-transform: uppercase; }
.hero-copy { max-width: 600px; margin: 26px 0 0; color: var(--ink-soft); font-size: clamp(1rem, 1.6vw, 1.19rem); }
.core-positioning { max-width: 680px; margin: 24px 0 0; padding: 13px 0 13px 18px; border-left: 2px solid var(--glass); }
.core-positioning p { margin: 0; font-size: clamp(1rem, 1.55vw, 1.18rem); line-height: 1.55; }
.core-positioning p + p { margin-top: 5px; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 13px; margin-top: 32px; }
.action {
  display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 10px 16px;
  border: 1px solid var(--ink); text-decoration: none; transition: transform .2s ease, background .2s ease;
}
.action:hover { transform: translateY(-2px); }
.action-primary { background: var(--ink); color: var(--paper); }
.action-secondary { border-color: var(--glass); color: var(--glass); }
.jar-stage { position: relative; min-height: 405px; display: grid; place-items: center; }
.jar-stage::before { content: ""; position: absolute; width: 78%; height: 1px; background: var(--signal); transform: rotate(-12deg); }
.jar-svg { position: relative; width: min(100%, 390px); overflow: visible; }
.jar-label { position: absolute; right: 0; bottom: 20px; color: var(--signal); font: .68rem/1.4 var(--mono); letter-spacing: .07em; }
.section { position: relative; padding: clamp(72px, 9vw, 122px) 0; border-top: 1px solid var(--rule); }
.section-heading { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 28px; align-items: end; margin-bottom: 38px; }
.section-heading h2 { margin: 0; font-size: clamp(2rem, 4.4vw, 4rem); line-height: 1.06; font-weight: 500; letter-spacing: -.035em; }
.section-heading p:last-child { margin: 0; max-width: 590px; color: var(--ink-soft); }
.unspoken-line { position: relative; height: 27px; margin: 0 0 26px; color: var(--signal); }
.unspoken-line::before { content: ""; position: absolute; top: 14px; left: 0; width: 100%; height: 1px; background: currentColor; }
.unspoken-line span { position: absolute; top: 0; left: 0; padding-right: 9px; background: var(--paper); font: .64rem var(--mono); letter-spacing: .09em; }
.line-track { color: var(--glass); }
.line-track::after { content: ""; position: absolute; top: 10px; left: 29%; width: 9px; height: 9px; border: 1px solid currentColor; border-radius: 50%; background: var(--paper); }
.line-stem { color: var(--amber); }
.line-stem::before { transform: rotate(-1.2deg); transform-origin: left; }
.line-stem::after { content: ""; position: absolute; top: 5px; left: 57%; width: 10px; height: 10px; background: var(--moss); border-radius: 100% 0 100% 0; transform: rotate(25deg); }
.line-contour { color: var(--moss); }
.line-contour::before { height: 11px; border-top: 1px solid currentColor; border-bottom: 1px solid currentColor; background: transparent; }
.line-state { color: var(--signal); }
.line-state::after { content: "○—○—○"; position: absolute; top: 2px; right: 0; background: var(--paper); padding-left: 10px; font: .8rem var(--mono); }
.line-evidence { color: var(--amber); }
.line-evidence::after { content: "◇—◇—◇"; position: absolute; top: 2px; right: 0; background: var(--paper); padding-left: 10px; font: .8rem var(--mono); }
.gallery-controls { display: flex; justify-content: space-between; align-items: center; gap: 18px; margin: 0 0 15px; }
.gallery-controls p { margin: 0; color: var(--ink-soft); font-size: .9rem; }
.grid-toggle { appearance: none; border: 1px solid var(--ink); padding: 8px 12px; cursor: pointer; color: var(--ink); background: transparent; }
.gallery-rail { display: flex; gap: 18px; overflow-x: auto; padding: 8px 1px 22px; scroll-snap-type: x proximity; scrollbar-color: var(--moss) var(--paper-deep); touch-action: pan-y pinch-zoom; cursor: grab; }
.gallery-rail.is-dragging { cursor: grabbing; user-select: none; }
.gallery-rail::-webkit-scrollbar { height: 8px; }
.gallery-rail::-webkit-scrollbar-track { background: var(--paper-deep); }
.gallery-rail::-webkit-scrollbar-thumb { background: var(--moss); }
.gallery-frame { width: min(65vw, 274px); flex: 0 0 auto; margin: 0; scroll-snap-align: start; }
.gallery-open { display: block; width: 100%; padding: 0; border: 0; background: transparent; cursor: zoom-in; text-align: left; }
.gallery-open img { display: block; width: 100%; aspect-ratio: 3 / 4; object-fit: cover; border: 1px solid var(--ink); filter: saturate(.88); transition: filter .2s ease, transform .2s ease; }
.gallery-open:hover img { filter: saturate(1); transform: translateY(-3px); }
.gallery-frame figcaption { padding: 9px 2px 0; }
.gallery-frame strong { display: block; font-weight: 500; }
.gallery-frame small { display: block; color: var(--ink-soft); font-size: .78rem; line-height: 1.45; }
.gallery-rail.is-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(154px, 1fr)); overflow: visible; cursor: default; }
.gallery-rail.is-grid .gallery-frame { width: auto; }
.flagships { display: grid; gap: 68px; }
.flagship { display: grid; grid-template-columns: minmax(102px, .23fr) minmax(0, 1fr); gap: 28px; padding-bottom: 58px; border-bottom: 1px solid var(--rule); }
.flagship:last-child { border-bottom: 0; padding-bottom: 0; }
.instrument-code { color: var(--amber); font-size: .73rem; padding-top: 8px; }
.flagship h3 { margin: 0; font-size: clamp(1.8rem, 3.5vw, 3.2rem); line-height: 1.08; font-weight: 500; letter-spacing: -.03em; }
.flagship-tagline { margin: 14px 0 28px; color: var(--ink-soft); }
.five-parts { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); margin: 0; padding: 0; list-style: none; border-top: 1px solid var(--rule); }
.five-parts li { padding: 15px 13px 0 0; min-height: 180px; border-right: 1px solid var(--rule); }
.five-parts li + li { padding-left: 13px; }
.five-parts li:last-child { border-right: 0; }
.five-parts span { display: block; color: var(--signal); font: .64rem var(--mono); letter-spacing: .06em; }
.five-parts strong { display: block; margin: 10px 0; font-size: .9rem; font-weight: 600; }
.five-parts p { margin: 0; color: var(--ink-soft); font-size: .86rem; line-height: 1.55; }
.instrument-link { display: inline-block; margin-top: 23px; color: var(--glass); text-underline-offset: .24em; }
.responsive-list { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); grid-auto-flow: dense; gap: 1px; border-top: 1px solid var(--rule); background: var(--rule); }
.responsive-world { display: flex; flex-direction: column; grid-column: span 4; min-height: 280px; gap: 13px; padding: 24px; background: var(--paper); border: 0; }
.responsive-world.specimen-large { grid-column: span 7; min-height: 415px; padding: 33px; }
.responsive-world.specimen-tall { grid-column: span 5; min-height: 415px; padding: 30px; }
.responsive-world.specimen-wide { grid-column: span 8; min-height: 322px; padding: 30px; }
.responsive-world.specimen-compact { grid-column: span 4; min-height: 322px; }
.responsive-world.specimen-medium { grid-column: span 5; min-height: 348px; padding: 28px; }
.responsive-world.specimen-tall-right { grid-column: span 7; min-height: 348px; padding: 31px; }
.world-number { color: var(--moss); font-size: .72rem; }
.responsive-world h3 { margin: 0; font-size: clamp(1.35rem, 2.4vw, 2rem); font-weight: 500; line-height: 1.15; }
.responsive-world p { margin: 12px 0 0; color: var(--ink-soft); }
.world-spec { margin-top: auto; padding-top: 14px; border-top: 1px solid var(--rule); font-size: .91rem; }
.world-spec p { margin: 0 0 10px; }
.world-spec b { color: var(--glass); font-weight: 600; }
.benches { border-top: 1px solid var(--rule); }
.bench { display: grid; grid-template-columns: 72px minmax(0, .72fr) minmax(0, 1fr); gap: 22px; padding: 26px 0; border-bottom: 1px solid var(--rule); }
.bench-id { color: var(--amber); font-size: .75rem; }
.bench h3 { margin: 0; font-size: 1.25rem; font-weight: 500; }
.bench p { margin: 7px 0 0; color: var(--ink-soft); }
.bench-members { color: var(--moss) !important; font: .73rem/1.5 var(--mono); }
.private-tag { display: inline-block; margin-top: 12px; color: var(--signal); font-size: .63rem; }
.bench-flow { align-self: center; padding-left: 20px; border-left: 2px solid var(--moss); font: .76rem/1.6 var(--mono); color: var(--ink-soft); }
.rejection-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 38px; margin: 0; padding: 0; list-style: none; border-top: 1px solid var(--rule); }
.rejection-list li { padding: 19px 0; border-bottom: 1px solid var(--rule); }
.rejection-list span { display: inline-block; width: 30px; color: var(--signal); font: .69rem var(--mono); }
.path-section { padding-bottom: 70px; }
.path-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, .7fr); gap: 34px; }
.path-grid p { margin: 0; font-size: clamp(1.1rem, 2vw, 1.45rem); }
.entrances { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; }
.entrances a { color: var(--glass); text-underline-offset: .23em; }
.source-note { margin-top: 35px !important; color: var(--ink-soft); font-size: .78rem !important; }
.site-footer { border-top: 1px solid var(--rule); padding: 26px 0 40px; color: var(--ink-soft); font-size: .78rem; }
dialog { width: min(90vw, 720px); max-height: 92vh; padding: 16px; border: 1px solid var(--ink); background: var(--paper); color: var(--ink); }
dialog::backdrop { background: rgba(27, 27, 24, .62); }
.lightbox-close { display: block; margin-left: auto; border: 1px solid var(--ink); background: transparent; padding: 6px 10px; cursor: pointer; }
.lightbox-image { display: block; width: auto; max-width: 100%; max-height: 75vh; margin: 12px auto; }
.lightbox-caption { margin: 0; text-align: center; }
@media (max-width: 800px) {
  .hero, .section-heading, .path-grid { grid-template-columns: 1fr; }
  .hero { padding-top: 42px; min-height: auto; }
  .jar-stage { min-height: 280px; order: -1; }
  .jar-svg { width: min(75vw, 320px); }
  .five-parts { grid-template-columns: 1fr; }
  .five-parts li, .five-parts li + li { min-height: auto; padding: 16px 0; border-right: 0; border-bottom: 1px solid var(--rule); }
  .flagship, .bench { grid-template-columns: 1fr; gap: 11px; }
  .responsive-list { grid-template-columns: 1fr; }
  .responsive-world, .responsive-world.specimen-large, .responsive-world.specimen-tall, .responsive-world.specimen-wide, .responsive-world.specimen-compact, .responsive-world.specimen-medium, .responsive-world.specimen-tall-right { grid-column: 1; min-height: auto; padding: 24px; }
  .instrument-code, .world-number, .bench-id { padding-top: 0; }
  .bench-flow { padding: 12px 0 0; border-left: 0; border-top: 2px solid var(--moss); }
  .rejection-list { grid-template-columns: 1fr; }
  .section { padding: 70px 0; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; } }
"""


SITE_JS = r"""
(() => {
  const rail = document.getElementById("gallery-rail");
  const toggle = document.getElementById("gallery-grid-toggle");
  const dialog = document.getElementById("gallery-lightbox");
  const dialogImage = document.getElementById("lightbox-image");
  const dialogCaption = document.getElementById("lightbox-caption");
  const dialogClose = document.getElementById("lightbox-close");

  if (rail) {
    const storageKey = `shasha1108.gallery.position.${document.documentElement.lang}.v3`;
    try {
      const saved = Number(window.localStorage.getItem(storageKey));
      if (Number.isFinite(saved) && saved > 0) requestAnimationFrame(() => { rail.scrollLeft = saved; });
    } catch (_) {}

    let saveFrame = 0;
    rail.addEventListener("scroll", () => {
      cancelAnimationFrame(saveFrame);
      saveFrame = requestAnimationFrame(() => {
        try { window.localStorage.setItem(storageKey, String(Math.round(rail.scrollLeft))); } catch (_) {}
      });
    }, { passive: true });

    rail.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      rail.scrollBy({ left: event.key === "ArrowLeft" ? -Math.min(rail.clientWidth * .78, 430) : Math.min(rail.clientWidth * .78, 430), behavior: "smooth" });
    });

    let pointerId = null;
    let startX = 0;
    let startLeft = 0;
    let moved = false;
    let suppressClick = false;
    rail.addEventListener("pointerdown", (event) => {
      if (rail.classList.contains("is-grid") || event.pointerType === "mouse" && event.button !== 0) return;
      pointerId = event.pointerId;
      startX = event.clientX;
      startLeft = rail.scrollLeft;
      moved = false;
      rail.classList.add("is-dragging");
      rail.setPointerCapture(pointerId);
    });
    rail.addEventListener("pointermove", (event) => {
      if (pointerId !== event.pointerId) return;
      const delta = event.clientX - startX;
      if (Math.abs(delta) > 4) moved = true;
      if (moved) rail.scrollLeft = startLeft - delta;
    });
    const release = (event) => {
      if (pointerId !== event.pointerId) return;
      if (moved) {
        suppressClick = true;
        window.setTimeout(() => { suppressClick = false; }, 0);
      }
      if (rail.hasPointerCapture(pointerId)) rail.releasePointerCapture(pointerId);
      pointerId = null;
      rail.classList.remove("is-dragging");
    };
    rail.addEventListener("pointerup", release);
    rail.addEventListener("pointercancel", release);
    rail.addEventListener("click", (event) => {
      if (!suppressClick) return;
      event.preventDefault();
      event.stopPropagation();
    }, true);
  }

  if (toggle && rail) {
    toggle.addEventListener("click", () => {
      const expanded = rail.classList.toggle("is-grid");
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.textContent = expanded ? toggle.dataset.collapse : toggle.dataset.expand;
    });
  }

  document.querySelectorAll(".gallery-open").forEach((button) => {
    button.addEventListener("click", () => {
      if (!dialog || !dialogImage || !dialogCaption) return;
      dialogImage.src = button.dataset.full || "";
      dialogImage.alt = button.dataset.title || "";
      dialogCaption.textContent = button.dataset.title || "";
      dialog.showModal();
    });
  });
  if (dialogClose && dialog) dialogClose.addEventListener("click", () => dialog.close());
  if (dialog) dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
})();
"""


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def text_for(entry: dict, prefix: str, language: str) -> str:
    return str(entry[f"{prefix}_{language}"])


def work_data(snapshot: dict) -> dict[str, dict]:
    catalog = source_catalog(snapshot)
    detailed = {entry["slug"]: entry for entry in snapshot.get("works", []) if isinstance(entry, dict) and "slug" in entry}
    result: dict[str, dict] = {}
    for slug, item in catalog.items():
        merged = dict(item)
        merged.update(detailed.get(slug, {}))
        result[slug] = merged
    return result


def title_for(work: dict, language: str) -> str:
    return str(work[f"title_{language}"])


def entry_link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)} ↗</a>'


def gallery_items(config: dict) -> list[dict]:
    return [item for item in config["gallery"] if item["visible"]]


def render_readme(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    sections = README_SECTION_CONTRACT[language]
    identity = config["identity"]
    entrance = config["entrance"]
    path = config["path"]
    gallery = gallery_items(config)
    title = f"{text_for(identity, 'signature', language)} · {text_for(identity, 'site', language)}"
    lines = [
        f"# {title}",
        "",
        f"**{text_for(identity, 'role', language)}**",
        "",
        f"> {text_for(entrance, 'title', language)}",
        "",
        text_for(entrance, "body", language),
        "",
    ]
    lines.extend(f"> {statement}" for statement in entrance[f"core_positioning_{language}"])
    lines.extend([
        "",
        f"[{text_for(entrance, 'primary', language)}]({sections['flagship_fragment']}) · [{text_for(entrance, 'secondary', language)}]({sections['gallery_fragment']}) · [{esc(identity['language_switch_' + language])}]({'README_EN.md' if language == 'zh' else 'README.md'})",
        "",
        f"## {sections['gallery_heading']}",
        "",
        f"_{ui['readme_gallery']}_",
        "",
        "<table>",
        "<tr>",
    ])
    for item in gallery:
        title_text = text_for(item, "title", language)
        name = title_text or f"{ui['gallery_alt']} {item['id']}"
        lines.extend([
            f'<td align="center" data-gallery-id="{esc(item["id"])}">',
            f'<img src="{esc(item["webp_image"])}" width="154" alt="{esc(name)}"/>',
        ])
        if title_text:
            lines.append(f"<br/><sub>{esc(title_text)}</sub>")
        lines.append("</td>")
    lines.extend(["</tr>", "</table>", "", f"_{ui['source_note']}_", ""])

    lines.extend([f"## {sections['flagship_heading']}", ""])
    for work_config in config["flagship_works"]:
        work = works[work_config["slug"]]
        lines.extend([
            f"### [{title_for(work, language)}]({work['page_url']})",
            "",
        ])
        if language == "zh":
            lines.extend([f"> {work['tagline']}", ""])
        for index, part in enumerate(work_config["five_parts"][language], 1):
            lines.append(f"{index}. **{part['label']}** — {part['text']}")
        lines.extend(["", entry_link(work["page_url"], ui["open"]), ""])

    lines.extend([f"## 03 / {ui['readme_worlds']}", ""])
    for world_config in config["responsive_worlds"]:
        work = works[world_config["slug"]]
        lines.extend([
            f"### [{title_for(work, language)}]({work['page_url']})",
            "",
            text_for(world_config, "reason", language),
            "",
            text_for(world_config, "action", language),
            "",
            text_for(world_config, "response", language),
            "",
            entry_link(work["page_url"], ui["enter"]),
            "",
        ])

    lines.extend([f"## 04 / {ui['readme_benches']}", ""])
    for bench in config["workbenches"]:
        lines.extend([
            f"### {bench['id']} · {text_for(bench, 'name', language)}",
            "",
            f"**{ui['private']}**",
            "",
            f"**{ui['members']}** — {text_for(bench, 'members', language)}",
            "",
            text_for(bench, "role", language),
            "",
            f"**{ui['redacted_flow']}** — `{text_for(bench, 'flow', language)}`",
            "",
        ])

    lines.extend([f"## 05 / {ui['readme_rejections']}", ""])
    for rejection in config["rejections"]:
        lines.append(f"- {rejection[language]}")
    lines.extend(["", f"## 06 / {ui['readme_path']}", "", text_for(path, "body", language), ""])
    entrance_links = " · ".join(
        f"[{text_for(entry, 'label', language)}]({entry['url']})" for entry in path["entrances"]
    )
    lines.extend([
        entrance_links,
        "",
        f"<sub>{ui['footer']}</sub>",
        "",
    ])
    return "\n".join(lines)


def jar_svg() -> str:
    return """
<svg class="jar-svg" viewBox="0 0 460 560" role="img" aria-label="Bottled Cosmos">
  <defs>
    <linearGradient id="jar-glass" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#e1f3ee" stop-opacity=".82"/><stop offset=".5" stop-color="#70b5ba" stop-opacity=".35"/><stop offset="1" stop-color="#1b5260" stop-opacity=".5"/></linearGradient>
    <radialGradient id="jar-cosmos"><stop stop-color="#f5c66d"/><stop offset=".23" stop-color="#a55d91"/><stop offset=".64" stop-color="#28576a"/><stop offset="1" stop-color="#142833"/></radialGradient>
  </defs>
  <path d="M173 72h114l-11 53c0 18 70 23 83 75 19 75 26 237-10 299-26 45-78 69-119 69s-93-24-119-69c-36-62-29-224-10-299 13-52 83-57 83-75z" fill="url(#jar-glass)" stroke="#1b1b18" stroke-width="3"/>
  <path d="M159 74h142l-12-38H171z" fill="#ae6d22" stroke="#1b1b18" stroke-width="3"/>
  <ellipse cx="230" cy="316" rx="116" ry="164" fill="url(#jar-cosmos)" opacity=".91"/>
  <g fill="#f5efe4"><circle cx="183" cy="216" r="3"/><circle cx="260" cy="190" r="4"/><circle cx="299" cy="252" r="2"/><circle cx="161" cy="333" r="2"/><circle cx="269" cy="394" r="3"/><circle cx="202" cy="445" r="2"/></g>
  <path d="M149 168c-16 85-15 227 19 298" fill="none" stroke="#fff" stroke-opacity=".63" stroke-width="8" stroke-linecap="round"/>
  <path d="M212 273c20-22 42-4 24 17-19 22-45 12-27-17 17-26 58-11 62 20" fill="none" stroke="#f5c66d" stroke-width="2"/>
  <path d="M92 498h276" stroke="#a33a31" stroke-width="2"/>
</svg>
""".strip()


def render_gallery(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    frames = []
    for item in gallery_items(config):
        title = text_for(item, "title", language)
        description = text_for(item, "description", language)
        alt = title or f"{ui['gallery_alt']} {item['id']}"
        links = []
        if item["xhs_url"] is not None:
            links.append(f'<a class="instrument-link" href="{esc(item["xhs_url"])}" target="_blank" rel="noopener">{esc(ui["gallery_xhs"])} ↗</a>')
        if item["work_slug"] is not None:
            links.append(f'<a class="instrument-link" href="{esc(works[item["work_slug"]]["page_url"])}" target="_blank" rel="noopener">{esc(ui["gallery_work"])} ↗</a>')
        caption = ""
        if title or description or links:
            title_html = f"<strong>{esc(title)}</strong>" if title else ""
            description_html = f"<small>{esc(description)}</small>" if description else ""
            caption = f"<figcaption>{title_html}{description_html}{''.join(links)}</figcaption>"
        caption_line = f"\n  {caption}" if caption else ""
        frames.append(
            f'''<figure class="gallery-frame">
  <button class="gallery-open" type="button" data-gallery-id="{esc(item['id'])}" data-full="{esc(item['image'])}" data-title="{esc(alt)}">
    <img src="{esc(item['webp_image'])}" loading="lazy" decoding="async" width="376" height="500" alt="{esc(alt)}">
  </button>{caption_line}
</figure>'''
        )
    return "\n".join(frames)


def render_flagships(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    rendered = []
    for index, work_config in enumerate(config["flagship_works"], 1):
        work = works[work_config["slug"]]
        parts = "\n".join(
            f'''<li><span>{part_index:02d}</span><strong>{esc(part['label'])}</strong><p>{esc(part['text'])}</p></li>'''
            for part_index, part in enumerate(work_config["five_parts"][language], 1)
        )
        tagline = f'<p class="flagship-tagline">{esc(work["tagline"])}</p>' if language == "zh" else ""
        tagline_line = f"\n    {tagline}" if tagline else ""
        rendered.append(
            f'''<article class="flagship">
  <div class="instrument-code">{index:02d} / instrument</div>
  <div>
    <h3>{esc(title_for(work, language))}</h3>{tagline_line}
    <ol class="five-parts">{parts}</ol>
    <a class="instrument-link" href="{esc(work['page_url'])}" target="_blank" rel="noopener">{esc(ui['open'])} ↗</a>
  </div>
</article>'''
        )
    return "\n".join(rendered)


def render_worlds(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    automatic_sizes = ("large", "tall", "wide", "compact", "medium", "tall-right")
    rendered = []
    for index, world in enumerate(config["responsive_worlds"], 1):
        work = works[world["slug"]]
        specimen_size = world.get("specimen_size")
        if specimen_size == "auto" or specimen_size is None:
            specimen_size = automatic_sizes[(index - 1) % len(automatic_sizes)]
        rendered.append(
            f'''<article class="responsive-world specimen-{esc(specimen_size)}">
  <div class="world-number">{index:02d}</div>
  <div>
    <h3>{esc(title_for(work, language))}</h3>
    <p>{esc(text_for(world, 'reason', language))}</p>
    <a class="instrument-link" href="{esc(work['page_url'])}" target="_blank" rel="noopener">{esc(ui['enter'])} ↗</a>
  </div>
  <div class="world-spec">
    <p><b>{esc(text_for(world, 'action', language).split('：')[0] if language == 'zh' else 'Primary gesture')}</b><br>{esc(text_for(world, 'action', language))}</p>
    <p><b>{esc(text_for(world, 'response', language).split('：')[0] if language == 'zh' else 'Response')}</b><br>{esc(text_for(world, 'response', language))}</p>
  </div>
</article>'''
        )
    return "\n".join(rendered)


def render_benches(config: dict, language: str) -> str:
    ui = UI[language]
    return "\n".join(
        f'''<article class="bench">
  <div class="bench-id">{esc(bench['id'])}</div>
  <div><h3>{esc(text_for(bench, 'name', language))}</h3><p class="bench-members">{esc(ui['members'])} / {esc(text_for(bench, 'members', language))}</p><p>{esc(text_for(bench, 'role', language))}</p><span class="private-tag">{esc(ui['private'])}</span></div>
  <div class="bench-flow">{esc(ui['redacted_flow'])}<br>{esc(text_for(bench, 'flow', language))}</div>
</article>'''
        for bench in config["workbenches"]
    )


def render_rejections(config: dict, language: str) -> str:
    return "\n".join(
        f'<li><span>{index:02d}</span>{esc(rejection[language])}</li>'
        for index, rejection in enumerate(config["rejections"], 1)
    )


def render_site(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    identity = config["identity"]
    entrance = config["entrance"]
    path = config["path"]
    switch_file = "index_en.html" if language == "zh" else "index.html"
    title = f"{text_for(identity, 'signature', language)} · {text_for(identity, 'site', language)}"
    entrance_links = "".join(
        f'<a href="{esc(entry["url"])}" target="_blank" rel="noopener">{esc(text_for(entry, "label", language))} ↗</a>'
        for entry in path["entrances"]
    )
    return f'''<!doctype html>
<html lang="{ui['lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(text_for(entrance, 'body', language))}">
  <meta name="theme-color" content="#f4efe4">
  <title>{esc(title)}</title>
  <style>{SITE_CSS}</style>
</head>
<body>
  <div class="page-shell">
    <header class="topbar">
      <a class="wordmark" href="#entrance">{esc(text_for(identity, 'signature', language))} / {esc(text_for(identity, 'site', language))}</a>
      <a class="language-link" href="{switch_file}" lang="{'en' if language == 'zh' else 'zh-CN'}">{esc(identity['language_switch_' + language])}</a>
    </header>
    <main>
      <section class="hero" id="entrance">
        <div>
          <p class="eyebrow">{esc(text_for(entrance, 'eyebrow', language))}</p>
          <h1>{esc(text_for(entrance, 'title', language))}</h1>
          <p class="hero-role">{esc(text_for(identity, 'role', language))}</p>
          <p class="hero-copy">{esc(text_for(entrance, 'body', language))}</p>
          <div class="core-positioning">{''.join(f'<p>{esc(statement)}</p>' for statement in entrance[f'core_positioning_{language}'])}</div>
          <div class="hero-actions">
            <a class="action action-primary" href="#flagship-works">{esc(text_for(entrance, 'primary', language))}</a>
            <a class="action action-secondary" href="#gallery">{esc(text_for(entrance, 'secondary', language))}</a>
          </div>
        </div>
        <div class="jar-stage">{jar_svg()}<span class="jar-label">BOTTLED COSMOS / 30 SEC</span></div>
      </section>

      <section class="section gallery-section" id="gallery">
        <div class="unspoken-line line-track"><span>UNNAMED LINE / TRACK</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['gallery_index'])}</p><h2>{esc(ui['gallery_title'])}</h2></div><p>{esc(ui['gallery_body'])}</p></div>
        <div class="gallery-controls"><p>{esc(ui['gallery_hint'])}</p><button class="grid-toggle" id="gallery-grid-toggle" type="button" aria-expanded="false" data-expand="{esc(ui['expand'])}" data-collapse="{esc(ui['collapse'])}">{esc(ui['expand'])}</button></div>
        <div class="gallery-rail" id="gallery-rail" tabindex="0" aria-label="{esc(ui['gallery_title'])}">
          {render_gallery(config, works, language)}
        </div>
      </section>

      <section class="section" id="flagship-works">
        <div class="unspoken-line line-stem"><span>UNNAMED LINE / STEM</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['flagship_index'])}</p><h2>{esc(ui['flagship_title'])}</h2></div><p>{esc(ui['flagship_body'])}</p></div>
        <div class="flagships">{render_flagships(config, works, language)}</div>
      </section>

      <section class="section" id="responsive-worlds">
        <div class="unspoken-line line-contour"><span>UNNAMED LINE / CONTOUR</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['world_index'])}</p><h2>{esc(ui['world_title'])}</h2></div><p>{esc(ui['world_body'])}</p></div>
        <div class="responsive-list">{render_worlds(config, works, language)}</div>
      </section>

      <section class="section" id="system-benches">
        <div class="unspoken-line line-state"><span>UNNAMED LINE / STATE MACHINE</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['bench_index'])}</p><h2>{esc(ui['bench_title'])}</h2></div><p>{esc(ui['bench_body'])}</p></div>
        <div class="benches">{render_benches(config, language)}</div>
      </section>

      <section class="section" id="rejections">
        <div class="unspoken-line line-evidence"><span>UNNAMED LINE / EVIDENCE CHAIN</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['reject_index'])}</p><h2>{esc(ui['reject_title'])}</h2></div></div>
        <ol class="rejection-list">{render_rejections(config, language)}</ol>
      </section>

      <section class="section path-section" id="path">
        <div class="unspoken-line"><span>UNNAMED LINE / OPEN EXIT</span></div>
        <div class="section-heading"><div><p class="section-index">{esc(ui['path_index'])}</p><h2>{esc(text_for(path, 'title', language))}</h2></div></div>
        <div class="path-grid"><p>{esc(text_for(path, 'body', language))}</p><div class="entrances">{entrance_links}</div></div>
        <p class="source-note">{esc(ui['source_note'])}</p>
      </section>
    </main>
    <footer class="site-footer">{esc(ui['footer'])}</footer>
  </div>
  <dialog id="gallery-lightbox" aria-labelledby="lightbox-caption"><button class="lightbox-close" id="lightbox-close" type="button">{esc(ui['lightbox_close'])}</button><img class="lightbox-image" id="lightbox-image" alt=""><p class="lightbox-caption" id="lightbox-caption"></p></dialog>
  <script>{SITE_JS}</script>
</body>
</html>
'''


def validate_rendered(outputs: dict[str, str], config: dict) -> None:
    expected_gallery = [item["id"] for item in gallery_items(config)]
    for filename, content in outputs.items():
        found_gallery = re.findall(r'data-gallery-id="([^"]+)"', content)
        if found_gallery != expected_gallery:
            raise ValueError(f"{filename} does not preserve the configured gallery order")
        if filename.endswith(".html"):
            ids = re.findall(r'\bid="([^"]+)"', content)
            duplicated = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
            if duplicated:
                raise ValueError(f"{filename} has duplicate DOM id(s): {', '.join(duplicated)}")
            if "<iframe" in content.lower() or "<canvas" in content.lower():
                raise ValueError(f"{filename} must not preload H5 via iframe or canvas")
    for filename, language in (("README.md", "zh"), ("README_EN.md", "en")):
        content = outputs[filename]
        sections = README_SECTION_CONTRACT[language]
        entrance = config["entrance"]
        expected_nav = (
            f"[{text_for(entrance, 'primary', language)}]({sections['flagship_fragment']}) · "
            f"[{text_for(entrance, 'secondary', language)}]({sections['gallery_fragment']})"
        )
        if expected_nav not in content:
            raise ValueError(f"{filename} top navigation does not match its section-anchor contract")
        for section in ("gallery", "flagship"):
            heading = f"## {sections[f'{section}_heading']}"
            if heading not in content:
                raise ValueError(f"{filename} is missing its {section} heading for the anchor contract")


def build_outputs() -> dict[str, str]:
    config, snapshot = load_data()
    errors = validate(config, snapshot)
    if errors:
        raise ValueError("\n".join(errors))
    works = work_data(snapshot)
    outputs = {
        "README.md": render_readme(config, works, "zh"),
        "README_EN.md": render_readme(config, works, "en"),
        "index.html": render_site(config, works, "zh"),
        "index_en.html": render_site(config, works, "en"),
    }
    validate_rendered(outputs, config)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Living Instrument Room profile outputs.")
    parser.add_argument("--check", action="store_true", help="verify generated files match the configuration without writing")
    args = parser.parse_args()
    try:
        outputs = build_outputs()
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    drift = []
    for filename, expected in outputs.items():
        path = ROOT / filename
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            drift.append(filename)
            if not args.check:
                path.write_text(expected, encoding="utf-8")

    if args.check:
        if drift:
            print("profile build check: DRIFT " + ", ".join(drift), file=sys.stderr)
            return 1
        print("profile build check: OK (README.md, README_EN.md, index.html, index_en.html)")
        return 0

    changed = ", ".join(drift) if drift else "none"
    print(f"profile build: OK (updated: {changed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
