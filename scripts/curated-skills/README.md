# 精选下载（SkillsMP → GitHub）

从 [SkillsMP](https://skillsmp.com) **按主题限量搜索**，再从 **GitHub 源仓库**下载 skill 目录，写入本仓库对应分类。  
**不是**全站镜像（违反其[服务条款](https://skillsmp.com/terms)）。

## 流程

```
topics.json（主题 + 分类 + 每主题条数）
    → SkillsMP search API（每主题几条）
    → GitHub Contents API 下载目录
    → {category}/{name}/SKILL.md + SOURCE.txt
    → rebuild-index.py 刷新 catalog / site/data/skills.json
```

## 用法

```bash
cd ~/Desktop/skills

# 1) 只看计划（不写盘）
python3 scripts/curated-skills/fetch-curated.py --dry-run

# 2) 真正下载（建议先小范围）
python3 scripts/curated-skills/fetch-curated.py --apply --topics video,figma

# 3) 按 topics.json 全部主题下载
python3 scripts/curated-skills/fetch-curated.py --apply

# 4) 重建站点索引
python3 scripts/curated-skills/rebuild-index.py
```

### 可选环境变量

| 变量 | 作用 |
|------|------|
| `SKILLSMP_API_KEY` | 提高 SkillsMP 额度（登录开发者门户申请） |
| `GITHUB_TOKEN` / `GH_TOKEN` | 提高 GitHub API 限额，私有/限流更稳 |

## 配置

编辑 [`topics.json`](topics.json)：

- `query`：搜索词  
- `category`：入库分类（如 `04-frontend-ui`）  
- `per_topic`：该主题最多拉几条（默认 2～3）  
- `defaults.min_stars`：最低 star 门槛  

同名 skill 已存在时会跳过或自动加 `-作者` 后缀。

## SOURCE.txt

新 skill 会写：

```
origin: skillsmp-curated
github_url: ...
skillsmp_url: ...
```

便于以后追溯与更新。
