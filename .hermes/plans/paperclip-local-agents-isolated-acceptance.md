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
- Codex run 当时尝试连接 `http://127.0.0.1:18060/mcp`，但当前托管 `config.toml` 的 `xiaohongshu` 已为 `enabled=false`。历史错误来源还未查清，需核对对应运行时配置快照，不能假定 disabled 已约束运行时。
- Paperclip 本地 `filesystemScope` 对 Windows 不可用：实测返回 `Local process filesystem and network scopes are currently supported only on Linux.`

## 2026-10-18 Windows 短路径隔离 smoke 结果

- Paperclip 项目执行工作区的 `worktreeParentDir` 改为 `C:/pcwt`，原因是原路径叠加长分支名会触发 Windows Git：`fatal: '$GIT_DIR' too big`。
- 修改已通过 Paperclip 项目 GET 读回确认；主仓库与 Paperclip 主 checkout 均未改动，仍为 `main...origin/main`。
- FIV-29 的首次 assignment run `488c2c3a-6c21-48b1-b7f6-839a4e0a71b2` 成功返回精确字符串 `PAPERCLIP_ISOLATED_WORKSPACE_OK`，adapter 日志明确记录 `cwd=C:\pcwt`，实际命令为只读 wrapper，worktree 基于 `origin/main`，任务临时目录已清理。
- 验收 worktree 初始干净，HEAD 等于 `origin/main`；结束后已删除该临时 worktree 和 `FIV-29-...` 主题分支，`C:/pcwt` 无残留目录。
- 后续 recovery run `b0095eb3-f7c3-4e35-83fb-8f9443715d0e` 因旧 wrapper 未写回 issue disposition 被人工取消；这不否定 worktree 隔离结果，但说明该 wrapper 只能证明启动/隔离，不能证明 Paperclip issue 生命周期闭环。
- 本次仅证明 Windows 短路径下的 Antigravity 标准 process smoke 能创建并运行隔离 worktree；不证明 Windows sandbox scopes 可用，不放行 Claude/Codex 正式项目写入，也不证明任何 Agent 可直接写 `main`。

## 建议的最小复验顺序
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

## 2026-10-18 后续复核

- FIV-27 的遗留 `stranded_assigned_issue` recovery 已通过 Paperclip recovery API 明确收尾为 `blocked`；读回确认 `activeRecoveryAction=null`，没有因此重试低信任 Agent，也没有放宽 `low_trust_requires_sandbox_environment` 保护。
- Paperclip managed checkout 原先落后远程 `main` 一个提交；已执行 `fetch` + `pull --ff-only`，现在 HEAD 与 `origin/main` 同为 `6e8583a`，工作区干净，`git diff --check` 通过。
- 已知 FIV-29 取消运行时遗留的精确进程 PID `32436`（`cua-driver.exe`）及子 PID `32144`（`conhost.exe`）仍存在；对这两个 PID 的精确 `taskkill /F` 返回“拒绝访问”。它们不属于当前 Paperclip live run，未改动仓库；后续需通过 Paperclip/Windows 重启或管理员可见清理路径解决，禁止按进程名批量误杀当前桌面 CUA。
- 当前仍未开放 Claude/Codex 正式项目写入。下一阶段必须先修复或验证：只读 wrapper 的 disposition 写回、Windows process adapter 子进程回收、Codex 实际只读 argv，以及 Claude 的可验证权限边界。

## 2026-10-18 wrapper 与 Windows 子进程回收修复

- 只读 wrapper `C:\Users\loez\AppData\Local\Paperclip\agy-process-readonly.ps1` 已增加 run-scoped `X-Paperclip-Run-Id` 头，并在 PATCH 后 GET 验证 issue 终态、active run 和 recovery；写入审核 wrapper 同样增加该头，并验证 `in_review / pending / approval`。
- 两个 wrapper 在启动 CLI 前调用本地 `paperclip-job-guard.ps1`。守卫使用 Windows Job Object 的 `KILL_ON_JOB_CLOSE`，创建/配置/绑定失败即拒绝启动，避免未验证的子进程链继续运行。
- FIV-30 真实只读回归：issue 进入 `done`，run 成功，recovery 为空，Agent 回到 `idle`，并使用 `C:\pcwt` 隔离 worktree；结束后 worktree、主题分支和临时目录已清理。
- FIV-31 无 Job Object 对照 smoke 复现失败：Paperclip 父进程退出但子 PowerShell 进程仍存活；该测试的精确 PID 已清理，issue 保留为 `blocked` 证据。
- FIV-32 真实 Paperclip 集成验收通过：Job Object 接入后取消 run `83ecb900-b604-42b9-9a05-0b19c25b14e2`，父 PID `21892` 与子 PID `13988` 均退出；run 为 `cancelled` 且 `executionCancellation.state=acknowledged`，`live-runs=0`、`activeRecoveryAction=null`。FIV-32 因人为取消而保留为 `blocked`，不把取消测试误报为业务成功。
- FIV-32 一次性 Agent 已 `terminated`，四个 smoke 临时文件已删除；正式仓库没有 worktree/业务改动。复核时旧 PID `32436/32144` 已不存在。
- Job Object 只解决 wrapper 进程树回收，不等于 Windows OS sandbox；仍不能替代 Claude/Codex 的实际 argv、cwd、网络和文件权限验收。

## 当前安全结论（修复后）

- Antigravity wrapper 的 disposition 写回和 Windows wrapper 子进程回收均有真实 smoke 证据；这不等于正式项目写入已获准。
- Claude/Codex 正式项目写入继续关闭。Codex 仍需显式只读 argv 验收，Claude 仍需可验证的权限边界验收。
- Paperclip API 短暂停止后已恢复；最终读回为 Agent `terminated`、FIV-32 `blocked`、无 live run、无 active recovery。后续重新测试必须新建一次性 Agent，不复用 terminated Agent。
