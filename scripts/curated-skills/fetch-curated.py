#!/usr/bin/env python3
"""
Curated skill download: SkillsMP search (limited) → download folder from GitHub.

Does NOT scrape SkillsMP wholesale. Uses their public search API within rate limits,
then pulls the skill directory from GitHub (source of truth).

Usage:
  python3 scripts/curated-skills/fetch-curated.py --dry-run
  python3 scripts/curated-skills/fetch-curated.py --apply
  python3 scripts/curated-skills/fetch-curated.py --apply --topics video,figma
  SKILLSMP_API_KEY=sk_live_xxx python3 ... --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOPICS_PATH = Path(__file__).resolve().parent / "topics.json"
SKILLSMP_SEARCH = "https://skillsmp.com/api/v1/skills/search"
GITHUB_API = "https://api.github.com"
USER_AGENT = "SkillCafe-CuratedFetch/1.0 (+local curated import)"

CATEGORY_LABELS = {
    "01-cursor-native": "Cursor 原生能力",
    "02-workflow-git": "Git / PR / 工作流",
    "03-code-quality": "代码质量 / 安全 / Review",
    "04-frontend-ui": "前端 / UI / 设计",
    "05-testing": "测试 / QA",
    "06-devops-infra": "DevOps / 基础设施",
    "07-docs-office": "文档 / Office / 内容",
    "08-research-web": "调研 / 联网 / 搜索",
    "09-analytics": "分析 / 可观测 / 监控",
    "10-payments-auth": "支付 / 认证",
    "11-planning": "规划 / 架构",
    "12-meta": "Skill 创作 / Meta",
    "13-integrations": "厂商集成 / 平台",
    "14-finance": "金融 / 投资",
    "99-misc": "其他 / 未分类",
}


def http_json(url: str, headers: dict | None = None, retries: int = 3) -> dict:
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 502, 503) and i < retries - 1:
                time.sleep(2 ** (i + 1))
                continue
            body = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {e.code} for {url}: {body}") from e
        except Exception as e:
            last_err = e
            if i < retries - 1:
                time.sleep(1)
                continue
            raise
    raise RuntimeError(str(last_err))


def http_bytes(url: str, headers: dict | None = None) -> bytes:
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def github_headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def skillsmp_headers() -> dict:
    h = {}
    key = os.environ.get("SKILLSMP_API_KEY")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def parse_github_tree_url(url: str) -> tuple[str, str, str, str] | None:
    """
    https://github.com/{owner}/{repo}/tree/{ref}/{path...}
    https://github.com/{owner}/{repo}  → ref=main, path="" (repo root skill)
    → owner, repo, ref, path
    """
    url = url.strip().rstrip("/")
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.*)$",
        url,
    )
    if m:
        owner, repo, ref, path = m.groups()
        return owner, repo, ref, path
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)$", url)
    if m:
        owner, repo, ref = m.groups()
        return owner, repo, ref, ""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)$", url)
    if m:
        owner, repo = m.groups()
        return owner, repo, "main", ""
    return None


def existing_skill_names() -> set[str]:
    names = set()
    for cat in CATEGORY_LABELS:
        d = ROOT / cat
        if not d.is_dir():
            continue
        for child in d.iterdir():
            if child.is_dir() and (child / "SKILL.md").exists():
                names.add(child.name.lower())
    return names


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-").lower()
    return s or "skill"


def unique_dir_name(base: str, author: str, taken: set[str]) -> str:
    base = slugify(base)
    if base not in taken:
        return base
    alt = slugify(f"{base}-{author}")
    if alt not in taken:
        return alt
    i = 2
    while f"{alt}-{i}" in taken:
        i += 1
    return f"{alt}-{i}"


def search_skillsmp(query: str, limit: int, sort_by: str, language: str | None) -> list[dict]:
    params = {
        "q": query,
        "limit": min(limit * 3, 50),  # oversample then filter
        "page": 1,
        "sortBy": sort_by,
    }
    if language:
        params["language"] = language
    url = SKILLSMP_SEARCH + "?" + urllib.parse.urlencode(params)
    data = http_json(url, headers=skillsmp_headers())
    if not data.get("success"):
        raise RuntimeError(f"SkillsMP search failed: {data}")
    return data.get("data", {}).get("skills") or []


def list_github_dir(owner: str, repo: str, path: str, ref: str) -> list[dict]:
    if path:
        api = (
            f"{GITHUB_API}/repos/{owner}/{repo}/contents/"
            f"{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"
        )
    else:
        api = f"{GITHUB_API}/repos/{owner}/{repo}/contents?ref={urllib.parse.quote(ref)}"
    data = http_json(api, headers=github_headers())
    if isinstance(data, dict) and data.get("type") == "file":
        return [data]
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected GitHub contents response for {api}")
    return data


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def download_via_sparse_git(owner: str, repo: str, path: str, ref: str, dest: Path) -> list[str]:
    """Clone with sparse-checkout (avoids GitHub REST rate limits)."""
    tmp_root = ROOT / "_tmp_curated"
    tmp_root.mkdir(parents=True, exist_ok=True)
    clone_dir = tmp_root / f"{owner}-{repo}-{os.getpid()}"
    if clone_dir.exists():
        shutil.rmtree(clone_dir, ignore_errors=True)

    url = f"https://github.com/{owner}/{repo}.git"
    try:
        _run(
            [
                "git",
                "-c",
                "advice.detachedHead=false",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                ref,
                url,
                str(clone_dir),
            ]
        )
    except subprocess.CalledProcessError:
        # branch name might be a commit-ish; try default branch then checkout ref
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                url,
                str(clone_dir),
            ]
        )
        try:
            _run(["git", "fetch", "--depth", "1", "origin", ref], cwd=clone_dir)
            _run(["git", "checkout", ref], cwd=clone_dir)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"git clone/checkout failed for {url}@{ref}: {e.stderr}") from e

    sparse_paths = []
    if path:
        sparse_paths.append(path)
    else:
        sparse_paths.extend(["SKILL.md", "scripts", "references", "assets", "templates", "examples"])

    try:
        _run(["git", "sparse-checkout", "set", *sparse_paths], cwd=clone_dir)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"sparse-checkout failed: {e.stderr}") from e

    src = clone_dir / path if path else clone_dir
    if path and not src.exists():
        raise RuntimeError(f"path not found in repo: {path}")

    if not path:
        # copy only skill-relevant bits from repo root
        dest.mkdir(parents=True, exist_ok=True)
        files = []
        for name in ("SKILL.md", "README.md", "LICENSE", "LICENSE.md", "AGENTS.md"):
            p = src / name
            if p.is_file():
                shutil.copy2(p, dest / name)
                files.append(name)
        for dname in ("scripts", "references", "assets", "templates", "examples"):
            d = src / dname
            if d.is_dir():
                shutil.copytree(d, dest / dname, dirs_exist_ok=True)
                for f in (dest / dname).rglob("*"):
                    if f.is_file():
                        files.append(f.relative_to(dest).as_posix())
    else:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git", "node_modules", ".DS_Store"))
        files = [
            f.relative_to(dest).as_posix()
            for f in dest.rglob("*")
            if f.is_file()
        ]

    shutil.rmtree(clone_dir, ignore_errors=True)
    return files


def download_github_tree(owner: str, repo: str, path: str, ref: str, dest: Path) -> list[str]:
    """Prefer git sparse-checkout; fall back to Contents API."""
    try:
        return download_via_sparse_git(owner, repo, path, ref, dest)
    except Exception as git_err:
        print(f"  git sparse failed ({git_err}); trying API…")
        return download_github_tree_api(owner, repo, path, ref, dest)


def download_github_tree_api(owner: str, repo: str, path: str, ref: str, dest: Path) -> list[str]:
    """Recursively download via GitHub Contents API."""
    files: list[str] = []
    entries = list_github_dir(owner, repo, path, ref)
    dest.mkdir(parents=True, exist_ok=True)

    if not path:
        names = {e["name"] for e in entries}
        if "SKILL.md" not in names:
            for candidate in ("skills", ".agents/skills", ".claude/skills"):
                top = candidate.split("/")[0]
                if top in names:
                    try:
                        nested = list_github_dir(owner, repo, candidate, ref)
                        if any(e.get("name") == "SKILL.md" for e in nested):
                            return download_github_tree_api(owner, repo, candidate, ref, dest)
                    except Exception:
                        pass

    for ent in entries:
        name = ent["name"]
        if name in (".git", "node_modules", ".DS_Store"):
            continue
        if not path and ent["type"] == "dir" and name not in (
            "scripts",
            "references",
            "assets",
            "templates",
            "examples",
        ):
            continue
        if ent["type"] == "file":
            if ent.get("size", 0) > 2_000_000:
                print(f"  skip large file: {name} ({ent.get('size')} bytes)")
                continue
            if not path and name not in (
                "SKILL.md",
                "README.md",
                "LICENSE",
                "LICENSE.md",
                "AGENTS.md",
            ) and not name.endswith((".md", ".py", ".sh", ".js", ".ts", ".json")):
                continue
            download_url = ent.get("download_url")
            if not download_url:
                continue
            content = http_bytes(download_url, headers=github_headers())
            (dest / name).write_bytes(content)
            files.append(name)
        elif ent["type"] == "dir":
            sub_path = f"{path}/{name}" if path else name
            sub = download_github_tree_api(owner, repo, sub_path, ref, dest / name)
            files.extend(f"{name}/{s}" for s in sub)
        time.sleep(0.05)
    return files


def content_hash(skill_md: Path) -> str:
    h = hashlib.sha256(skill_md.read_bytes()).hexdigest()
    return h[:12]


def write_source_txt(
    dest: Path,
    *,
    category: str,
    github_url: str,
    skill_url: str,
    author: str,
    stars: int,
    skillsmp_id: str,
) -> None:
    skill_md = dest / "SKILL.md"
    lines = [
        "origin: skillsmp-curated",
        f"repo: {author}",
        f"github_url: {github_url}",
        f"skillsmp_url: {skill_url}",
        f"skillsmp_id: {skillsmp_id}",
        f"stars: {stars}",
        f"source_path: {skill_md}",
        f"content_hash: {content_hash(skill_md) if skill_md.exists() else 'pending'}",
        f"category: {category}",
        "",
    ]
    (dest / "SOURCE.txt").write_text("\n".join(lines), encoding="utf-8")


def skill_dedupe_key(h: dict) -> str:
    """Prefer one skill per author+name (drop locale doc mirrors)."""
    name = slugify(h.get("name") or "skill")
    author = (h.get("author") or "").lower()
    return f"{author}::{name}"


def path_quality(github_url: str) -> int:
    """Higher is better — prefer canonical skills/ over localized docs/."""
    u = github_url.lower()
    score = 0
    if "/skills/" in u:
        score += 10
    if "/docs/" in u or "/ja-" in u or "/zh-" in u or "/ko-" in u:
        score -= 5
    if u.count("/") > 8:
        score -= 1
    return score


def pick_candidates(
    hits: list[dict],
    *,
    need: int,
    min_stars: int,
    taken_names: set[str],
    skip_existing: bool,
) -> list[dict]:
    # rank hits: stars then path quality
    ranked = sorted(
        hits,
        key=lambda h: (int(h.get("stars") or 0), path_quality(h.get("githubUrl") or "")),
        reverse=True,
    )
    picked = []
    seen_urls = set()
    seen_keys = set()
    for h in ranked:
        if len(picked) >= need:
            break
        stars = int(h.get("stars") or 0)
        if stars < min_stars:
            continue
        gurl = h.get("githubUrl") or ""
        parsed = parse_github_tree_url(gurl)
        if not parsed:
            continue
        if gurl in seen_urls:
            continue
        key = skill_dedupe_key(h)
        if key in seen_keys:
            continue
        name = slugify(h.get("name") or "skill")
        if skip_existing and name in taken_names:
            # still allow author-suffixed download later
            pass
        seen_urls.add(gurl)
        seen_keys.add(key)
        picked.append(h)
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description="Curated SkillsMP → GitHub skill import")
    ap.add_argument("--dry-run", action="store_true", help="Only plan (default if no --apply)")
    ap.add_argument("--apply", action="store_true", help="Actually download into categories")
    ap.add_argument("--topics", type=str, default="", help="Comma-separated topic ids")
    ap.add_argument("--config", type=Path, default=TOPICS_PATH)
    ap.add_argument("--per-topic", type=int, default=0, help="Override per-topic limit")
    args = ap.parse_args()

    apply = bool(args.apply)
    dry = (not apply) or args.dry_run
    if args.apply and args.dry_run:
        dry = True
        apply = False

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    defaults = cfg.get("defaults") or {}
    topics = cfg.get("topics") or []
    if args.topics:
        want = {t.strip() for t in args.topics.split(",") if t.strip()}
        topics = [t for t in topics if t["id"] in want]

    taken = existing_skill_names()
    skip_existing = bool(defaults.get("skip_existing_names", True))
    min_stars = int(defaults.get("min_stars", 50))
    sort_by = defaults.get("sortBy") or "stars"
    language = defaults.get("language")

    planned = []
    print(f"Root: {ROOT}")
    print(f"Mode: {'DRY-RUN' if dry else 'APPLY'}")
    print(f"Existing skills: {len(taken)}")
    print()

    for topic in topics:
        tid = topic["id"]
        query = topic["query"]
        category = topic["category"]
        need = args.per_topic or topic.get("per_topic") or defaults.get("per_topic") or 3
        lang = topic.get("language", language)
        topic_min_stars = int(topic.get("min_stars", min_stars))

        print(f"[{tid}] search «{query}» → {category} (need {need})")
        try:
            hits = search_skillsmp(query, need, sort_by, lang)
        except Exception as e:
            print(f"  ERROR search: {e}")
            continue
        time.sleep(0.4)

        picks = pick_candidates(
            hits,
            need=need,
            min_stars=topic_min_stars,
            taken_names=taken,
            skip_existing=skip_existing,
        )
        if not picks:
            print("  (no candidates)")
            continue

        for h in picks:
            gurl = h["githubUrl"]
            parsed = parse_github_tree_url(gurl)
            if not parsed:
                print(f"  skip unparsable URL: {gurl}")
                continue
            owner, repo, ref, path = parsed
            dirname = unique_dir_name(h.get("name") or "skill", h.get("author") or owner, taken)
            dest = ROOT / category / dirname
            item = {
                "topic": tid,
                "name": dirname,
                "category": category,
                "dest": str(dest.relative_to(ROOT)),
                "githubUrl": gurl,
                "skillUrl": h.get("skillUrl"),
                "author": h.get("author"),
                "stars": h.get("stars"),
                "description": (h.get("description") or "")[:160],
                "skillsmp_id": h.get("id"),
                "owner": owner,
                "repo": repo,
                "ref": ref,
                "path": path,
            }
            planned.append(item)
            taken.add(dirname)
            print(f"  + {dirname}  ★{h.get('stars')}  {gurl}")

        print()

    print(f"Planned: {len(planned)} skills")
    if dry:
        print("Dry-run only. Re-run with --apply to download.")
        return 0

    ok = 0
    fail = 0
    for item in planned:
        dest = ROOT / item["dest"]
        if dest.exists() and (dest / "SKILL.md").exists():
            print(f"skip exists: {item['dest']}")
            continue
        print(f"download: {item['dest']}")
        try:
            files = download_github_tree(
                item["owner"], item["repo"], item["path"], item["ref"], dest
            )
            if not (dest / "SKILL.md").exists():
                raise RuntimeError("SKILL.md missing after download")
            write_source_txt(
                dest,
                category=item["category"],
                github_url=item["githubUrl"],
                skill_url=item.get("skillUrl") or "",
                author=item.get("author") or item["owner"],
                stars=int(item.get("stars") or 0),
                skillsmp_id=item.get("skillsmp_id") or "",
            )
            print(f"  ok ({len(files)} files)")
            ok += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            fail += 1
            # cleanup partial
            if dest.exists() and not (dest / "SKILL.md").exists():
                shutil.rmtree(dest, ignore_errors=True)
        time.sleep(0.3)

    print()
    print(f"Done. ok={ok} fail={fail}")
    print("Next: python3 scripts/curated-skills/rebuild-index.py")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
