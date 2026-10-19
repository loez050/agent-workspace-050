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

## 2026-10-18 历史 smoke workspace 清理

- Paperclip managed checkout 已改用真实路径 `C:\Users\loez\.paperclip\instances\default\projects\0a8707ff-5772-411c-928e-a6c5154db384\270eca47-efc0-4a7a-8d1e-1a3d0e315cb8\agent-workspace-050`，并已快进同步到 `4eec70a`；此前误查的 `companies\\<company>` 目录不是 Git checkout。
- FIV-21、FIV-22、FIV-23 的 Issue 均为终态 `done`、workspace readiness 为 `ready`、工作区干净且已合并；通过 Paperclip archive API 归档后，实际 worktree 和对应分支均已删除，并逐项读回确认。
- FIV-16 是无物理目录的共享 workspace 会话，已按 `ready_with_warnings` 归档记录；没有删除共享基础设施。
- FIV-18、FIV-19、FIV-20 保留：物理 worktree 仍有唯一未跟踪的 `proof.txt`、`proof-final.txt`、`clean-approval-proof.txt`，不得在未另存验收依据前删除。
- FIV-24 保留：Issue 为 `blocked` 且仍有真实 Claude smoke worktree；Paperclip close-readiness 阻止破坏性关闭。
- FIV-26、FIV-28 保留：Issue 为 `blocked`，Paperclip 将其判定为非终态并拒绝破坏性关闭；当前物理目录已不存在，正式 Git worktree/分支列表没有残留。
- 当前正式仓库和 Paperclip managed checkout 均干净，`live-runs=0`，历史 smoke 清理没有触碰 `main` 或正式业务文件。

## 2026-10-18 Codex 显式只读 argv smoke

- FIV-33 使用一次性 `codex_local` Agent `ce049812-34b0-4d8f-8147-ab03132de969` 和隔离 Issue `FIV-33`；验收结束后已终止该 Agent，未用于正式项目。
- 适配器配置显式携带 `--sandbox read-only`，并关闭测试所需的托管 MCP/插件；`dangerouslyBypassApprovalsAndSandbox=false` 保持不变。适配器源码与运行记录均确认没有使用 `dangerously*` 绕过参数。
- 首次 assignment run `6a95398b-50e6-4ca0-960a-a5fc5282fc76` 成功返回 `CODEX_READ_ONLY_SMOKE_OK`；Paperclip 事件记录的 cwd 为 `C:\\pcwt\\FIV-33-read-only-codex-explicit-read-only-argv-smoke`，不是正式 checkout。
- 该 run 的工作区从 `origin/main` 创建，初始 HEAD 为 `369dd6c`；结束时 `git status --short` 为空、ahead/behind 均为 0、没有未跟踪文件，未发现文件修改。
- Codex 输出提示 `model_reasoning_effort` 与 `plugins` 两项配置被当前 CLI 忽略；这不影响本次只读字符串 smoke，但说明不能把这些配置项当作已生效的权限证据。
- Paperclip 运行环境仍报告 `PAPERCLIP_RUNNER_NETWORK_ACCESS=enabled`；本次任务没有调用 shell、MCP、插件或网络工具，因此不证明网络隔离，也不证明 Windows OS sandbox。只证明显式只读参数链和隔离 worktree 启动链可用。
- 运行期间误触发一次 disposition-repair automation；已取消后续 run，读回 `live-runs=[]`、recovery 为空、Issue=`done`、Agent=`terminated`，没有留下活动进程。
- FIV-33 execution workspace 已按 Paperclip close-readiness 归档；实际 worktree 和主题分支均已删除，正式仓库、managed checkout 和 `main` 未改动。

## Codex 只读结论

- Codex 的显式只读参数链通过一次性隔离 smoke；旧 FIV-22 的 `workspace-write` 记录仍不能作为只读证据。
- 这次结果不放行 Codex 正式项目写入：Windows runtime sandbox、网络隔离、完整权限边界和人工 approval/merge 流程仍未完成业务级验收。


## 2026-10-19 真实 Claude 只读/隔离写入验收与历史记录收尾

