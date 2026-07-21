# Skill Café

星巴克设计系统风格的本地 Agent Skills 目录站。

## 启动

必须在 `skills` 根目录起静态服务（下载 / 预览要读上层 skill 文件夹）：

```bash
cd ~/Desktop/skills
python3 -m http.server 8765
```

浏览器打开：http://localhost:8765/site/

## 功能

- 搜索（名称 / 描述 / 分类）
- 分类筛选与排序
- 排行榜 / 热门 / 最近更新
- 预览 `SKILL.md`
- 下载单个 skill（zip 整包，或仅 md）

## 结构

```
site/
  index.html
  css/styles.css
  js/app.js
  data/skills.json   # 由 catalog 生成
```
