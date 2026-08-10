#!/usr/bin/env python3
"""Build the bilingual profile READMEs and static pages from showcase.json."""

from __future__ import annotations

import argparse
import re
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from manage_showcase import ROOT, load_data, source_catalog, validate


UI = {
    "zh": {
        "lang": "zh-CN",
        "about": "关于我",
        "about_title": "从代码走到感受",
        "about_lead": "这些年，我看过无数代码和数据。复杂的系统可以被建模、被呈现、被调试——但人的内心不行。",
        "about_end": "我不替你定义感受，也不让自动化替创作者做最后的决定。技术只是把这些微小体验做出来的方法。",
        "gallery_kicker": "一段视觉记忆",
        "gallery_title": "也许你从这些画面认识我。",
        "gallery_body": "它们记录了我反复回到的颜色、光线和情绪。你可以慢慢拖动这条长卷，也可以展开来看完整画廊。",
        "gallery_hint": "拖动、触屏滑动或使用方向键",
        "expand": "展开画廊",
        "collapse": "收起画廊",
        "gallery_alt": "云野自由的画面",
        "gallery_xhs": "小红书原帖",
        "gallery_work": "进入关联作品",
        "featured_kicker": "三个可以走进去的瞬间",
        "featured_title": "我把这些感受，做成了小世界。",
        "featured_body": "不是为了替你解释，而是让一次触碰、一段停留，真的改变眼前的世界。",
        "open_work": "进入作品",
        "worlds_kicker": "会记得被触碰的小世界",
        "worlds_title": "它们安静地活着，也等你回来。",
        "worlds_body": "每一件都有自己的天气、呼吸和回应。打开它们时，作品才真正开始。",
        "behind_kicker": "作品背后",
        "behind_title": "让细腻的体验可靠地发生。",
        "behind_body": "我的技术工作不站在作品前面。它负责让交互成立、让创作流程可靠，也让每一个判断经得起验证。",
        "members": "相关项目",
        "path_kicker": "走到这里",
        "links_title": "继续看看",
        "lightbox_close": "关闭",
        "readme_worlds": "它们安静地活着，也等你回来",
        "readme_behind": "如果你也关心这些体验是怎样发生的",
        "closing": "如果其中某件作品让你感到被看见——那就是这些代码存在的全部意义。",
    },
    "en": {
        "lang": "en",
        "about": "About",
        "about_title": "From code toward feeling",
        "about_lead": "I have spent years with code and data. Complex systems can be modelled, visualised, and debugged—but an inner life cannot.",
        "about_end": "I do not define a feeling for you, or let automation make a creator's final decision. Technology is simply how these small experiences become possible.",
        "gallery_kicker": "A visual memory",
        "gallery_title": "Perhaps these are the images through which you know me.",
        "gallery_body": "They hold the colours, light, and feelings I return to. Move through the long reel slowly, or open the complete gallery.",
        "gallery_hint": "Drag, swipe, or use the arrow keys",
        "expand": "Open the gallery",
        "collapse": "Close the gallery",
        "gallery_alt": "An image by Yunye Ziyou",
        "gallery_xhs": "Xiaohongshu post",
        "gallery_work": "Enter related work",
        "featured_kicker": "Three moments you can enter",
        "featured_title": "I turn these feelings into small worlds.",
        "featured_body": "They do not explain a feeling for you. A touch or a pause changes the world in front of you.",
        "open_work": "Enter the work",
        "worlds_kicker": "Small worlds that remember touch",
        "worlds_title": "They live quietly, and wait for your return.",
        "worlds_body": "Each has its own weather, breath, and response. The work begins only when you open it.",
        "behind_kicker": "Behind the work",
        "behind_title": "Making delicate experiences happen reliably.",
        "behind_body": "My technical work stays behind the experience. It makes interaction meaningful, creative workflows reliable, and judgment accountable.",
        "members": "Related projects",
        "path_kicker": "How I arrived here",
        "links_title": "Keep exploring",
        "lightbox_close": "Close",
        "readme_worlds": "They live quietly, and wait for your return",
        "readme_behind": "If you also wonder how these experiences are made",
        "closing": "If one of these pieces made you feel seen—that is the only reason this code exists.",
    },
}