- Claude 只读 smoke FIV-34 在一次性 Agent + 隔离 worktree 中通过；显式 `--permission-mode plan --permission-prompts none --tools "" --safe-mode --no-session-persistence --strict-mcp-config`，真实 run 返回 `CLAUDE_READ_ONLY_SMOKE_OK`，cwd 为 `C:\pcwt\FIV-34-read-only-claude-explicit-plan-tools-off-argv-smoke`；结束后 Agent terminated、Issue cancelled、worktree/branch 删除、无 run/recovery。该 run 不证明 Windows OS 或网络隔离。
- Claude 隔离写入 smoke FIV-35 通过：一次性 Agent `Claude Isolated Write Smoke` 实际 argv 有 `--permission-mode acceptEdits --permission-prompts none --tools Read,Edit,Write --strict-mcp-config --disable-slash-commands`，`dangerouslySkipPermissions=false`；`adapter.invoke` 未注入 `--dangerously-skip-permissions`。日志记录 `permissionMode=acceptEdits`、仅 Edit/Read/Write、`mcp_servers=[]`、`CLAUDE_ISOLATED_WRITE_SMOKE_OK`。
- FIV-35 任务只在 `C:\pcwt\FIV-35-write-smoke-claude-isolated-accept-edits-proof` 新建指定 proof 文件，内容精确为 `CLAUDE_ISOLATED_WRITE_OK`；运行后工作区无 tracked/untracked 改动。Issue 一次性取消、Agent terminated，workspace 归档、分支与 worktree 已删除，精确 PID 已退出。
- 正式 Claude Developer 与 Codex Reviewer 均 idle；Paperclip live-runs=0。正式仓库和 managed checkout 仍为 `58c31400078e86ec1d084e8b4ac2165229234959`，main 与 origin/main 同步且干净。
- 本地 Paperclip runner network access 仍 enabled，Windows filesystem/network scopes 仍不可用。验收只证明 Claude CLI 参数链、隔离 worktree 写入和 Job Object 进程回收；不证明 Windows OS sandbox、AppContainer、Hyper-V VM 或网络隔离，不能据此开放正式项目 Agent 写入。
- 2026-10-19 对旧测试记录 FIV-19、FIV-20、FIV-24、FIV-26、FIV-28 做了带证据的归档：记录各自验证结果/失败状态的审计评论；FIV-19/24/26/28 终态 `cancelled`，FIV-20 保留已通过状态 `done`；五条均无 live run/recovery，Paperclip workspace 已 archive。FIV-19/20 proof 文件原内容与 SHA-256 已先核验并写入 Paperclip 审计评论后才删除；FIV-19/20/24 临时 worktree、主题分支均不存在。FIV-26/28 物理目录本已不存在，归档时 Paperclip 设置了无法解析仓库路径的 cleanupReason；managed checkout 中没有相应分支/worktree。
- 旧 smoke 收尾的经验：即使归档 API 返回 200，也必须读回 cleanupReason 并独立检查物理 worktree/branch。只在 readiness 允许破坏性关闭后归档；若物理路径已被先行清理，分支 cleanupReason 不能仅靠归档成功推断为已处理。


## 2026-10-19 旧 Antigravity 审核 Agent 故障和 Linux sandbox 边界

