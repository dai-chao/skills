# Codex Dream Skin Studio — macOS 安装与切换笔记

适用场景：用户把 GitHub 上的 Fei-Away/Codex-Dream-Skin 仓库 clone 到 macOS，想要安装、切换主题、验证或恢复。

## 前置条件

- macOS 已安装官方 ChatGPT/Codex 桌面端（bundle id `com.openai.codex`）
- 至少启动过一次，确认 `~/.codex/config.toml` 存在
- 安装时 Codex 不能正在运行（脚本会拒绝安装，防止 config.toml 被覆盖）

## 典型流程

```bash
# 1. 关闭 Codex
osascript -e 'tell application id "com.openai.codex" to quit'
# 等待主进程退出

# 2. 安装引擎到 ~/.codex/codex-dream-skin-studio
cd /Users/chao/Desktop/Codex-Dream-Skin/macos
./scripts/install-dream-skin-macos.sh --no-launch

# 3. 启动并注入主题（会带 CDP 重启 Codex）
~/.codex/codex-dream-skin-studio/scripts/start-dream-skin-macos.sh --port 9341 --prompt-restart

# 4. 切换主题（默认已安装 6 个预设）
~/.codex/codex-dream-skin-studio/scripts/switch-theme-macos.sh --id preset-romantic-rose

# 5. 验证并截图
~/.codex/codex-dream-skin-studio/scripts/verify-dream-skin-macos.sh --screenshot "$HOME/Desktop/Codex Dream Skin Verification.png"
```

## 可用预设

- `preset-midnight-aurora`（午夜极光）
- `preset-romantic-rose`（桥本有菜）
- `preset-amber-dusk`
- `preset-cyber-neon`
- `preset-forest-mist`
- `preset-sakura-dawn`

## 恢复官方外观

```bash
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh --restore-base-theme --restart-codex
```

## 重要路径

- 引擎：`~/.codex/codex-dream-skin-studio`
- 状态/日志：`~/Library/Application Support/CodexDreamSkinStudio`
- 主题库：`~/Library/Application Support/CodexDreamSkinStudio/themes`
- 当前激活主题：`~/Library/Application Support/CodexDreamSkinStudio/theme`

## 日志排障

- 启动错误：`~/Library/Application Support/CodexDreamSkinStudio/start-error.log`
- 注入器日志：`~/Library/Application Support/CodexDreamSkinStudio/injector.log`
- 注入器错误：`~/Library/Application Support/CodexDreamSkinStudio/injector-error.log`
- Codex 启动日志：`~/Library/Application Support/CodexDreamSkinStudio/codex-launch.log`

## 常见坑点

1. **安装时 Codex 正在运行**：脚本会拒绝安装。必须先退出应用，等 `/Applications/ChatGPT.app/Contents/MacOS/ChatGPT` 主进程消失。
2. **启动脚本超时**：如果 120 秒超时，不代表失败，可能是脚本挂起等待。检查 `state.json` 和 `injector.log` 看是否已注入成功。
3. **验证脚本不接受 `--timeout-ms`**：直接运行 `verify-dream-skin-macos.sh`，或加 `--screenshot` 参数。
4. **主题未生效**：切换主题后如果窗口早就打开，可能需要重新切换一次路由或重新启动 Codex 让注入器重新应用。
5. **不要直接用效果图做背景**：仓库 `docs/images/presets/*-light.jpg` 等截图带 UI，不能当 `background.jpg` 导入；要用 `*-source.png` 或自己生成的无 UI 壁纸。

## 安全边界

- CDP 只绑定 `127.0.0.1`
- 不修改 `.app` / `app.asar` / WindowsApps / 代码签名
- 不改 API Key 或 Base URL

## 相关文件

- 项目 `macos/README.md`：完整使用指南
- 项目 `macos/SKILL.md`：能力入口说明
- 注入脚本：`~/.codex/codex-dream-skin-studio/scripts/injector.mjs`