SITE_CSS = r"""
:root {
  --night: #173b5a;
  --ink: #274a63;
  --soft-ink: #56758a;
  --water: #dff7fb;
  --sky: #edfaff;
  --foam: #fbffff;
  --cyan: #69cbd5;
  --leaf: #63ad96;
  --sunset: #f1ad82;
  --lavender: #9faee5;
  --line: rgba(39, 74, 99, .14);
  --shadow: 0 24px 70px rgba(41, 105, 137, .16);
  --serif: Iowan Old Style, Songti SC, STSong, Noto Serif CJK SC, Georgia, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at 9% 8%, rgba(255,255,255,.96) 0 5%, transparent 23%),
    radial-gradient(circle at 86% 19%, rgba(112,218,223,.24), transparent 28%),
    linear-gradient(180deg, #e9faff 0%, #f9ffff 32%, #eef9f6 72%, #f7fbff 100%);
  font: 16px/1.75 var(--sans);
  overflow-x: hidden;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: .34;
  background-image: radial-gradient(rgba(50,109,140,.16) .7px, transparent .7px);
  background-size: 17px 17px;
  mask-image: linear-gradient(to bottom, #000, transparent 70%);
}
a { color: inherit; }
button, a { font: inherit; }
a:focus-visible, button:focus-visible, [tabindex]:focus-visible { outline: 3px solid var(--sunset); outline-offset: 4px; }
.ambient-fish { position: fixed; inset: 0; z-index: 0; width: 100%; height: 100%; pointer-events: none; opacity: .72; }
.shell { position: relative; z-index: 1; width: min(1120px, calc(100% - 38px)); margin: 0 auto; }
.topbar {
  position: relative; z-index: 10; display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 24px 0; color: var(--night); font-size: .9rem;
}
.signature { font-family: var(--serif); font-size: 1.08rem; font-weight: 600; text-decoration: none; letter-spacing: .02em; }
.topnav { display: flex; align-items: center; gap: 20px; }
.topnav a { text-decoration: none; border-bottom: 1px solid transparent; }
.topnav a:hover { border-color: currentColor; }
.hero {
  position: relative; min-height: min(690px, calc(100vh - 72px)); display: grid; grid-template-columns: minmax(0, .94fr) minmax(370px, .76fr);
  align-items: center; gap: clamp(32px, 6vw, 84px); padding: 30px 0 66px;
}
.hero-copy { position: relative; z-index: 2; }
.eyebrow, .kicker { margin: 0 0 17px; color: var(--leaf); font-size: .78rem; font-weight: 650; letter-spacing: .13em; text-transform: uppercase; }
.hero h1 {
  max-width: 660px; min-height: 2.65em; margin: 0; color: #3a8a7a;
  font: 600 clamp(1.8rem, 2.65vw, 2.65rem)/1.32 "Cascadia Code", "PingFang SC", "Microsoft YaHei", sans-serif;
  letter-spacing: .01em; text-shadow: 0 4px 14px rgba(58,138,122,.12);
}
.typing-text.is-typing::after { content: "_"; display: inline-block; margin-left: .08em; color: #5aaccc; animation: caretBlink .8s steps(1) infinite; }
.hero-intro { max-width: 590px; margin: 20px 0 0; color: var(--soft-ink); font-size: clamp(.98rem, 1.35vw, 1.12rem); }
.role { margin: 16px 0 0; color: var(--ink); font-size: .82rem; letter-spacing: .04em; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 13px; margin-top: 24px; }
.button {
  display: inline-flex; align-items: center; justify-content: center; min-height: 48px; padding: 10px 18px;
  border: 1px solid rgba(39,74,99,.38); border-radius: 999px; text-decoration: none; transition: .25s ease;
}
.button.primary { color: #fff; border-color: var(--night); background: var(--night); box-shadow: 0 12px 30px rgba(23,59,90,.2); }
.button:hover { transform: translateY(-3px); box-shadow: 0 16px 36px rgba(41,105,137,.18); }
.memory-orbit { position: relative; min-height: 500px; }
.memory-orbit::before, .memory-orbit::after {
  content: ""; position: absolute; border-radius: 50%; border: 1px solid rgba(255,255,255,.9);
  background: radial-gradient(circle at 28% 24%, #fff 0 8%, rgba(211,249,251,.68) 25%, rgba(104,203,213,.12) 63%, rgba(255,255,255,.45));
  box-shadow: inset -12px -14px 28px rgba(62,161,183,.12), 0 18px 40px rgba(78,166,194,.12); backdrop-filter: blur(2px);
}
.memory-orbit::before { width: 118px; height: 118px; top: 16px; right: -8px; animation: float 8s ease-in-out infinite; }
.memory-orbit::after { width: 66px; height: 66px; left: -26px; bottom: 45px; animation: float 6s ease-in-out infinite reverse; }
.memory-frame {
  position: absolute; margin: 0; overflow: hidden; border: 8px solid rgba(255,255,255,.72); border-radius: 30px;
  background: #dff5f8; box-shadow: var(--shadow); transform: rotate(var(--tilt));
}
.memory-frame img { display: block; width: 100%; height: 100%; object-fit: cover; }
.memory-main { --tilt: 2.2deg; width: 72%; height: 395px; top: 55px; right: 0; }
.memory-left { --tilt: -7deg; width: 45%; height: 235px; left: 0; bottom: 3px; }
.memory-small { --tilt: 7deg; width: 34%; height: 170px; left: 18px; top: 7px; }
.section { position: relative; padding: clamp(82px, 10vw, 138px) 0; }
.section-head { max-width: 760px; margin-bottom: 42px; }
.section h2 { margin: 0; color: var(--night); font: 500 clamp(1.9rem, 3.6vw, 3.15rem)/1.2 var(--serif); letter-spacing: -.025em; }
.section-intro { max-width: 650px; margin: 20px 0 0; color: var(--soft-ink); font-size: 1.05rem; }
.gallery-section::before {
  content: ""; position: absolute; inset: 8% -10% 3%; z-index: -1; transform: rotate(-1deg);
  border-radius: 48% 52% 44% 56%; background: rgba(255,255,255,.52); box-shadow: inset 0 0 70px rgba(122,211,218,.11);
}
.gallery-controls { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 18px; color: var(--soft-ink); font-size: .88rem; }
.gallery-controls p { margin: 0; }
.gallery-toggle { border: 0; border-bottom: 1px solid currentColor; padding: 3px 0; color: var(--ink); background: transparent; cursor: pointer; }
.gallery-rail { display: flex; gap: 22px; overflow-x: auto; padding: 12px 5px 28px; scroll-snap-type: x proximity; scrollbar-width: thin; scrollbar-color: var(--cyan) transparent; cursor: grab; touch-action: pan-y pinch-zoom; }
.gallery-rail.is-dragging { cursor: grabbing; user-select: none; }
.gallery-frame { flex: 0 0 auto; width: min(67vw, 270px); margin: 0; scroll-snap-align: start; }
.gallery-open { display: block; width: 100%; padding: 0; border: 0; border-radius: 24px; background: transparent; cursor: zoom-in; }
.gallery-open img { display: block; width: 100%; aspect-ratio: 3/4; object-fit: cover; border: 7px solid rgba(255,255,255,.7); border-radius: 24px; box-shadow: 0 15px 42px rgba(49,117,148,.14); transition: transform .28s ease, box-shadow .28s ease; }
.gallery-open:hover img { transform: translateY(-7px) rotate(-.5deg); box-shadow: 0 22px 55px rgba(49,117,148,.22); }
.gallery-frame figcaption { padding: 10px 6px 0; color: var(--soft-ink); font-size: .83rem; }
.gallery-frame strong, .gallery-frame small { display: block; }
.gallery-frame a { display: inline-block; margin: 5px 12px 0 0; text-underline-offset: .2em; }
.gallery-rail.is-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); overflow: visible; cursor: default; }
.gallery-rail.is-grid .gallery-frame { width: auto; }
.featured-section { padding-top: 110px; }
.featured-list { display: grid; gap: 40px; }
.featured-work {
  display: grid; grid-template-columns: minmax(300px, .9fr) minmax(0, 1.1fr); overflow: hidden;
  border-radius: 38px; background: rgba(255,255,255,.64); box-shadow: 0 22px 70px rgba(43,111,143,.12);
}
.featured-work:nth-child(even) .featured-preview { order: 2; }
.featured-preview { position: relative; min-height: 390px; overflow: hidden; background: linear-gradient(145deg, #bceaf1, #324e70); }
.featured-preview img { width: 100%; height: 100%; object-fit: cover; }
.featured-content { display: flex; flex-direction: column; justify-content: center; padding: clamp(34px, 6vw, 70px); }
.featured-number { color: var(--leaf); font-size: .75rem; letter-spacing: .13em; }
.featured-content h3 { margin: 14px 0 0; color: var(--night); font: 500 clamp(2rem, 4vw, 3.65rem)/1.12 var(--serif); }
.featured-content p { margin: 22px 0 0; color: var(--soft-ink); font-size: 1.05rem; }
.text-link { display: inline-flex; align-items: center; gap: 8px; align-self: flex-start; margin-top: 26px; color: var(--night); text-decoration: none; border-bottom: 1px solid rgba(23,59,90,.4); }
.text-link::after { content: "↗"; transition: transform .2s ease; }
.text-link:hover::after { transform: translate(3px,-3px); }
.worlds-section::before { content: ""; position: absolute; inset: 7% -10%; z-index: -1; background: radial-gradient(ellipse at center, rgba(161,225,211,.24), transparent 68%); }
.world-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 18px; }
.small-world { position: relative; display: flex; flex-direction: column; min-height: 300px; grid-column: span 4; padding: 30px; overflow: hidden; border: 1px solid rgba(255,255,255,.78); border-radius: 32px; text-decoration: none; box-shadow: 0 16px 50px rgba(62,126,148,.09); transition: .28s ease; }
.small-world:nth-child(1), .small-world:nth-child(6) { grid-column: span 7; }
.small-world:nth-child(2), .small-world:nth-child(5) { grid-column: span 5; }
.small-world:nth-child(1) { background: linear-gradient(145deg, rgba(195,241,249,.92), rgba(111,190,213,.56)); }
.small-world:nth-child(2) { background: linear-gradient(145deg, rgba(221,246,226,.94), rgba(117,183,151,.48)); }
.small-world:nth-child(3) { background: linear-gradient(145deg, rgba(255,242,209,.94), rgba(239,176,104,.43)); }
.small-world:nth-child(4) { background: linear-gradient(145deg, rgba(228,230,255,.94), rgba(144,165,219,.46)); }
.small-world:nth-child(5) { background: linear-gradient(145deg, rgba(207,242,239,.94), rgba(101,177,166,.48)); }
.small-world:nth-child(6) { background: linear-gradient(145deg, rgba(214,233,250,.94), rgba(157,165,221,.44)); }
.small-world::after { content: ""; position: absolute; width: 150px; height: 150px; right: -42px; top: -42px; border: 1px solid rgba(255,255,255,.72); border-radius: 50%; box-shadow: inset -18px -18px 30px rgba(57,122,148,.08); }
.small-world:hover { transform: translateY(-6px); box-shadow: 0 24px 60px rgba(62,126,148,.16); }
.world-index { color: rgba(39,74,99,.65); font-size: .74rem; letter-spacing: .12em; }
.small-world h3 { max-width: 560px; margin: auto 0 0; color: var(--night); font: 500 clamp(1.65rem, 3vw, 2.7rem)/1.18 var(--serif); }
.small-world p { max-width: 600px; margin: 17px 0 0; color: rgba(39,74,99,.8); }
.world-arrow { margin-top: 22px; font-size: 1.25rem; }
.about-section { padding-top: 100px; }
.about-wrap { display: grid; grid-template-columns: minmax(250px, .72fr) minmax(0, 1.28fr); gap: clamp(40px, 8vw, 100px); align-items: center; }
.about-image { position: relative; margin: 0; }
.about-image img { display: block; width: 100%; aspect-ratio: 3/4; object-fit: cover; border: 9px solid rgba(255,255,255,.72); border-radius: 42% 42% 32px 32px; box-shadow: var(--shadow); }
.about-image::after { content: ""; position: absolute; width: 90px; height: 90px; right: -24px; bottom: -28px; border-radius: 50%; background: rgba(105,203,213,.25); border: 1px solid rgba(255,255,255,.8); }
.about-copy h2 { max-width: 620px; }
.about-lead { margin: 28px 0 0; color: var(--night); font: 500 clamp(1.25rem, 2.3vw, 1.7rem)/1.6 var(--serif); }
.story { margin-top: 26px; }
.story p { margin: 0; color: var(--soft-ink); }
.story p + p { margin-top: 13px; }
.about-end { margin-top: 28px; padding-left: 20px; border-left: 2px solid var(--sunset); color: var(--ink); }
.behind-section { padding-top: 85px; }
.behind-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.behind-item { padding: 28px 0; border-top: 1px solid rgba(39,74,99,.28); }
.behind-item h3 { margin: 0; color: var(--night); font: 500 1.55rem/1.3 var(--serif); }
.behind-item p { margin: 16px 0 0; color: var(--soft-ink); }
.behind-members { display: block; margin-top: 20px; color: rgba(86,117,138,.8); font-size: .73rem; line-height: 1.55; word-break: break-word; }
.closing-section { padding: 100px 0 70px; }
.closing-card { padding: clamp(38px, 7vw, 74px); border-radius: 42px; color: #fff; background: linear-gradient(135deg, #24557a, #4e91a0 58%, #6aac98); box-shadow: var(--shadow); }
.closing-card h2 { color: #fff; }
.path-copy { max-width: 800px; margin: 20px 0 0; color: rgba(255,255,255,.8); }
.entrances { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 32px; }
.entrances a { padding: 9px 15px; border: 1px solid rgba(255,255,255,.44); border-radius: 999px; color: #fff; text-decoration: none; }
.entrances a:hover { background: rgba(255,255,255,.12); }
.site-footer { padding: 0 0 48px; color: var(--soft-ink); text-align: center; font-family: var(--serif); }
dialog { width: min(92vw, 760px); max-height: 92vh; padding: 14px; border: 0; border-radius: 28px; color: var(--ink); background: var(--foam); box-shadow: var(--shadow); }
dialog::backdrop { background: rgba(18,49,72,.72); backdrop-filter: blur(7px); }
.lightbox-close { display: block; margin-left: auto; border: 0; padding: 7px 10px; color: var(--ink); background: transparent; cursor: pointer; }
.lightbox-image { display: block; width: auto; max-width: 100%; max-height: 76vh; margin: 4px auto 12px; border-radius: 18px; }
.lightbox-caption { margin: 0; text-align: center; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-18px); } }
@keyframes caretBlink { 0%,45% { opacity: 1; } 46%,100% { opacity: 0; } }
@media (max-width: 820px) {
  .topnav a:not(.language-link) { display: none; }
  .hero { min-height: auto; grid-template-columns: 1fr; padding: 45px 0 80px; }
  .hero h1 { min-height: 0; font-size: clamp(1.8rem, 7.5vw, 2.65rem); }
  .memory-orbit { min-height: 500px; }
  .memory-main { height: 410px; }
  .memory-left { height: 235px; }
  .memory-small { height: 175px; }
  .featured-work { grid-template-columns: 1fr; }
  .featured-work:nth-child(even) .featured-preview { order: 0; }
  .featured-preview { min-height: 330px; }
  .world-grid { grid-template-columns: 1fr; }
  .small-world, .small-world:nth-child(1), .small-world:nth-child(2), .small-world:nth-child(5), .small-world:nth-child(6) { grid-column: 1; min-height: 280px; }
  .about-wrap, .behind-grid { grid-template-columns: 1fr; }
  .about-image { width: min(76vw, 420px); }
}
@media (max-width: 520px) {
  .shell { width: min(100% - 26px, 1120px); }
  .topbar { padding-top: 17px; }
  .hero { padding-top: 22px; }
  .memory-orbit { min-height: 420px; }
  .memory-main { width: 74%; height: 330px; top: 50px; }
  .memory-left { width: 45%; height: 190px; }
  .memory-small { height: 145px; }
  .section { padding: 82px 0; }
  .featured-preview { min-height: 290px; }
  .featured-content, .small-world { padding: 28px; }
  .gallery-frame { width: 72vw; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
"""


