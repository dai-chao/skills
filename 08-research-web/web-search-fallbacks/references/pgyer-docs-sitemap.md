# 蒲公英（pgyer.com）文档站点结构与导航

来源：会话中通过 `curl -sL https://www.pgyer.com/doc/view/account_certification` 获取的 Next.js 服务端 JSON payload 中暴露的完整页面树。

## 站点特征

- 文档中心根路径：`https://www.pgyer.com/doc/view`
- 页面路由为 `/doc/view/<slug>`，slug 通常是 kebab-case 的英文/拼音标识。
- 使用 Next.js 客户端水合（hydration）；`web_extract` 不可用（SearXNG 仅限搜索），且 `browser_navigate` 已能正常渲染。
- 若已知 slug，直接 `browser_navigate` 是最快路径；若不确定 slug，可查看页面树或从 `https://www.pgyer.com/doc/view/quick_start` 进入后点击侧边栏。

## 已确认的常见 slug 映射

| 中文标题 | slug | 目录 |
|---|---|---|
| 快速开始 | `quick_start` | 根 |
| 应用上传 | `app_upload` | 应用上传与发布 |
| 内测模式与分发模式 | `app_install` | 应用管理 |
| 实名认证 | `certified` | 账号与合规 |
| 协议与政策 | `legal` | 账号与合规 |
| 应用下载计费说明 | `download_fee` | 计费与发票 |
| 应用审核概述 | `review_summary` | 应用审核指南 |
| 应用资质 | `review_app_certification` | 应用审核指南 |
| 开放 API 2.0 | `api` | API 2.0 |

## 查找未知 slug 的方法

1. 打开任意文档页，执行 `curl -sL https://www.pgyer.com/doc/view/<候选slug>`。
2. 在返回的 HTML 中搜索 `\"$id\":\"zh-CN:` 片段，可找到完整页面树与每个页面的 `name` / `url` / `file` 对应关系。
3. 例如 `"account_certification"` 在 2026-07-20 已返回 404，其实际 slug 为 `certified`。

## 相关页面

- 内测/分发模式对比：https://www.pgyer.com/doc/view/app_install
- 实名认证（个人/企业差异）：https://www.pgyer.com/doc/view/certified
