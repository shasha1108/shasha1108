#!/usr/bin/env python3
"""Maintain the configuration-backed profile showcase without a CMS.

Usage:
  python3 scripts/manage_showcase.py list
  python3 scripts/manage_showcase.py set-responsive <slug...>
  python3 scripts/manage_showcase.py reorder-gallery <id...>
  python3 scripts/manage_showcase.py check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "content" / "showcase.json"
FLAGSHIP_ORDER = ["eternal-bloom", "bottled-cosmos", "layered-mountains"]
RESPONSIVE_MIN = 3
RESPONSIVE_MAX = 12
SPECIMEN_SIZES = {"large", "tall", "wide", "compact", "medium", "tall-right", "auto"}
FIVE_PARTS_ZH = ["它接住什么", "用户必须做什么", "系统如何判断", "世界怎样回应", "为什么只能这样交互"]
FIVE_PARTS_EN = [
    "What it holds",
    "What the visitor must do",
    "How the system decides",
    "How the world responds",
    "Why this interaction must be this way",
]
REQUIRED_SIGNATURE_ZH = "Sha.w.z / 云野自由"
REQUIRED_SIGNATURE_EN = "Sha.w.z / 云野自由 (Yunye Ziyou)"
REQUIRED_ROLE_ZH = "产品经理 · AI Agent 与 Skill 开发 · 数字内容创作"
REQUIRED_ROLE_EN = "Product · AI Agent & Skill Development · Digital Content Creation"
REQUIRED_TITLE_ZH = "让每个说不清的情绪，都能被看见、被理解。"
REQUIRED_TITLE_EN = "Let every feeling that is hard to name be seen and understood."
REQUIRED_CORE_POSITIONING_ZH = [
    "开发 → 自动化测试 → 数据产品经理。",
    "我习惯把复杂的系统变得可见，却越来越在意那些没有接口、没有日志、说也说不清的感受。",
    "所以我开始用图像、声音和交互，为它们做一些可以停留的小世界。",
]
REQUIRED_CORE_POSITIONING_EN = [
    "Development → QA automation → data product management.",
    "I learned to make complex systems visible, then became more interested in feelings with no interface, no logs, and no easy name.",
    "So I began using images, sound, and interaction to give those feelings a small world in which to stay.",
]
REQUIRED_BENCHES = [
    {
        "id": "01",
        "name_zh": "把感受变成体验",
        "name_en": "Turning Feeling into Experience",
        "members_zh": "healing-space / pixel-bloom / Healing Visual Lab",
        "members_en": "healing-space / pixel-bloom / Healing Visual Lab",
        "flow_zh": "感受 → 隐喻 → 不可替代动作 → 回应状态",
        "flow_en": "Feeling → metaphor → irreplaceable action → response state",
    },
    {
        "id": "02",
        "name_zh": "让创作流程更可靠",
        "name_en": "Making Creative Workflows Reliable",
        "members_zh": "content-creation-router / inner-voice / echo-caption / duotone-screenprint / social-video-editor / h5-publish",
        "members_en": "content-creation-router / inner-voice / echo-caption / duotone-screenprint / social-video-editor / h5-publish",
        "flow_zh": "输入 → 场景判断 → handoff → 专业执行器 → 用户确认",
        "flow_en": "Input → scene judgment → handoff → specialist executor → user confirmation",
    },
    {
        "id": "03",
        "name_zh": "让判断经得起验证",
        "name_en": "Keeping Judgment Evidence-Bound",
        "members_zh": "content-growth-advisor / yunye-growth-lab / creator-growth-workbench",
        "members_en": "content-growth-advisor / yunye-growth-lab / creator-growth-workbench",
        "flow_zh": "事实 → 推断 → 待验证 → 单变量实验 → 真实复盘",
        "flow_en": "Facts → inference → to be verified → single-variable experiment → real retrospective",
    },
]
REQUIRED_REJECTIONS_ZH = [
    "不把缺失数据当成 `0`。",
    "不把发布完成写成增长成立。",
    "不替用户确认创作意图。",
    "不让公式替代真实读者目标。",
    "不让点击成为没有隐喻意义的特效。",
    "不用万能 Agent 掩盖专业判断的缺失。",
]
REQUIRED_REJECTIONS_EN = [
    "I do not treat missing data as `0`.",
    "I do not write a completed publication as proof that growth happened.",
    "I do not confirm a user’s creative intent on their behalf.",
    "I do not let a formula replace a real reader goal.",
    "I do not let a click become an effect with no metaphorical meaning.",
    "I do not use a one-size-fits-all Agent to conceal the absence of professional judgment.",
]
REQUIRED_PATH_ZH = "开发 → 自动化测试 → 数据产品经理 → 用技术把感受与创作变成可以被体验的东西"
REQUIRED_PATH_EN = "Development → QA automation → data product management → using technology to turn feelings and creative ideas into experiences"
REQUIRED_ENTRANCES = [
    ("portfolio", "完整作品集", "Complete portfolio", "https://shasha1108.github.io/healing-visual-lab/"),
    ("xiaohongshu", "小红书", "Xiaohongshu", "https://xhslink.com/m/1kVPy4geTiQ"),
    ("github", "个人主页", "Personal profile", "https://github.com/shasha1108"),
]
WORK_URL = re.compile(
    r"^https://shasha1108\.github\.io/healing-visual-lab/([a-z0-9-]+)/\1\.html$"
)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"missing required file: {path.relative_to(ROOT)}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {error}") from error


def load_data() -> tuple[dict, dict]:
    config = read_json(CONFIG_PATH)
    source_rel = config.get("source_snapshot")
    if not isinstance(source_rel, str) or not source_rel:
        raise ValueError("showcase.json must define a string source_snapshot")
    snapshot = read_json(ROOT / source_rel)
    return config, snapshot


def write_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def source_catalog(snapshot: dict) -> dict[str, dict]:
    catalog = snapshot.get("catalog", [])
    if not isinstance(catalog, list):
        return {}
    return {work.get("slug"): work for work in catalog if isinstance(work, dict) and nonempty_text(work.get("slug"))}


def validate(config: dict, snapshot: dict) -> list[str]:
    errors: list[str] = []
    catalog = source_catalog(snapshot)
    source = snapshot.get("source")

    if not isinstance(source, dict):
        errors.append("snapshot must contain source metadata")
    else:
        for key in ("upstream_manifest", "upstream_ref", "upstream_commit", "pages_base"):
            if not nonempty_text(source.get(key)):
                errors.append(f"snapshot source.{key} must be a non-empty string")
        expected_count = source.get("upstream_work_count")
        if not isinstance(expected_count, int) or expected_count != len(catalog):
            errors.append("snapshot source.upstream_work_count must equal catalog length")

    if not catalog:
        errors.append("snapshot catalog must contain source-backed works")
    else:
        for slug, work in catalog.items():
            if not nonempty_text(work.get("title_zh")) or not nonempty_text(work.get("title_en")):
                errors.append(f"catalog {slug} must have Chinese and English titles")
            url = work.get("page_url")
            match = WORK_URL.fullmatch(url) if isinstance(url, str) else None
            if not match or match.group(1) != slug:
                errors.append(f"catalog {slug} has an invalid canonical page_url")
            if work.get("preview_asset") is not None and not nonempty_text(work.get("preview_asset")):
                errors.append(f"catalog {slug} preview_asset must be a filename or null")

    identity = config.get("identity")
    if not isinstance(identity, dict):
        errors.append("identity must be an object")
    else:
        if identity.get("signature_zh") != REQUIRED_SIGNATURE_ZH:
            errors.append("identity must retain the Sha.w.z / 云野自由 signature")
        if identity.get("role_zh") != REQUIRED_ROLE_ZH:
            errors.append("identity must retain the approved Chinese role line")
        if identity.get("signature_en") != REQUIRED_SIGNATURE_EN:
            errors.append("identity must retain the approved English signature")
        if identity.get("role_en") != REQUIRED_ROLE_EN:
            errors.append("identity must retain the approved English role")

    entrance = config.get("entrance")
    if not isinstance(entrance, dict):
        errors.append("entrance must be an object")
    else:
        if entrance.get("title_zh") != REQUIRED_TITLE_ZH:
            errors.append("entrance must retain the personal Chinese emotional statement")
        if entrance.get("title_en") != REQUIRED_TITLE_EN:
            errors.append("entrance must retain the English emotional statement")
        if entrance.get("core_positioning_zh") != REQUIRED_CORE_POSITIONING_ZH:
            errors.append("entrance must retain the three approved Chinese positioning statements")
        core_en = entrance.get("core_positioning_en")
        if core_en != REQUIRED_CORE_POSITIONING_EN:
            errors.append("entrance must retain the three approved English positioning statements")

    for key in ("flagship_works", "responsive_worlds", "gallery"):
        if not isinstance(config.get(key), list):
            errors.append(f"showcase.json {key} must be a list")

    flagships = config.get("flagship_works", [])
    if isinstance(flagships, list):
        slugs = [entry.get("slug") for entry in flagships if isinstance(entry, dict)]
        if slugs != FLAGSHIP_ORDER:
            errors.append("flagship_works must retain the required initial order")
        if len(slugs) != len(flagships):
            errors.append("every flagship entry must be an object with a slug")
        for entry in flagships:
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug")
            if slug not in catalog:
                errors.append(f"flagship {slug!r} is absent from the source catalog")
            for key in ("note_zh", "note_en"):
                if not nonempty_text(entry.get(key)):
                    errors.append(f"flagship {slug} must define {key}")
            preview = entry.get("preview_image")
            if not nonempty_text(preview) or not (ROOT / str(preview)).is_file():
                errors.append(f"flagship {slug} must reference an existing local preview_image")
            parts = entry.get("five_parts")
            if not isinstance(parts, dict):
                errors.append(f"flagship {slug} must include five_parts")
                continue
            for language, labels in (("zh", FIVE_PARTS_ZH), ("en", FIVE_PARTS_EN)):
                values = parts.get(language)
                if not isinstance(values, list) or len(values) != 5:
                    errors.append(f"flagship {slug} must contain five {language} explanation parts")
                    continue
                actual_labels = [item.get("label") for item in values if isinstance(item, dict)]
                if actual_labels != labels:
                    errors.append(f"flagship {slug} must use the fixed {language} explanation labels")
                if any(not isinstance(item, dict) or not nonempty_text(item.get("text")) for item in values):
                    errors.append(f"flagship {slug} has an empty {language} explanation")

    worlds = config.get("responsive_worlds", [])
    if isinstance(worlds, list):
        if not RESPONSIVE_MIN <= len(worlds) <= RESPONSIVE_MAX:
            errors.append(f"responsive_worlds must contain {RESPONSIVE_MIN}–{RESPONSIVE_MAX} works")
        world_slugs = [entry.get("slug") for entry in worlds if isinstance(entry, dict)]
        if len(world_slugs) != len(worlds) or len(set(world_slugs)) != len(world_slugs):
            errors.append("responsive_worlds slugs must be unique")
        if set(world_slugs) & set(FLAGSHIP_ORDER):
            errors.append("responsive_worlds and flagship_works must not overlap")
        for entry in worlds:
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug")
            if slug not in catalog:
                errors.append(f"responsive world {slug!r} is absent from the source catalog")
            for key in ("reason_zh", "reason_en", "action_zh", "action_en", "response_zh", "response_en"):
                if not nonempty_text(entry.get(key)):
                    errors.append(f"responsive world {slug} must define {key}")
            size = entry.get("specimen_size", "auto")
            if size not in SPECIMEN_SIZES:
                errors.append(f"responsive world {slug} specimen_size must be one of the supported drawer sizes")

    all_work_slugs = [entry.get("slug") for entry in flagships + worlds if isinstance(entry, dict)]
    if len(all_work_slugs) != len(set(all_work_slugs)):
        errors.append("all selected work slugs must be unique")

    gallery = config.get("gallery", [])
    if isinstance(gallery, list):
        visible = [entry for entry in gallery if isinstance(entry, dict) and entry.get("visible") is True]
        if len(visible) != 21:
            errors.append("gallery must contain exactly 21 visible items")
        ids = [entry.get("id") for entry in gallery if isinstance(entry, dict)]
        images = [entry.get("image") for entry in gallery if isinstance(entry, dict)]
        if len(ids) != len(gallery) or len(set(ids)) != len(ids):
            errors.append("gallery ids must be unique")
        if len(images) != len(gallery) or len(set(images)) != len(images):
            errors.append("gallery image paths must be unique")
        required = (
            "id", "image", "title_zh", "title_en", "description_zh", "description_en",
            "xhs_url", "work_slug", "visible",
        )
        for entry in gallery:
            if not isinstance(entry, dict):
                errors.append("every gallery item must be an object")
                continue
            item_id = entry.get("id", "<unknown>")
            for key in required:
                if key not in entry:
                    errors.append(f"gallery {item_id} is missing required field {key}")
            for key in ("id", "image"):
                if not nonempty_text(entry.get(key)):
                    errors.append(f"gallery {item_id} has an empty {key}")
            for key in ("title_zh", "title_en", "description_zh", "description_en"):
                if not isinstance(entry.get(key), str):
                    errors.append(f"gallery {item_id} {key} must be a string (empty is allowed for unknown metadata)")
            if not isinstance(entry.get("visible"), bool):
                errors.append(f"gallery {item_id} visible must be boolean")
            original = ROOT / str(entry.get("image", ""))
            webp = ROOT / str(entry.get("webp_image", ""))
            if not original.is_file():
                errors.append(f"gallery {item_id} source image is missing: {entry.get('image')}")
            if not webp.is_file() or webp.suffix.lower() != ".webp":
                errors.append(f"gallery {item_id} WebP is missing: {entry.get('webp_image')}")
            xhs_url = entry.get("xhs_url")
            if xhs_url is not None and (not isinstance(xhs_url, str) or not xhs_url.startswith("https://")):
                errors.append(f"gallery {item_id} xhs_url must be null or an https URL")
            work_slug = entry.get("work_slug")
            if work_slug is not None and work_slug not in catalog:
                errors.append(f"gallery {item_id} work_slug must be null or source-backed")

    benches = config.get("workbenches")
    if not isinstance(benches, list) or len(benches) != 3:
        errors.append("workbenches must contain exactly three private system descriptions")
    elif any(not isinstance(entry, dict) for entry in benches):
        errors.append("every workbench must be an object")
    else:
        for entry, required in zip(benches, REQUIRED_BENCHES):
            for key, value in required.items():
                if entry.get(key) != value:
                    errors.append(f"workbench {required['id']} must retain approved {key}")
            for key in ("role_zh", "role_en"):
                if not nonempty_text(entry.get(key)):
                    errors.append(f"workbench {required['id']} must define {key}")

    rejections = config.get("rejections")
    if not isinstance(rejections, list) or len(rejections) != 6:
        errors.append("rejections must contain exactly six principles")
    elif any(not isinstance(entry, dict) or not nonempty_text(entry.get("zh")) or not nonempty_text(entry.get("en")) for entry in rejections):
        errors.append("every rejection must have Chinese and English text")
    elif [entry["zh"] for entry in rejections] != REQUIRED_REJECTIONS_ZH:
        errors.append("rejections must retain the six approved Chinese principles")
    elif [entry["en"] for entry in rejections] != REQUIRED_REJECTIONS_EN:
        errors.append("rejections must retain the six approved English principles")

    path = config.get("path")
    if not isinstance(path, dict):
        errors.append("path must be an object")
    else:
        if path.get("body_zh") != REQUIRED_PATH_ZH:
            errors.append("path must retain the approved Chinese career path")
        if path.get("body_en") != REQUIRED_PATH_EN:
            errors.append("path must retain the approved English career path")
        entrances = path.get("entrances")
        if not isinstance(entrances, list) or len(entrances) != len(REQUIRED_ENTRANCES):
            errors.append("path must contain the required public entrances")
        else:
            actual = [(entry.get("id"), entry.get("label_zh"), entry.get("label_en"), entry.get("url")) if isinstance(entry, dict) else None for entry in entrances]
            if actual != REQUIRED_ENTRANCES:
                errors.append("path entrances must retain the approved labels and real URLs")

    return errors


def print_errors(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


def command_list() -> int:
    config, snapshot = load_data()
    errors = validate(config, snapshot)
    if errors:
        return print_errors(errors)
    catalog = source_catalog(snapshot)
    print("Flagship works")
    for index, entry in enumerate(config["flagship_works"], 1):
        work = catalog[entry["slug"]]
        print(f"  {index}. {work['slug']} — {work['title_zh']} / {work['title_en']}")
    print("Responsive worlds")
    for index, entry in enumerate(config["responsive_worlds"], 1):
        work = catalog[entry["slug"]]
        print(f"  {index}. {work['slug']} — {work['title_zh']} / {work['title_en']}")
    print(f"Visible gallery: {sum(item['visible'] for item in config['gallery'])}")
    return 0


def default_world(work: dict) -> dict:
    tagline = work.get("tagline") or work["title_zh"]
    return {
        "slug": work["slug"],
        "specimen_size": "auto",
        "reason_zh": f"从上游作品清单进入：{tagline}",
        "reason_en": f"From the upstream work manifest: {work.get('title_en') or work['slug']}.",
        "action_zh": "主要动作：进入作品后自行探索。",
        "action_en": "Primary gesture: enter the work and explore on your own terms.",
        "response_zh": "回应方式：由作品本身在被打开后给出。",
        "response_en": "Response: supplied by the work itself after it is opened.",
    }


def command_set_responsive(slugs: list[str]) -> int:
    config, snapshot = load_data()
    catalog = source_catalog(snapshot)
    if not RESPONSIVE_MIN <= len(slugs) <= RESPONSIVE_MAX:
        return print_errors([f"set-responsive requires {RESPONSIVE_MIN}–{RESPONSIVE_MAX} slugs"])
    if len(set(slugs)) != len(slugs):
        return print_errors(["set-responsive slugs must be unique"])
    missing = [slug for slug in slugs if slug not in catalog]
    if missing:
        return print_errors([f"unknown source-backed slug(s): {', '.join(missing)}"])
    overlaps = sorted(set(slugs) & set(FLAGSHIP_ORDER))
    if overlaps:
        return print_errors([f"responsive worlds cannot overlap flagship work(s): {', '.join(overlaps)}"])

    previous = {entry["slug"]: entry for entry in config["responsive_worlds"]}
    config["responsive_worlds"] = [previous.get(slug, default_world(catalog[slug])) for slug in slugs]
    errors = validate(config, snapshot)
    if errors:
        return print_errors(errors)
    write_config(config)
    print(f"Updated responsive worlds ({len(slugs)}): {', '.join(slugs)}")
    return 0


def command_reorder_gallery(ids: list[str]) -> int:
    config, snapshot = load_data()
    existing = [item.get("id") for item in config.get("gallery", []) if isinstance(item, dict)]
    if len(ids) != len(existing) or set(ids) != set(existing) or len(set(ids)) != len(ids):
        return print_errors(["reorder-gallery requires every gallery id exactly once"])
    by_id = {item["id"]: item for item in config["gallery"]}
    config["gallery"] = [by_id[item_id] for item_id in ids]
    errors = validate(config, snapshot)
    if errors:
        return print_errors(errors)
    write_config(config)
    print("Reordered gallery: " + ", ".join(ids))
    return 0


def command_check() -> int:
    config, snapshot = load_data()
    errors = validate(config, snapshot)
    if errors:
        return print_errors(errors)
    visible = sum(item["visible"] for item in config["gallery"])
    print(
        "showcase check: OK "
        f"({len(config['flagship_works'])} flagship, "
        f"{len(config['responsive_worlds'])} responsive, {visible} visible gallery)"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the Living Instrument Room showcase.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list source-backed featured works")
    set_parser = subparsers.add_parser("set-responsive", help="set 3–12 responsive world slugs")
    set_parser.add_argument("slugs", nargs="+", help="source-backed work slugs")
    reorder_parser = subparsers.add_parser("reorder-gallery", help="reorder every gallery id")
    reorder_parser.add_argument("ids", nargs="+", help="gallery ids in desired order")
    subparsers.add_parser("check", help="validate configuration, sources, and image assets")
    args = parser.parse_args()

    try:
        if args.command == "list":
            return command_list()
        if args.command == "set-responsive":
            return command_set_responsive(args.slugs)
        if args.command == "reorder-gallery":
            return command_reorder_gallery(args.ids)
        return command_check()
    except ValueError as error:
        return print_errors([str(error)])


if __name__ == "__main__":
    raise SystemExit(main())