SITE_JS = r"""
(() => {
  const typing = document.querySelector('[data-typewriter]');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typing && !reduceMotion) {
    const full = typing.dataset.typewriter || typing.textContent || '';
    typing.textContent = '';
    typing.classList.add('is-typing');
    let index = 0;
    const typeNext = () => {
      index += 1;
      typing.textContent = full.slice(0, index);
      if (index < full.length) window.setTimeout(typeNext, index < 5 ? 125 : 78);
      else window.setTimeout(() => typing.classList.remove('is-typing'), 900);
    };
    window.setTimeout(typeNext, 360);
  }

  const fishCanvas = document.getElementById('ambient-fish');
  if (fishCanvas) {
    const ctx = fishCanvas.getContext('2d');
    const palettes = [
      { type: 'angel', g1: '#6fc7bd', g2: '#9cb9dc', fin: 'rgba(112, 190, 190, .46)', size: 1.72 },
      { type: 'disk', g1: '#9aaed8', g2: '#d4b8dc', fin: 'rgba(157, 174, 216, .42)', size: 1.48 },
      { type: 'goldfish', g1: '#e5b493', g2: '#83c8bd', fin: 'rgba(216, 171, 142, .43)', size: 1.62 },
      { type: 'angel', g1: '#82c9d4', g2: '#b5b4df', fin: 'rgba(118, 190, 204, .4)', size: 1.28 },
      { type: 'disk', g1: '#77b9ae', g2: '#e1c49f', fin: 'rgba(112, 177, 164, .39)', size: 1.36 },
      { type: 'goldfish', g1: '#a6b8df', g2: '#74c6c3', fin: 'rgba(145, 164, 214, .38)', size: 1.22 },
    ];
    const fish = palettes.map((palette, index) => ({
      ...palette,
      x: innerWidth * (.08 + index * .17),
      y: innerHeight * (.18 + ((index * 29) % 61) / 100),
      vx: (index % 2 ? -1 : 1) * (.18 + index * .025),
      phase: index * 1.13,
      drift: 13 + index * 3,
      opacity: .48 + (index % 3) * .09,
    }));
    let width = 0, height = 0, dpr = 1, last = performance.now();
    let pointerX = -1000, pointerY = -1000;
    const resizeFish = () => {
      width = innerWidth; height = innerHeight; dpr = Math.min(devicePixelRatio || 1, 2);
      fishCanvas.width = Math.round(width * dpr); fishCanvas.height = Math.round(height * dpr);
      fishCanvas.style.width = `${width}px`; fishCanvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const drawFish = (item, time) => {
      ctx.save();
      ctx.translate(item.x, item.y);
      if (item.vx < 0) ctx.scale(-1, 1);
      ctx.globalAlpha = item.opacity;
      const s = item.size;
      const tailSway = Math.sin(time * .006 + item.phase) * 5;
      const body = ctx.createLinearGradient(0, -12 * s, 0, 12 * s);
      body.addColorStop(0, item.g1); body.addColorStop(.52, item.g2); body.addColorStop(1, '#dff7f6');
      ctx.fillStyle = item.fin;
      if (item.type === 'angel') {
        ctx.beginPath(); ctx.moveTo(-5*s,-8*s); ctx.quadraticCurveTo(-15*s,-38*s+tailSway,-2*s,-12*s); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-5*s,8*s); ctx.quadraticCurveTo(-15*s,38*s+tailSway,-2*s,12*s); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-15*s,0); ctx.quadraticCurveTo(-32*s,-20*s+tailSway,-28*s,tailSway); ctx.quadraticCurveTo(-32*s,20*s+tailSway,-15*s,0); ctx.fill();
        ctx.fillStyle = body; ctx.beginPath(); ctx.ellipse(0,0,16*s,12*s,0,0,Math.PI*2); ctx.fill();
      } else if (item.type === 'goldfish') {
        ctx.beginPath(); ctx.moveTo(-10*s,0); ctx.bezierCurveTo(-25*s,-24*s+tailSway,-36*s,-12*s+tailSway,-26*s,5*s+tailSway); ctx.bezierCurveTo(-36*s,22*s+tailSway,-22*s,26*s+tailSway,-10*s,0); ctx.fill();
        ctx.fillStyle = body; ctx.beginPath(); ctx.ellipse(0,0,15*s,11*s,0,0,Math.PI*2); ctx.fill();
      } else {
        ctx.beginPath(); ctx.moveTo(-12*s,0); ctx.lineTo(-25*s,-14*s+tailSway); ctx.lineTo(-20*s,tailSway); ctx.lineTo(-25*s,14*s+tailSway); ctx.closePath(); ctx.fill();
        ctx.fillStyle = body; ctx.beginPath(); ctx.ellipse(0,0,16*s,15*s,0,0,Math.PI*2); ctx.fill();
      }
      ctx.fillStyle = 'rgba(255,255,255,.86)'; ctx.beginPath(); ctx.arc(8*s,-3*s,3.2*s,0,Math.PI*2); ctx.fill();
      ctx.fillStyle = 'rgba(35,78,102,.82)'; ctx.beginPath(); ctx.arc(9.3*s,-3*s,1.55*s,0,Math.PI*2); ctx.fill();
      ctx.restore();
    };
    const frameFish = (now) => {
      const delta = Math.min(34, now - last); last = now; ctx.clearRect(0, 0, width, height);
      fish.forEach((item) => {
        const dx = item.x - pointerX, dy = item.y - pointerY;
        if (dx*dx + dy*dy < 19000) item.vx += Math.sign(dx || 1) * .012;
        item.vx *= .998; item.vx = Math.max(-.42, Math.min(.42, item.vx));
        item.x += item.vx * delta;
        item.y += Math.sin(now * .00055 + item.phase) * .055 * delta;
        if (item.x > width + 70) item.x = -70;
        if (item.x < -70) item.x = width + 70;
        item.y = Math.max(55, Math.min(height - 55, item.y));
        drawFish(item, now);
      });
      if (!reduceMotion) requestAnimationFrame(frameFish);
    };
    window.addEventListener('resize', resizeFish);
    window.addEventListener('pointermove', (event) => { pointerX = event.clientX; pointerY = event.clientY; }, { passive: true });
    resizeFish(); requestAnimationFrame(frameFish);
  }

  const rail = document.getElementById("gallery-rail");
  const toggle = document.getElementById("gallery-toggle");
  const dialog = document.getElementById("gallery-lightbox");
  const image = document.getElementById("lightbox-image");
  const caption = document.getElementById("lightbox-caption");
  const close = document.getElementById("lightbox-close");

  if (rail) {
    const key = `shasha1108.gallery.${document.documentElement.lang}.v4`;
    try {
      const saved = Number(localStorage.getItem(key));
      if (Number.isFinite(saved) && saved > 0) requestAnimationFrame(() => { rail.scrollLeft = saved; });
    } catch (_) {}
    let frame = 0;
    rail.addEventListener("scroll", () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => { try { localStorage.setItem(key, String(Math.round(rail.scrollLeft))); } catch (_) {} });
    }, { passive: true });
    rail.addEventListener("keydown", (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      rail.scrollBy({ left: event.key === 'ArrowLeft' ? -380 : 380, behavior: 'smooth' });
    });
    let pointer = null, startX = 0, startLeft = 0, moved = false, suppress = false;
    rail.addEventListener("pointerdown", (event) => {
      if (rail.classList.contains('is-grid') || (event.pointerType === 'mouse' && event.button !== 0)) return;
      pointer = event.pointerId; startX = event.clientX; startLeft = rail.scrollLeft; moved = false;
      rail.classList.add('is-dragging'); rail.setPointerCapture(pointer);
    });
    rail.addEventListener("pointermove", (event) => {
      if (event.pointerId !== pointer) return;
      const delta = event.clientX - startX; if (Math.abs(delta) > 4) moved = true;
      if (moved) rail.scrollLeft = startLeft - delta;
    });
    const release = (event) => {
      if (event.pointerId !== pointer) return;
      if (moved) { suppress = true; setTimeout(() => { suppress = false; }, 0); }
      if (rail.hasPointerCapture(pointer)) rail.releasePointerCapture(pointer);
      pointer = null; rail.classList.remove('is-dragging');
    };
    rail.addEventListener('pointerup', release); rail.addEventListener('pointercancel', release);
    rail.addEventListener('click', (event) => { if (suppress) { event.preventDefault(); event.stopPropagation(); } }, true);
  }
  if (toggle && rail) toggle.addEventListener('click', () => {
    const expanded = rail.classList.toggle('is-grid');
    toggle.setAttribute('aria-expanded', String(expanded));
    toggle.textContent = expanded ? toggle.dataset.collapse : toggle.dataset.expand;
  });
  document.querySelectorAll('.gallery-open').forEach((button) => button.addEventListener('click', () => {
    if (!dialog || !image || !caption) return;
    image.src = button.dataset.full || ''; image.alt = button.dataset.title || ''; caption.textContent = button.dataset.title || '';
    dialog.showModal();
  }));
  if (close && dialog) close.addEventListener('click', () => dialog.close());
  if (dialog) dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
})();
"""


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def text_for(entry: dict, prefix: str, language: str) -> str:
    return str(entry[f"{prefix}_{language}"])


