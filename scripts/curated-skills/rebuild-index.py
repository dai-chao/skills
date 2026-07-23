#!/usr/bin/env python3
"""
Rebuild catalog.json + site/data/skills.json by scanning category folders.

Preserves popularity / hot / rank / description_zh from the previous skills.json
when the skill id already exists.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_JSON = ROOT / "site" / "data" / "skills.json"
CATALOG_JSON = ROOT / "catalog.json"
SYNONYMS_JSON = ROOT / "site" / "data" / "search-synonyms.json"

CATEGORIES = [
    ("01-cursor-native", "Cursor 原生能力"),
    ("02-workflow-git", "Git / PR / 工作流"),
    ("03-code-quality", "代码质量 / 安全 / Review"),
    ("04-frontend-ui", "前端 / UI / 设计"),
    ("05-testing", "测试 / QA"),
    ("06-devops-infra", "DevOps / 基础设施"),
    ("07-docs-office", "文档 / Office / 内容"),
    ("08-research-web", "调研 / 联网 / 搜索"),
    ("09-analytics", "分析 / 可观测 / 监控"),
    ("10-payments-auth", "支付 / 认证"),
    ("11-planning", "规划 / 架构"),
    ("12-meta", "Skill 创作 / Meta"),
    ("13-integrations", "厂商集成 / 平台"),
    ("14-finance", "金融 / 投资"),
    ("99-misc", "其他 / 未分类"),
]


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    meta: dict[str, str] = {}
    key: str | None = None
    folded: list[str] = []
    folded_style: str | None = None  # '>' or '|'

    def flush() -> None:
        nonlocal key, folded, folded_style
        if key is None:
            return
        if folded_style:
            # YAML folded (>) → join with spaces; literal (|) → keep newlines
            body = "\n".join(folded).strip()
            meta[key] = " ".join(body.split()) if folded_style == ">" else body
        key = None
        folded = []
        folded_style = None

    for raw in block.splitlines():
        line = raw.rstrip()
        if folded_style is not None:
            # continuation: indented, or blank line inside block
            if not line.strip():
                folded.append("")
                continue
            if line.startswith(" ") or line.startswith("\t"):
                folded.append(line.strip())
                continue
            flush()

        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if not k:
            continue
        if v in (">", "|"):
            flush()
            key = k
            folded_style = v
            folded = []
            continue
        flush()
        meta[k] = v.strip().strip("\"'")

    flush()
    return meta


def title_from_name(name: str) -> str:
    return re.sub(r"[-_]+", " ", name).strip().title()


def read_origin(skill_dir: Path) -> str:
    src = skill_dir / "SOURCE.txt"
    if not src.exists():
        return "local"
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("origin:"):
            return line.split(":", 1)[1].strip() or "local"
    return "local"


def list_files(skill_dir: Path, limit: int = 40) -> list[str]:
    files = []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(skill_dir).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        if "node_modules" in rel:
            continue
        files.append(rel)
        if len(files) >= limit:
            break
    return files


def load_category_keywords() -> dict[str, list[str]]:
    if not SYNONYMS_JSON.exists():
        return {}
    try:
        data = json.loads(SYNONYMS_JSON.read_text(encoding="utf-8"))
        raw = data.get("category_keywords") or {}
        return {str(k): [str(x) for x in (v or [])] for k, v in raw.items()}
    except Exception:
        return {}


def load_prev() -> dict[str, dict]:
    if not SITE_JSON.exists():
        return {}
    data = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    return {s["id"]: s for s in data.get("skills") or []}


def main() -> int:
    prev = load_prev()
    cat_keywords = load_category_keywords()
    skills = []
    catalog = []

    for cat_id, cat_label in CATEGORIES:
        cat_dir = ROOT / cat_id
        if not cat_dir.is_dir():
            continue
        for skill_dir in sorted(cat_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.exists():
                continue
            name = skill_dir.name
            sid = f"{cat_id}/{name}"
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            meta = parse_frontmatter(text)
            description = meta.get("description") or ""
            if not description:
                # first non-empty paragraph after frontmatter
                body = text
                if body.startswith("---"):
                    end = body.find("\n---", 3)
                    if end >= 0:
                        body = body[end + 4 :]
                for line in body.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        description = line[:300]
                        break

            title = (meta.get("title") or "").strip() or title_from_name(meta.get("name") or name)
            origin = read_origin(skill_dir)
            files = list_files(skill_dir)
            st = skill_md.stat()
            updated_ts = int(st.st_mtime)
            updated = datetime.fromtimestamp(updated_ts, tz=timezone.utc).strftime("%Y-%m-%d")

            old = prev.get(sid, {})
            popularity = old.get("popularity", 0) or 0
            hot = old.get("hot", float(popularity) if popularity else 0)
            rank = old.get("rank", 0)
            description_zh = old.get("description_zh") or ""
            # Refresh Chinese blurb when frontmatter description carries CJK keywords
            if re.search(r"[\u4e00-\u9fff]", description):
                description_zh = description[:400]

            search_keywords = list(cat_keywords.get(cat_id) or [])

            skills.append(
                {
                    "id": sid,
                    "name": name,
                    "title": title,
                    "category": cat_id,
                    "category_label": cat_label,
                    "description": description[:400],
                    "origin": origin,
                    "path": sid,
                    "files": files,
                    "updated": updated,
                    "updated_ts": updated_ts,
                    "popularity": popularity,
                    "hot": hot,
                    "rank": rank,
                    "description_zh": description_zh,
                    "search_keywords": search_keywords,
                }
            )
            catalog.append(
                {
                    "name": name,
                    "original_name": meta.get("name") or name,
                    "category": cat_id,
                    "category_label": cat_label,
                    "description": description[:400],
                    "origin": origin,
                    "source": str(skill_md),
                }
            )

    # rank by hot desc if ranks missing/zero
    skills_sorted = sorted(skills, key=lambda s: (-(s.get("hot") or 0), s["name"]))
    for i, s in enumerate(skills_sorted, start=1):
        if not s.get("rank"):
            s["rank"] = i

    # keep category then name order in file for stability
    skills.sort(key=lambda s: (s["category"], s["name"]))
    catalog.sort(key=lambda s: (s["category"], s["name"]))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    out = {
        "generated_at": now,
        "total": len(skills),
        "categories": [{"id": c, "label": l} for c, l in CATEGORIES],
        "skills": skills,
    }
    SITE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SITE_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {SITE_JSON.relative_to(ROOT)} ({len(skills)} skills)")
    print(f"Wrote {CATALOG_JSON.relative_to(ROOT)} ({len(catalog)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
