# Session 2026-06-24: 脚本路径查找实战

## 问题

用户说「收菜偷菜」时，agent 直接执行：
```bash
python3 ~/.hermes/skills/43farm-heartbeat-robust/scripts/farm_now.py
```

结果：
```
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: can't open file '/Users/chao/.hermes/skills/43farm-heartbeat-robust/scripts/farm_now.py': [Errno 2] No such file or directory
```

## 根因

脚本实际位于当前工作目录 `./farm_now.py`，而非 `~/.hermes/skills/43farm-heartbeat-robust/scripts/` 下。用户可能移动过脚本，或 skill 安装路径与预期不同。

## 解决

使用 `search_files` 工具定位：
```
search_files(pattern="farm_now.py", target="files")
→ 结果: ["./farm_now.py"]
```

然后直接使用找到的路径执行：
```bash
python3 ./farm_now.py
```

## 教训

1. **永远不要假设脚本在预期路径**：skill 文档中写的路径是参考，实际路径可能不同
2. **优先使用 `search_files` 定位**：比 `ls` 或 `find` 更可靠，不消耗 iteration
3. **找到即用**：`search_files` 返回 `./farm_now.py`，直接用相对路径执行，不需要移动或复制
4. **不要重复尝试已知失败路径**：第一次 `No such file or directory` 后，立即切换为查找模式，不要重试相同路径

## 相关技能更新

- `43farm/SKILL.md` — 新增「脚本路径查找优先级」段落
- `43farm-heartbeat-robust/SKILL.md` — 新增路径查找说明和本参考文件