def work_data(snapshot: dict) -> dict[str, dict]:
    catalog = source_catalog(snapshot)
    details = {work["slug"]: work for work in snapshot.get("works", []) if isinstance(work, dict) and "slug" in work}
    return {slug: {**item, **details.get(slug, {})} for slug, item in catalog.items()}


def title_for(work: dict, language: str) -> str:
    return str(work[f"title_{language}"])


def gallery_items(config: dict) -> list[dict]:
    return [item for item in config["gallery"] if item["visible"]]


def typing_svg_url(text: str, *, size: int, color: str, width: int, weight: int | None = None) -> str:
    params = {
        "font": "Cascadia Code",
        "size": size,
        "color": color,
        "center": "true",
        "vCenter": "true",
        "width": width,
        "pause": 100000,
        "lines": text,
    }
    if weight is not None:
        params["weight"] = weight
    return "https://readme-typing-svg.herokuapp.com?" + urlencode(params)


def render_readme(config: dict, works: dict[str, dict], language: str) -> str:
    ui, identity, entrance, path = UI[language], config["identity"], config["entrance"], config["path"]
    gallery = gallery_items(config)
    profile_site = "https://shasha1108.github.io/shasha1108/index.html"
    profile_site_label = "个人主页" if language == "zh" else "Personal site"
    language_url = (
        "https://github.com/shasha1108/shasha1108/blob/main/README_EN.md"
        if language == "zh"
        else "https://github.com/shasha1108/shasha1108/blob/main/README.md"
    )
    language_label = "English" if language == "zh" else "中文"
    headline = text_for(entrance, "title", language)
    role = text_for(identity, "role", language)
    lines = [
        "<!-- Generated from content/showcase.json by scripts/build_profile.py. Do not edit this file directly. -->",
        "",
        '<div align="center">',
        f'<img src="{esc(typing_svg_url(headline, size=20, color="C4A46C", width=750, weight=600))}" alt="{esc(headline)}"/>',
        '',
        f'<img src="{esc(typing_svg_url(role, size=15, color="8B9DC3", width=700))}" alt="{esc(role)}"/>',
        f'<p>{esc(text_for(entrance, "body", language))}</p>',
        f'<p><a href="{esc(identity["xhs_url"])}">小红书 / Xiaohongshu</a> · <a href="{esc(identity["lab_url"])}">Healing Visual Lab</a> · <a href="{profile_site}">{profile_site_label}</a></p>',
        '</div>', '',
        '<table><tr>',
    ]
    for item in gallery[:3]:
        lines.append(f'<td width="33%"><img src="{esc(item["webp_image"])}" width="100%" alt="{esc(ui["gallery_alt"])}"/></td>')
    lines.extend(['</tr></table>', '', f'## 🫧 {ui["about"]}', '', ui["about_lead"], ''])
    for paragraph in entrance[f"core_positioning_{language}"]:
        lines.extend([paragraph, ''])
    lines.extend([ui["about_end"], '', f'## {ui["gallery_title"]}', '', ui["gallery_body"], '', '<h3 align="center">🖱️ 左右滑动浏览更多 →</h3>' if language == 'zh' else '<h3 align="center">🖱️ Scroll sideways to see more →</h3>', '', '<pre style="background:transparent;border:none;font:inherit;padding:8px 0;margin:0;overflow-x:auto;">'])
    lines.append(''.join(
        f'<img data-gallery-id="{esc(item["id"])}" src="{esc(item["webp_image"])}" width="290" alt="{esc(text_for(item, "title", language) or ui["gallery_alt"])}"/>'
        for item in gallery
    ))
    lines.extend(['</pre>', '', f'## {ui["featured_title"]}', '', ui["featured_body"], '', '<table><tr>'])
    for item in config["flagship_works"]:
        work = works[item["slug"]]
        image = item["preview_image"]
        lines.extend([
            '<td width="33%" valign="top">',
            f'<a href="{esc(work["page_url"])}"><img src="{esc(image)}" width="100%" alt="{esc(title_for(work, language))}"/></a><br/>',
            f'<strong>{esc(title_for(work, language))}</strong><br/>',
            f'<sub>{esc(text_for(item, "note", language))}</sub><br/><br/>',
            f'<a href="{esc(work["page_url"])}">{esc(ui["open_work"])} ↗</a>',
            '</td>',
        ])
    lines.extend(['</tr></table>', '', f'## {ui["readme_worlds"]}', ''])
    for item in config["responsive_worlds"]:
        work = works[item["slug"]]
        note = work.get("tagline") if language == "zh" else text_for(item, "reason", language)
        lines.extend([f'### [{esc(title_for(work, language))}]({esc(work["page_url"])})', '', str(note), ''])
    lines.extend([f'<details><summary><strong>{esc(ui["readme_behind"])}</strong></summary>', ''])
    for bench in config["workbenches"]:
        lines.extend([f'### {esc(text_for(bench, "name", language))}', '', text_for(bench, "role", language), '', f'<sub>{esc(text_for(bench, "members", language))}</sub>', ''])
    lines.extend(['</details>', '', f'## {esc(text_for(path, "title", language))}', '', esc(text_for(path, "body", language)), ''])
    lines.extend([
        '<div align="center">',
        f'<h3><a href="{language_url}">{language_label} →</a></h3>',
        '</div>',
    ])
    lines.extend(['', '---', '', f'<div align="center"><em>{esc(ui["closing"])}</em><br/><br/>{esc(text_for(identity, "signature", language))}</div>', ''])
    return "\n".join(lines)


