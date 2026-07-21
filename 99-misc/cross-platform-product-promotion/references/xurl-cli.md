# xurl — X (Twitter) 官方 CLI 参考

`xurl` 是 X 开发者平台维护的官方 CLI，支持 X API v2 的常见操作和 raw curl 式访问。以下命令全部返回 JSON。

> 安全提示：不要读取或发送 `~/.xurl` 到对话中；认证和 app 注册必须由用户在终端外完成。详见 `cross-platform-product-promotion` SKILL.md 中的 X/Twitter 发布章节。

## 安装

```bash
# 推荐脚本（Linux/macOS）
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# 验证
xurl --help
xurl auth status
```

## 一次性用户配置（用户在终端外执行）

1. 在 https://developer.x.com/en/portal/dashboard 创建 app，设置 redirect URI 为 `http://localhost:8080/callback`。
2. 注册 app：`xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET`
3. 认证：`xurl auth oauth2 --app my-app [YOUR_USERNAME]`（若 `/2/users/me` 返回 403 则加上用户名）
4. 设为默认：`xurl auth default my-app`
5. 验证：`xurl auth status && xurl whoami`

> Docker 用户注意：Hermes 子进程 HOME 可能是 `/opt/data/home`，所以 `~/.xurl` 实际落在 `/opt/data/home/.xurl`，配置时需要用相同的 HOME。

## 快速参考

| 动作 | 命令 |
| --- | --- |
| 发推 | `xurl post "Hello world!"` |
| 带图发推 | `xurl media upload photo.jpg` → `xurl post "..." --media-id MEDIA_ID` |
| 回复 | `xurl reply POST_ID "Nice post!"` |
| 引用 | `xurl quote POST_ID "My take"` |
| 删除 | `xurl delete POST_ID` |
| 读取 | `xurl read POST_ID` |
| 搜索 | `xurl search "QUERY" -n 10` |
| 我是谁 | `xurl whoami` |
| 查用户 | `xurl user @handle` |
| 时间线 | `xurl timeline -n 20` |
| 提及 | `xurl mentions -n 10` |
| 点赞/取消 | `xurl like POST_ID` / `xurl unlike POST_ID` |
| 转发/取消 | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| 关注/取消 | `xurl follow @handle` / `xurl unfollow @handle` |
| 发私信 | `xurl dm @handle "message"` |
| 列私信 | `xurl dms -n 25` |
| 上传媒体 | `xurl media upload path/to/file.mp4` |
| 媒体状态 | `xurl media status MEDIA_ID` |

POST_ID 支持完整 URL（如 `https://x.com/user/status/1234567890`），xurl 会自动提取 ID。

## 全局参数

- `--app APP`：指定已注册的 app（覆盖默认）。
- `--username / -u USER`：同一 app 下多个账号时指定用户。
- `--verbose / -v`：**禁止在 agent 会话中使用**，可能泄漏认证头。

## Raw API 模式

```bash
xurl /2/users/me
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'
xurl -X DELETE /2/tweets/1234567890
xurl https://api.x.com/2/users/me
```

## 常见错误

- 认证成功后仍报错：OAuth token 可能存到了空的 `default` app，而非命名的 app。重跑 `xurl auth oauth2 --app my-app` 并 `xurl auth default my-app`。
- `UsernameNotFound` / 403 on `/2/users/me`：加上用户名重跑认证（xurl v1.1.0+）。
- `client-forbidden` / `client-not-enrolled`：需在 X dashboard 将 app 移到 "Pay-per-use" 套餐的 Production 环境。
- `CreditsDepleted`：API 余额不足，需充值。
- 图片上传失败：默认 category 是 `amplify_video`，加 `--category tweet_image --media-type image/png`。

## 完整上游

- CLI: https://github.com/xdevplatform/xurl
- 原 Hermes skill 已合并到 `cross-platform-product-promotion`。
