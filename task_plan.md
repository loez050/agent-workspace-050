# Paperclip + Antigravity 稳定接入

## 目标
让 Paperclip 通过安全的 `process` 适配器调用本机 `agy`。当前只读/计划模式，不开放写入。

## 阶段
- [complete] 1. 检查 Paperclip、Agent、process 契约及社区方案
- [complete] 2. 排除不安全社区 Antigravity Adapter
- [complete] 3. 建立动态只读 wrapper，通过 run→issue API 获取任务
- [complete] 4. 两次 Paperclip heartbeat 验证任务上下文路由
- [complete] 5. 写入 smoke 风险评估与清理

## 安全边界
- 不动 Hermes、Claude、Codex 配置。
- 写入 smoke 只可作用于临时 Paperclip lab git clone/worktree；主 smoke repo 与正式项目保持不变。
- 不使用 `--dangerously-skip-permissions`。
- 允许写操作时使用 Antigravity `default` mode + OS sandbox + fail-closed wrapper。
- 每个写任务须配置 Paperclip QA Review stage + Board Approval stage，maxReviewRounds=1。
- sandbox AppContainer 未经验证时不派发任何写入任务；只单独测试 CLI 能否创建临时 proof file，之后立刻清理。


## 已验证方案
- Paperclip 2026.1012.0 无内置 `antigravity_local`，但内置 `process` 可运行本机命令。
- 本机 `agy` 1.3.5 已登录，代理通过 `127.0.0.1:7890`。
- Paperclip Process 将 `PAPERCLIP_API_URL`、`PAPERCLIP_API_KEY`、`PAPERCLIP_RUN_ID`、`PAPERCLIP_AGENT_ID` 注入子进程。
- wrapper 用 run ID 查询 `/api/heartbeat-runs/{runId}/issues`，再读取当前 Agent 被分派 Issue 的标题/描述。
- FIV-13 和 FIV-14 动态只读任务路由均成功；每个任务有两个 continuation/assignment heartbeat，都返回正确 issue ID/title。
- 正式 Agent `Antigravity Read-only Researcher` 使用 `process` + 本机 wrapper `C:\Users\loez\AppData\Local\Paperclip\agy-process-readonly.ps1`，状态保持 paused。
- Agent 权限被收紧：不允许创建 Agents、Skills、派发任务；wrapper 要求 issue description 以 `[READ-ONLY]` 开头，且强制 sandbox + plan。
- wrapper 的读取范围为本 run 关联 issue；先校验 id、active 状态和 assignee。模型返回内容会写回任务评论；不要提交秘密。


## 清理/状态
- 社区 adapter、npm 外部包和 extensions 目录均已清理。
- 临时 smoke Agents 已 terminated；临时 issues 已完成或取消；smoke workspace 已清理。
- 无残留 `agy.exe` 进程；Hermes/Claude/Codex 未改。

## 当前限制与写入 smoke 结果
- 社区 Adapter 已移除；本机 Paperclip 仍无内置 `antigravity_local`，正式只读 Antigravity Process Agent 保持 paused。
- FIV-15 写入尝试在 Paperclip 的 `agy` 子进程里因 OAuth/token exchange 认证超时失败；issue 后来被人工标 done，不算成功验收。
- 另一次直接 Agy CLI smoke 使用了 `--mode=default`，但 CLI 不支持该 mode；PowerShell `Set-Location` 到测试目录失败后仍继续，Agy 在原终端 cwd 创建了 marker 文件。Marker 已确认内容并立即删除。这个测试没有验证 Paperclip，也没有验证离开 workspace 的 sandbox containment。
- FIV-16 配了 Review→Approval policy，但 checkout/workspace 没读回为 isolated worktree，run 没有成功执行，issue 已取消。只验证过修改 issue status 会进入 review/approval stage 状态；不能据此断言写过程受保护。
- Windows Agy 版本合法 mode 为 `accept-edits`、`auto`、`plan`；非交互 Paperclip child 不能接收 TUI 中的逐文件 `default` 审批。
- 写入上线门槛仍未满足：Paperclip 认证/调用能成功 + Paperclip per-issue isolated worktree 实际 provision 成功 + Windows AppContainer sandbox 的外部写入探测被拒绝 + Issue Review/Board Approval 全流程实测。全部通过前保持 Agent paused，不派写任务。

## 错误记录
- `{{PAPERCLIP_TASK_SCRATCH_DIR}}` 不会在 process `args` 中展开；scratch 只提供临时目录，不保证含 task.md。
- 使用 Paperclip run→issue API 获取任务上下文；只接受 run 关联 issue、assignee 匹配、active 状态的唯一一条记录。
- Windows PowerShell `$matches` 是自动变量；集合另用 `$assignedIssues`。
- `agy --print` 的 prompt 必须保持单一参数，显式 `--print "$prompt"`。
- Paperclip 一次 assignment 可能带 continuation run；判断验收时要追踪所有 run 的终态。