def render_gallery(config: dict, works: dict[str, dict], language: str) -> str:
    ui, frames = UI[language], []
    for item in gallery_items(config):
        title, description = text_for(item, "title", language), text_for(item, "description", language)
        alt = title or f'{ui["gallery_alt"]} {item["id"]}'
        links = []
        if item["xhs_url"]:
            links.append(f'<a href="{esc(item["xhs_url"])}" target="_blank" rel="noopener">{esc(ui["gallery_xhs"])} ↗</a>')
        if item["work_slug"]:
            links.append(f'<a href="{esc(works[item["work_slug"]]["page_url"])}" target="_blank" rel="noopener">{esc(ui["gallery_work"])} ↗</a>')
        caption = ''
        if title or description or links:
            caption = f'<figcaption>{f"<strong>{esc(title)}</strong>" if title else ""}{f"<small>{esc(description)}</small>" if description else ""}{"".join(links)}</figcaption>'
        frames.append(f'''<figure class="gallery-frame">
  <button class="gallery-open" type="button" data-gallery-id="{esc(item['id'])}" data-full="{esc(item['image'])}" data-title="{esc(alt)}">
    <img src="{esc(item['webp_image'])}" loading="lazy" decoding="async" width="376" height="500" alt="{esc(alt)}">
  </button>{caption}
</figure>''')
    return "\n".join(frames)


