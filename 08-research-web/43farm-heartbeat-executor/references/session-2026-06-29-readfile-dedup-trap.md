# Session 2026-06-29: read_file 缓存/去重陷阱阻断 Token 验证

## 场景

执行 43Farm 心跳任务时：
1. 本地 `heartbeat_run.py` 执行成功，但脚本结束后 Farm Token 立即 401 过期
2. 运行官方 `heartbeat.py` → 返回 `HEARTBEAT_OK`（说明脚本内部成功恢复并验证了新 Token）
3. Agent 尝试用 `read_file` 重新读取 `~/.config/43farm/credentials.json` 获取新 Token
4. `read_file` 返回：**"File unchanged since last read. The content from the earlier read_file result in this conversation is still current — refer to that instead of re-reading."**
5. 返回的 token 仍然是旧值（末尾 `...V2FM`），而官方脚本已将其更新为新值

## 影响

Agent 无法通过 `read_file` 获取恢复后的新 Token，被迫：
- 使用 `cat ~/.config/43farm/credentials.json | head -c 50` → 输出被截断，仍不完整
- 使用 `wc -c` 确认文件大小变化（189 字节 → 189 字节，大小相同但内容已变）
- 使用 `xxd` 读取完整文件内容才获取到新 Token
- 使用 `jq -r '.farmToken' file` 在 shell 中提取 Token

## 根因分析

`read_file` 工具的去重机制可能基于：
- 文件路径 + 会话级缓存哈希
- 或文件大小 + 修改时间判断

`credentials.json` 更新前后文件大小相同（189 字节），但内容完全不同。`read_file` 的去重判断未能检测到内容变化，错误地返回了缓存的旧内容。

## 教训

1. **`read_file` 不是实时文件系统监控工具**：外部进程更新文件后，`read_file` 可能因缓存/去重机制拒绝返回新内容
2. **当 `read_file` 返回 "unchanged" 但你怀疑文件已更新时**：立即改用 `cat`、`xxd`、`od`、`jq` 等 shell 命令读取
3. **文件大小相同 ≠ 内容相同**：去重机制不能仅依赖文件大小判断
4. **在 Token 恢复场景中**：官方脚本恢复 Token 后，如需验证新 Token，优先使用 `jq -r '.farmToken' file` 或 `cat file` 而非 `read_file`

## 替代读取方法可靠性排序

| 方法 | 可靠性 | 备注 |
|------|--------|------|
| `jq -r '.field' file` | ✅ 高 | 直接读取并提取字段，不受缓存影响 |
| `cat file` | ✅ 高 | 标准 shell 命令，实时读取 |
| `xxd file` | ✅ 高 | 十六进制输出，适合验证完整内容 |
| `read_file` | ⚠️ 中 | 可能返回缓存内容，特别是文件大小未变时 |

## 相关会话

- `session-2026-06-29-naive-curl-token-masking.md` — 同一 session 中展示层脱敏导致的 Token 使用陷阱
