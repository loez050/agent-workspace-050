# Paperclip 本地 Agent 隔离验收追加记录（2026-10-18）

## 已核实证据

### Claude Developer
- 新 issue FIV-24 首次由 `source=assignment, reason=issue_assigned` 触发；run 为 `3ed65112-47fd-42b0-b60f-10103b0b5004`，`succeeded/exit 0`。
- cwd 是临时 Git worktree `C:\Users\loez\AppData\Local\Temp\paperclip-approval-only-lab\.paperclip\worktrees\FIV-24-read-only-claude-paperclip-disposition-smoke-2026-10-17`；`git status --porcelain` 为空。
- Claude 输出称当前会话无 HTTP/Paperclip resolve 工具，未写回状态。两次自动 disposition-repair run 同样未完成；不能将它们算作 disposition 成功。
- 已停止重试循环，将 recovery 处理为 `blocked`。最终 issue `blocked`、active recovery 为空、无 live runs、Claude Agent `idle`。不能称 Claude Paperclip disposition 闭环已通过。
- 原始提示要求一次 API PATCH；但本轮日志中的 Claude 初始化包含 Bash 和 Paperclip MCP，却未见专用 issue resolve 工具。下一轮前必须先确认可支持且实际注入的状态写回路径；避免再以只回传文字的任务自动触发重复恢复。

### Codex Reviewer
- FIV-22 run `ed22b564-82e1-4b4b-912b-44c33094fab9` 曾成功留言，但启动参数真实包含 `sandbox_mode="workspace-write"` 与 `sandbox_workspace_write.network_access=true`；此 run 不证明只读边界，也不得用于正式项目写权限验收。
- `adapter-codex-local/dist/server/codex-args.js:31-60` 表明 `dangerouslyBypassApprovalsAndSandbox=false` 并不会自动给 read-only；未显式指定 sandbox 时适配器仍生成 `workspace-write`。
- FIV-22 实际 `CODEX_HOME` 是 Paperclip 公司托管目录：`C:\Users\loez\.paperclip\instances\default\companies\0a8707ff-5772-411c-928e-a6c5154db384\codex-home`。MCP 需检查此目录下 `config.toml`，并核对 run 时实际 `CODEX_HOME`。
- Codex run 当时尝试连接 `http://127.0.0.1:18060/mcp`，但当前托管 `config.toml` 的 `xiaohongshu` 已为 `enabled=false`。历史错误来源还未查清，需核对对应运行时配置快照，不能假定 disabled 已约束运行时。
- Paperclip 本地 `filesystemScope` 对 Windows 不可用：`adapter-utils/dist/local-process-sandbox.js:282-289` 在非 Linux 抛出 “Local process filesystem and network scopes are currently supported only on Linux.” 本机实测自检返回相同错误。
- Codex 托管目录曾有缺失 instructions 路径错误；本轮确认当前 `config.toml` 不再含 `model_instructions_file`，但仍未证明新的 issue-assigned run 已无其他配置错误。

## 2026-10-18 Paperclip issue 生命周期源码补充

- 第三方只读审查子任务也超时；它在 Windows 下误选了 Desktop 根目录做 broad search，随后搜索/网络请求反复阻塞。未接受其超时作为独立结论。只采纳本机已验证安装源码。
- 本机 `@paperclipai/shared/dist/validators/issue.js:570-631, 664-673`：创建 issue 至少要有非空 `title` 或 `description`；关联项目和 assignee 可以显式指定。创建时省略 status，若有 agent/user assignee 则默认 `todo`，否则 `backlog`（537-568）。
- 本机 `@paperclipai/server/dist/routes/issues.js:8432-8445`：除 onboarding 首任务外，普通 issue create 在响应前会排队 `reason=issue_assigned, mutation=create` 的 assignment wake。不要再额外 POST heartbeat/wakeup；以第一次 assignment run 作为验收对象。
- 本机 `@paperclipai/server/dist/services/run-liveness.js:267-290`：issue 已 `done/cancelled` 时 liveness=`completed`；run succeeded 但 issue 仍 `in_progress` 时，有 concrete evidence 会 `advanced`，没有 evidence 但有 useful output 则 `needs_followup`。因此“模型说完成”或单条评论不是最终 disposition。
- 本机 `@paperclipai/server/dist/services/recovery/successful-run-handoff.js:259-317, 319-390`：有效处置需明确推进到 `done/cancelled`、有负责路径的 `in_review`、有 owner/action 的 `blocked`，或明确 delegation/continuation；评论、文档或总结只能作支持证据。补救 wake 最多一次并有重复/恢复保护，不能通过反复唤醒规避。
- Claude adapter 确实把 Paperclip run token 和 API URL 注入 CLI 子进程（`adapter-claude-local/dist/server/execute.js:87-89, 159-174`）；但本次未核实该 direct CLI prompt 是否自动包含可用的 API 写入说明。可安全验证时，任务应明确允许仅使用当前 run 注入的环境变量访问本机 Paperclip API，使用隔离 issue、无工作区写入，执行一次可核验的合法状态更新，然后立即结束。

### 建议的最小复验顺序
1. 先 GET 核实测试 Agent 可 invokable、无 live run/recovery；选专用空白 Git 项目/隔离 worktree。
2. 新建唯一测试 issue，显式指定 `title`、`description`、`projectId`、`assigneeAgentId`、`status=todo` 和 `executionWorkspaceId`；创建动作会触发 assignment wake。不得并发重复 wake。
3. Prompt 明确允许完成一次 Paperclip issue disposition；禁止修改 worktree；清楚指定完成后 `done`（或预期合法处置）并报告。不能同时禁止全部工具又要求 API 写回。
4. 读回首次 assignment run 的 wake reason、实际 `cwd`/argv/环境注入（不得打印 token）、run 日志、issue status/comment、recovery 队列、agent runtime、live-runs、Git diff/进程。通过条件：真实 disposition、issue 终态、无自动重试循环、无改文件、Agent 空闲且无残留进程。
5. 若 API 状态修改被拒绝或 Claude 没有可用的 HTTP 工具，只收集失败证据并标记隔离 issue `blocked`；不要人工替代写回后把 run 说成通过。

## 安全结论

- Claude 与 Codex 都尚未通过足以放行正式项目写入的完整验收。
- Codex 下一步需在隔离测试 Agent 中显式设置只读 sandbox 参数、读回 Paperclip Agent 配置、创建全新 issue，并从 `adapter.invoke` 日志核实实际 argv/cwd/CODEX_HOME；在 Windows 不依赖 Paperclip `filesystemScope`。
- Claude 下一步先查明可用的 Paperclip 原生状态写回工具或 Adapter 机制，再做一次性隔离测试；不能靠任务正文指示 Bash PATCH 来臆测工具链已通。
- 不要用普通 `~/.codex`、repo 配置或托管 home 中的 sandbox 声明，代替 run 实际 argv 和 Windows 执行隔离的验证。
- 曾有敏感 provider 配置字段出现在工具输出；已不在此计划中复写其值。后续日志与汇报保持脱敏。

## 后续停止条件

- 若新 run 的实际 Codex argv 仍为 `workspace-write`、出现 `dangerously*` 绕过、cwd 不是临时 Git worktree，立刻停止验收、不在正式项目运行。
- 若 Claude 再次只有模型文本、未能写入或完成明确 disposition，停止自动 retry，读 recovery/run 证据后由 board 安全收尾。
- 每轮结束读回 issue、run、recovery、Agent、live-runs，并确认测试 worktree 无意外改动。