def render_featured(config: dict, works: dict[str, dict], language: str) -> str:
    ui = UI[language]
    result = []
    for index, item in enumerate(config["flagship_works"], 1):
        work = works[item["slug"]]
        image = item["preview_image"]
        result.append(f'''<article class="featured-work">
  <a class="featured-preview" href="{esc(work['page_url'])}" target="_blank" rel="noopener"><img src="{esc(image)}" loading="lazy" alt="{esc(title_for(work, language))}"></a>
  <div class="featured-content"><span class="featured-number">0{index}</span><h3>{esc(title_for(work, language))}</h3><p>{esc(text_for(item, 'note', language))}</p><a class="text-link" href="{esc(work['page_url'])}" target="_blank" rel="noopener">{esc(ui['open_work'])}</a></div>
</article>''')
    return "\n".join(result)


def render_worlds(config: dict, works: dict[str, dict], language: str) -> str:
    result = []
    for index, item in enumerate(config["responsive_worlds"], 1):
        work = works[item["slug"]]
        note = work.get("tagline") if language == "zh" else text_for(item, "reason", language)
        result.append(f'''<a class="small-world" href="{esc(work['page_url'])}" target="_blank" rel="noopener">
  <span class="world-index">0{index}</span><h3>{esc(title_for(work, language))}</h3><p>{esc(note)}</p><span class="world-arrow" aria-hidden="true">↗</span>
</a>''')
    return "\n".join(result)