- `Antigravity Write Reviewer` 一次旧 assignment run `dd15eb9a-3772-45a4-9f11-db587ab20fa6` 的真实根因已从 Paperclip run result/log 证实：任务 `FIV-26` 标题为 `[READ-ONLY] ...`，wrapper 要求 issue 标题以 `[WRITE-APPROVED]` 开头，因此按设计 fail-closed 抛错并 exit 1；不是密码、CLI 缺失或 Windows 文件系统错误。wrapper 的准入行为符合安全约束，不应为让旧只读任务通过而放松。该 issue 仍 blocked；不通过重新运行或直接改成 `[WRITE-APPROVED]` 来掩盖历史失败。
- Paperclip 的失败 Agent 状态可被 PATCH 为 `idle`，但 GET 读回仍显示旧 `errorReason=Process exited with code 1`，runtime-state 也保留 lastRunStatus=`failed` / lastError；不能通过改 status 假装旧错误消失。后续只应在隔离环境用明确 `[WRITE-APPROVED]` + 人工 approval 的任务验证适当链路，或停用不再使用的测试 Agent；不可直接触碰正式项目。
- 本机可见 `Ubuntu-22.04` WSL2，内核 `6.6.114.1-microsoft-standard-WSL2`，用户 UID 1000；Paperclip adapter `local-process-sandbox.js` 明确仅 `process.platform === linux` 时可建 sandbox，使用 `bwrap --unshare-pid --unshare-ipc --unshare-uts`，workspace filesystem 用 tmpfs 根目录并显式 ro/rw bind，network scope 用 `--unshare-net`。本机 WSL 当前缺 `bwrap`，尚未证明 WSL 内能成功创建所需 user/mount/network namespaces 或 bwrap；因此不能声称 WSL sandbox 已具备。
- 项目所在 `/mnt/d` 实际是 DrvFS (`findmnt`: `drvfs;path=D:\`)，不是 WSL 原生 Linux 文件系统。不能把 Windows 主仓库直接经 `/mnt/d` 作为 bwrap writable workspace 来承诺 POSIX ACL/权限隔离；安全候选路径是另建 Linux 原生 ext4/VHDX 内的专用 clone，并用 Paperclip/Linux runner 在该 Linux filesystem 创建 isolated worktree，再逐步验证 bwrap read/write/network deny 子进程和真实 Agent run。此候选路径仍需工具安装、namespace 能力验收与实际端到端测试，目前没有启用或安装任何内容。
- Windows runner 仍没有 OS 级 filesystem/network sandbox 实证；Windows Sandbox optional feature 查询因当前非管理员无法确认，不能从 `HypervisorPresent=True` 或 `vmcompute` running 推出 Windows Sandbox 已安装。


## 2026-10-19 续查：旧审批记录与 WSL sandbox 仍需谨慎

- 重新读取旧 FIV-19/FIV-20 评论发现：FIV-20 保留有已完成人工审核的原始评论与当前 `done` 状态；FIV-19 只有 wrapper 的审批请求评论，后续 board 表示 proof 已人工核验的评论未在 Paperclip comments API 读回中出现。为避免丢失唯一审计依据，FIV-19 的 proof 文本与 hash 已先写入不可逆的 Paperclip audit comment 后物理删除；FIV-20 原人工批准状态仍保留，另有 proof hash 审计评论。FIV-19/20/24 临时 worktree/branch 现均不存在，FIV-26/28 无目录且主 managed checkout 无对应引用。归档 workspace 返回 200；FIV-26/28 读回 cleanupReason 为找不到仓库根目录，故依靠独立物理目录、分支与 worktree 检查确认没有目标残留，而非把 API 200 当物理清理成功。
- WSL Ubuntu-22.04 的只读验证确认 WSL2 内核、`/home` 为 ext4、项目 `/mnt/d` 为 DrvFS；当前 `bwrap` 缺失。WSL 一般用户成功执行 `unshare --user --map-root-user --mount --pid --fork true` 与 `unshare --user --map-root-user --net true`，`sudo -n true` 返回成功，说明可进一步做 namespace/bwrap 资格测试；但 Paperclip adapter 的 bwrap 启动尚未验证，WSL Paperclip runtime/CLI/认证链也未建立。此处只证明 Linux 内核的两类 unshare syscall 对该用户可用，不等于 bwrap sandbox或真实 Agent filesystem/network confinement已验收。不得继续引用“unshare未证明”作为当前缺口；仍应明确 `bwrap` 缺失、真实 Adapter run 未验证。
- 未安装 bwrap、未启动 WSL Paperclip、未改系统策略或权限，也未把 Windows 主 checkout 放到 WSL `/mnt/d` 作为受限 writable workspace。任何 WSL方案应使用 Linux ext4 中的专用 clone/worktree，并先读写探针验证 bwrap实际边界，再启动真实 smoke。


## 2026-10-19 审批审计记录补充与当前 CLI 健康复测

- 通过 Paperclip `GET /issues/{id}/comments` 复核：FIV-20 有原始人工审核确认评论，当前仍为 `done`；FIV-19 有 wrapper approval request 和本轮追加的 proof 内容/ SHA-256 审计评论，当前为 `cancelled`。FIV-19/20/24 物理 worktree 和对应 refs 均不存在；FIV-26/28 目录不存在、managed checkout 无对应 branch/worktree；所有目标 Issue 终态、无 activeRun/recovery、workspace 已 archive。
- 旧 `Antigravity Write Reviewer` 的 status 可通过 PATCH 变成 idle，但 Paperclip 仍保留 `errorReason=Process exited with code 1` 和 runtime-state `lastRunStatus=failed`/`lastError`；错误消退未被验证，不能把该 Agent 报为健康。禁止为刷新状态而复用/重跑旧 blocked `[READ-ONLY]` Issue。
- 重新做了非写入 Claude CLI readiness：Claude Code `2.1.299`；本地 CC Switch `/health` HTTP 200，`claude auth status --text` 显示 token 类型与 Base URL 为本机网关（不记录任何密钥）；在 no-tool/plan/单轮/no-session 模式下真实请求返回精确 `CLAUDE_CCSWITCH_CURRENT_OK`，exit 0。CLI 额外输出当前 gateway 对 Claude auto-mode classifier billing 的兼容性提示；本次只读 smoke 成功但不验证 Auto Mode 计费能力。


## 2026-10-19 最终状态复核和剩余阻塞

- Paperclip 全局 live-runs=`0`；FIV-19/20/24/26/28 五个历史 smoke workspace 都读回 `archived`。FIV-26/28 archived 记录保留 branch cleanup failure 文本，但 Windows 主 checkout、managed checkout、专用临时仓库的 Git worktree/refs 和其原 workspace 路径均查无目标残留。原 proof 文件已在删除前核对内容/hash；FIV-20 的人工批准原评论仍可读，FIV-19 的证明材料在 archive audit comment 中可读。
- Claude Developer 与 Codex Reviewer 当前 idle；Antigravity Write Reviewer 当前 status idle 但 `errorReason=Process exited with code 1` 和 runtime `lastError` 仍保留，因此不视作已修复/健康；不复用旧 `[READ-ONLY]` blocked Issue。
- 项目记录已推送 GitHub 私有仓库并让 Paperclip managed checkout fast-forward；正式仓库、managed checkout、`origin/main` 当前 SHA 同为 `37655c60c0bf9335dc9c541807742dec7bb6ca9c`，均干净且 `git diff --check` 通过。
- 本地 Claude CLI 当前是 `2.1.299`，CC Switch `/health` HTTP 200，认证类型为 `ANTHROPIC_AUTH_TOKEN` 且 Base URL 为 `http://127.0.0.1:15721`。显式无工具 `plan`、单轮、无会话保存的真实请求返回唯一预期 token `CLAUDE_CCSWITCH_CURRENT_OK`，exit 0；stderr 有 gateway 与 Auto Mode classifier billing 兼容性提示，和本次直接 CLI 请求成功是两个独立结果。
- Windows Sandbox optional-feature 状态因非管理员无法确认；WSL2 user/mount/pid/net unshare 探针通过但 bwrap 缺失，且未建立 Linux Paperclip runner。因此 OS 文件/网络隔离仍未验收，正式 Claude/Codex 写入保持关闭。

## 2026-10-19 当前看板与历史 smoke 收尾复核

- 通过 Paperclip API 先逐项确认无 `activeRun`、无 `activeRecoveryAction`，再把历史一次性阻塞 smoke FIV-11、FIV-25、FIV-27、FIV-31、FIV-32 统一转为 `cancelled`；每条 Issue 都读回状态并确认追加的关闭审计评论存在。没有重跑旧 Issue，没有删除历史 run/comment，也没有触碰正式项目配置。
- 当前公司 Issue 统计：`done=12`、`cancelled=22`、`blocked=0`、`in_progress=0`、`in_review=0`；公司 `live-runs=0`，非归档 execution workspace 数量为 0。
- 当前保留 Agent 均为 idle：Codex Reviewer、Hermes CEO、Claude Code Developer、Antigravity Read-only Researcher、Antigravity Read-only Disposition Smoke；旧失败的 Antigravity Write Reviewer 已删除，不再复用其残留错误状态。
- CC Switch `127.0.0.1:15721/health` 当前 HTTP 200；正式仓库与 Paperclip managed checkout 均干净，HEAD、`origin/main` 同为 `ee95d6fa1613de636971d4ec62a6752cce8b5e25`，`git diff --check` 通过。
- 当前仍不能放行正式 Agent 写入：Windows runner 的 OS 文件/网络隔离未证明，WSL2 缺少 `bwrap`，且没有 Linux Paperclip runner。后续如要继续做 WSL 沙箱，只能在 WSL 原生 ext4 专用 clone 中先验证 `bwrap` 的文件和网络边界，再接入 Paperclip；不得把 `/mnt/d` 或 worktree 本身当成强沙箱。


## 2026-10-19 WSL2 原生 ext4 Bubblewrap 探针

- 未改系统级包管理器、未请求 sudo；在 `/home/hermes/.local/share/paperclip-sandbox` 用户目录安装了可回滚的 Bubblewrap 0.6.1 用户副本，下载包 SHA-256 为 `3f4f3f862a9b5ee774571fa1c0ef7c4b21a4f457f3acf5a149ade0345305d032`，入口为 `bin/bwrap`。
- 同目录安装 Node.js `v24.22.0` 用户副本，压缩包 SHA-256 为 `cc2f601cee82d9a5a233302fe307abc600727035fd7d2c3a3571755989e95008`；不覆盖 WSL 系统 Node `v22.22.2`，仅用于隔离探针。
- 直接调用 Paperclip 已安装 `adapter-utils/dist/local-process-sandbox.js` 构建真实 bwrap argv，使用 `filesystemScope=workspace`、`networkScope=deny`、`workspaceDir=/home/hermes/.local/share/paperclip-sandbox/probe-adapter-20261019/workspace`。
- 真实执行结果：`hidden=true`（workspace 外的 secret 不可见）、`BWRAP_ADAPTER_OK` 写入 workspace 成功、网络返回 `blocked-EAI_AGAIN`、退出码 0；探针结束后删除 probe 目录。
- 第一次直接执行完整生成 argv 暴露出 Paperclip 当前生成的 `/bin` symlink 在这台 WSL bwrap 上失败；不改 `node_modules`，在 `/home/hermes/.local/share/paperclip-sandbox/bin/bwrap-compat` 放置用户级、权限 `700` 的最小兼容 wrapper，只过滤四组失败的 `--symlink` 参数，其余 argv 原样转给 bwrap。通过 Paperclip builder 将 `filesystemSandboxCommand` 指向该绝对路径后，完整生成 argv 真实执行成功：`hidden=true`、workspace 写入 `BWRAP_COMPAT_OK`、网络 `blocked-EAI_AGAIN`、退出码 0。这个结果证明 Paperclip 当前完整 builder + 用户级兼容层的底层隔离探针可用，但**不等于真实 Paperclip Linux runner 或 Agent heartbeat 已验收**。
- WSL 现状：Node 22 不满足 Paperclip package 声明的 `>=24.11.0`；已准备 Node 24 用户副本，但 WSL 内尚未启动第二个 Paperclip server，也未迁移 Windows primary database/credentials。
- 回滚：删除 `/home/hermes/.local/share/paperclip-sandbox` 即移除本轮用户级 bwrap/Node/探针；不影响 Windows Paperclip、正式仓库、GitHub 或系统 apt。


## 2026-10-19 WSL Linux Paperclip staging结果

- 使用固定版本 Paperclip `2026.1012.0` 的 Linux npm 包在 `/home/hermes/.local/share/paperclip-linux/npm-global` 安装成功；使用独立 Node `v24.22.0`，没有复用 Windows `node_modules`。
- `test-drive --data-dir /home/hermes/.local/share/paperclip-linux/test-drive-data-20261019 --no-browser` 已初始化独立 embedded-Postgres 数据目录；doctor 输出 12 项通过，loopback/private、Node 24、数据库、日志和本地存储均可用。
- 该命令在启动 server 后因没有配置 provider credential 自动退出；没有启动成功后的持久 Linux Paperclip 控制面，也没有创建 Agent、Issue 或 heartbeat。生成的 secrets 仅留在 WSL 专用 test-drive 目录，未复制 Windows 凭据。
- 安全发现：WSL `/home` 内启动命令仍继承 `PWD=/mnt/d/Hermes里/多agent协作`；后续 Linux runner 必须显式 `cd /home/...`，并把 cwd、数据、日志、workspace 与配置都限定在 `/home`，不能只依靠词法路径。
- WSL 到 Windows `127.0.0.1:15721` 当前探测为 connection refused；WSL 默认网关和 `host.docker.internal` 对该端口也超时。`--unshare-net` 下回调到 Windows CC Switch/Paperclip 更不应假设 localhost 可达。下一步必须先解决 provider/API 的 Linux 可达链路，再启动真实 Linux heartbeat。
- 现有 Windows Paperclip 保持唯一运行控制面；当前 live-runs=0、非归档 execution workspace=0、issues 仅 `done=12/cancelled=22`，正式仓库和 managed checkout 均干净同步。