def render_behind(config: dict, language: str) -> str:
    ui = UI[language]
    return "\n".join(
        f'''<article class="behind-item"><h3>{esc(text_for(item, 'name', language))}</h3><p>{esc(text_for(item, 'role', language))}</p><small class="behind-members">{esc(ui['members'])}<br>{esc(text_for(item, 'members', language))}</small></article>'''
        for item in config["workbenches"]
    )


def render_site(config: dict, works: dict[str, dict], language: str) -> str:
    ui, identity, entrance, path = UI[language], config["identity"], config["entrance"], config["path"]
    gallery = gallery_items(config)
    switch_file = "index_en.html" if language == "zh" else "index.html"
    links = "".join(f'<a href="{esc(item["url"])}" target="_blank" rel="noopener">{esc(text_for(item, "label", language))}</a>' for item in path["entrances"])
    story = "".join(f'<p>{esc(paragraph)}</p>' for paragraph in entrance[f"core_positioning_{language}"])
    return f'''<!-- Generated from content/showcase.json by scripts/build_profile.py. Do not edit this file directly. -->
<!doctype html>
<html lang="{ui['lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(text_for(entrance, 'body', language))}">
  <meta name="theme-color" content="#e9faff">
  <title>{esc(text_for(identity, 'signature', language))} · {esc(text_for(entrance, 'title', language))}</title>
  <style>{SITE_CSS}</style>
</head>
<body>
  <canvas class="ambient-fish" id="ambient-fish" aria-hidden="true"></canvas>
  <div class="shell">
    <header class="topbar">
      <a class="signature" href="#top">{esc(text_for(identity, 'signature', language))}</a>
      <nav class="topnav" aria-label="Primary"><a href="#gallery">{esc(ui['gallery_kicker'])}</a><a href="#worlds">{esc(ui['worlds_kicker'])}</a><a href="#about">{esc(ui['about'])}</a><a class="language-link" href="{switch_file}">{esc(identity['language_switch_' + language])}</a></nav>
    </header>
    <main>
      <section class="hero" id="top">
        <div class="hero-copy"><p class="eyebrow">{esc(text_for(entrance, 'eyebrow', language))}</p><h1 aria-label="{esc(text_for(entrance, 'title', language))}"><span class="typing-text" data-typewriter="{esc(text_for(entrance, 'title', language))}" aria-hidden="true">{esc(text_for(entrance, 'title', language))}</span></h1><p class="hero-intro">{esc(text_for(entrance, 'body', language))}</p><p class="role">{esc(text_for(identity, 'role', language))}</p><div class="hero-actions"><a class="button primary" href="#gallery">{esc(text_for(entrance, 'primary', language))}</a><a class="button" href="#worlds">{esc(text_for(entrance, 'secondary', language))}</a></div></div>
        <div class="memory-orbit" aria-label="{esc(ui['gallery_title'])}">
          <figure class="memory-frame memory-main"><img src="{esc(gallery[0]['webp_image'])}" alt="{esc(ui['gallery_alt'])}"></figure>
          <figure class="memory-frame memory-left"><img src="{esc(gallery[1]['webp_image'])}" alt="{esc(ui['gallery_alt'])}"></figure>
          <figure class="memory-frame memory-small"><img src="{esc(gallery[2]['webp_image'])}" alt="{esc(ui['gallery_alt'])}"></figure>
        </div>
      </section>

      <section class="section gallery-section" id="gallery">
        <header class="section-head"><p class="kicker">{esc(ui['gallery_kicker'])}</p><h2>{esc(ui['gallery_title'])}</h2><p class="section-intro">{esc(ui['gallery_body'])}</p></header>
        <div class="gallery-controls"><p>{esc(ui['gallery_hint'])}</p><button class="gallery-toggle" id="gallery-toggle" type="button" aria-expanded="false" data-expand="{esc(ui['expand'])}" data-collapse="{esc(ui['collapse'])}">{esc(ui['expand'])}</button></div>
        <div class="gallery-rail" id="gallery-rail" tabindex="0" aria-label="{esc(ui['gallery_title'])}">{render_gallery(config, works, language)}</div>
      </section>

      <section class="section featured-section" id="featured">
        <header class="section-head"><p class="kicker">{esc(ui['featured_kicker'])}</p><h2>{esc(ui['featured_title'])}</h2><p class="section-intro">{esc(ui['featured_body'])}</p></header>
        <div class="featured-list">{render_featured(config, works, language)}</div>
      </section>

      <section class="section worlds-section" id="worlds">
        <header class="section-head"><p class="kicker">{esc(ui['worlds_kicker'])}</p><h2>{esc(ui['worlds_title'])}</h2><p class="section-intro">{esc(ui['worlds_body'])}</p></header>
        <div class="world-grid">{render_worlds(config, works, language)}</div>
      </section>

      <section class="section about-section" id="about">
        <div class="about-wrap"><figure class="about-image"><img src="{esc(gallery[2]['webp_image'])}" loading="lazy" alt="{esc(ui['gallery_alt'])}"></figure><div class="about-copy"><p class="kicker">{esc(ui['about'])}</p><h2>{esc(ui['about_title'])}</h2><p class="about-lead">{esc(ui['about_lead'])}</p><div class="story">{story}</div><p class="about-end">{esc(ui['about_end'])}</p></div></div>
      </section>

      <section class="section behind-section" id="behind">
        <header class="section-head"><p class="kicker">{esc(ui['behind_kicker'])}</p><h2>{esc(ui['behind_title'])}</h2><p class="section-intro">{esc(ui['behind_body'])}</p></header>
        <div class="behind-grid">{render_behind(config, language)}</div>
      </section>

      <section class="closing-section" id="path"><div class="closing-card"><p class="kicker">{esc(ui['path_kicker'])}</p><h2>{esc(text_for(path, 'title', language))}</h2><p class="path-copy">{esc(text_for(path, 'body', language))}</p><div class="entrances" aria-label="{esc(ui['links_title'])}">{links}</div></div></section>
    </main>
    <footer class="site-footer">{esc(ui['closing'])}<br>{esc(text_for(identity, 'signature', language))}</footer>
  </div>
  <dialog id="gallery-lightbox" aria-labelledby="lightbox-caption"><button class="lightbox-close" id="lightbox-close" type="button">{esc(ui['lightbox_close'])}</button><img class="lightbox-image" id="lightbox-image" alt=""><p class="lightbox-caption" id="lightbox-caption"></p></dialog>
  <script>{SITE_JS}</script>
</body>
</html>
'''


def validate_rendered(outputs: dict[str, str], config: dict) -> None:
    gallery = [item["id"] for item in gallery_items(config)]
    headline_zh = config["entrance"]["title_zh"]
    banned = ("活体仪器室", "标本抽屉", "系统如何判断", "PRIVATE SYSTEM", "UNNAMED LINE")
    for filename, content in outputs.items():
        if re.findall(r'data-gallery-id="([^"]+)"', content) != gallery:
            raise ValueError(f"{filename} does not preserve the configured gallery order")
        if any(term in content for term in banned):
            raise ValueError(f"{filename} still contains retired public-facing terminology")
        if filename in ("README.md", "index.html") and headline_zh not in content:
            raise ValueError(f"{filename} is missing the personal emotional statement")
        if filename.endswith(".html"):
            ids = re.findall(r'\bid="([^"]+)"', content)
            duplicates = sorted({item for item in ids if ids.count(item) > 1})
            if duplicates:
                raise ValueError(f"{filename} has duplicate DOM ids: {', '.join(duplicates)}")
            if "<iframe" in content.lower():
                raise ValueError(f"{filename} must not preload interactive works")
            canvas_ids = re.findall(r'<canvas[^>]+id="([^"]+)"', content)
            if canvas_ids != ["ambient-fish"]:
                raise ValueError(f"{filename} may only contain the decorative ambient-fish canvas")


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
    parser = argparse.ArgumentParser(description="Build the Sha.w.z bilingual profile outputs.")
    parser.add_argument("--check", action="store_true", help="verify generated files match showcase.json")
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
    print(f"profile build: OK (updated: {', '.join(drift) if drift else 'none'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
