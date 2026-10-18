# Paperclip + Antigravity 审批闭环验收

## 结论

2026-10-17 在临时项目 `Antigravity Write Sandbox Lab` 的全新 Git worktree 中跑通：

1. Paperclip 创建隔离 Git worktree。
2. Antigravity 在 sandbox / `accept-edits` 模式下只创建任务指定文件。
3. wrapper 读取 Git 状态并通过 Paperclip API 将任务推进到 `in_review`。
4. Paperclip 生成用户 attention review 项，执行策略为单一 human approval，未配置 Codex stage。
5. 人工批准后，任务状态变为 `done`，`executionState.lastDecisionOutcome=approved`，审批阶段完成。

验收任务：`FIV-20`
隔离 worktree：`C:\Users\loez\AppData\Local\Temp\paperclip-approval-only-lab\.paperclip\worktrees\FIV-20-write-approved-clean-worktree-human-approval-smoke`
实际新增文件：`clean-approval-proof.txt`
文件内容：`CLEAN_WORKTREE_APPROVAL_OK\n`
最终 Paperclip 状态：`done / approved`
最终 attention：该任务不再出现在 attention 队列。

## 当前安全边界

- 只接受描述以 `[WRITE-APPROVED]` 开头的任务。
- 要求 Paperclip execution workspace 存在，并且必须是 `isolated_workspace + git_worktree`。
- 写入前拒绝 dirty worktree。
- Antigravity 通过 `--sandbox --mode accept-edits` 运行。
- `toolPermission` 为 `proceed-in-sandbox`，非全局无限权限。
- `allowNonWorkspaceAccess=false`。
- 禁止写 `.git/`，禁止 `git push/commit/reset/clean` 与 `gh pr merge`。
- Paperclip execution policy 只允许一个 approval stage，参与者必须是 user。
- 不配置 Codex 作为普通任务必经审核。

## 已验证文件

- `C:\Users\loez\AppData\Local\Paperclip\agy-process-write-review.ps1`
- `C:\Users\loez\.gemini\antigravity-cli\settings.json`

PowerShell 语法检查返回：`PS_PARSE_OK`。
Paperclip 健康检查返回：`ok 2026.1012.0`。

## 未声称的事项

- 没有把正式生产项目作为写入验收目标；本次只使用临时隔离项目。
- 没有验证邮件、桌面推送或飞书推送；已验证 Paperclip attention review 队列出现待审核项。
- FIV-18/FIV-19 是早期失败实验记录，不能作为当前闭环证据；FIV-20 才是最终干净验收记录。

## Claude Code 与 Codex Paperclip 接通验收（2026-10-17）

- Claude CLI 2.1.299 与 CC Switch Gateway `127.0.0.1:15721` 真实请求成功；Paperclip Claude agent `8f0c8e4c-d55c-4ef4-98f9-ea2b46692f40` 的 issue-assigned run `9b0ccf75-cbff-4578-9a7c-924c9aa011f1` 返回 `succeeded` / exit 0，原始日志含精确输出 `CLAUDE_PAPERCLIP_HEARTBEAT_OK`。后续两个 continuation/recovery run 虽然状态 `succeeded`，输出分别为“请告诉我你希望我执行什么任务”和“未提供 Paperclip 工具/API”，导致 disposition recovery 两次后 blocked。Board 已确认这是只读 smoke 并将 FIV-21 置为 `done`，recovery action 已清除。因此 Claude Provider/CLI 和 issue-assigned 执行已通过；heartbeat 后的 disposition/continuation 需单独注意，不能等同完整常规代码交付链已验收。
- Claude `C:\Users\loez\.claude\settings.json` 的 `ANTHROPIC_BASE_URL` 对齐 CC Switch `http://127.0.0.1:15721`（`/health` healthy），CLI smoke 返回 `CLAUDE_CCSWITCH_OK`；其他模型映射和 token 未改。
- Codex 托管 home 原 config 引用不存在的相对 `model_instructions_file`，导致 `os error 2`。仅修改 Paperclip managed home `C:\Users\loez\.paperclip\instances\default\companies\0a8707ff-5772-411c-928e-a6c5154db384\codex-home\config.toml`：移除该引用，model catalog 改用已有绝对路径，并将 sandbox 配置收紧为 `read-only`。普通用户 `~/.codex/config.toml` 未改；修改前备份在 `C:\Users\loez\AppData\Local\Temp\paperclip-codex-config-backup\config-20261017-214234.toml`。CLI smoke 返回 `CODEX_MANAGED_HOME_OK`。
- Codex issue-assigned heartbeat `ed22b564-82e1-4b4b-912b-44c33094fab9` 返回 `succeeded` / exit 0，并在 FIV-22 留下精确留言 `CODEX_PAPERCLIP_HEARTBEAT_OK`。FIV-22 已置 `done`，Codex agent 回到 `idle`，`dangerouslyBypassApprovalsAndSandbox=false`。另有一次无关联 issue 的 on-demand run 卡在 Paperclip Codex MCP/runtime continuation（遗留 `127.0.0.1:18060/mcp` 不可达 / task-bound connection 422）；已取消该 run，确认无 live runs、agent idle、相关 wrapper PID 退出。Codex MCP/runtime continuation 未单独修复。
- 所有 smoke 仅使用临时隔离项目 `Antigravity Write Sandbox Lab` / Git worktree 和只读任务；未验收正式项目写入。

## 2026-10-18 Claude/Codex 隔离复核

- Claude 新建隔离 issue `FIV-24`，首次 wake 为 `source=assignment, reason=issue_assigned`，执行 cwd 是临时 Git worktree；worktree `git status --porcelain` 为空。Claude run `3ed65112-47fd-42b0-b60f-10103b0b5004` `succeeded/exit 0`，但输出明确称当前会话没有 HTTP/Paperclip resolve 工具，未写回状态。随后两次 bounded disposition-repair automation run 也未写回，并把 issue 移交 board recovery；已按真实证据将 recovery resolve 为 `blocked`，FIV-24 最终 blocked、无 active recovery、无 live run，Claude Agent idle。不得称 Claude disposition 闭环已通过。
- FIV-24 原始提示虽然要求一次 API PATCH，但 Claude run init 实际提供 Bash 与 Paperclip MCP，而没有明确 `resolve` 工具；模型没有执行 Bash HTTP 请求。这将问题从“是否仅为提示矛盾”收窄到：Paperclip Claude 工具注入/提示映射是否足以支持原生 issue disposition，尚未验证。重试任务前须先确认可靠、被支持的 Paperclip 写回工具或适配层；不要再用仅有成功输出的任务自动触发重复恢复。
- Codex FIV-22 run `ed22b564-82e1-4b4b-912b-44c33094fab9` 的 `adapter.invoke` payload 明确为 `CODEX_HOME=C:\\Users\\loez\\.paperclip\\instances\\default\\companies\\0a8707ff-5772-411c-928e-a6c5154db384\\codex-home`，cwd 是独立 Git worktree；但 argv 明确含 `sandbox_mode="workspace-write"` 与 `sandbox_workspace_write.network_access=true`。因此该次不能证明只读隔离，不能放行正式项目。
- 源码核实：`adapter-codex-local/dist/server/codex-args.js:31-60` 中 `dangerouslyBypassApprovalsAndSandbox=false` 并不等于 read-only；没有 explicitSandbox 时适配器生成 workspace-write。应在独立 Agent 配置中显式传入已验证的 read-only CLI sandbox 参数并检查 run 的真实 argv，不要只改 `CODEX_HOME/config.toml` 的 `sandbox_mode`。
- Codex 真实 MCP 配置位置是 Paperclip 注入到 run 的 `CODEX_HOME` 下 `config.toml`；`codex-home.js:100-115` 说明 shared home 来源，`:282-301` 写入 Paperclip managed MCP block，`execute.js:517-530` 汇总运行时 gateways 并写入同一个 effective home。当前 managed config 的 `xiaohongshu` 表确认为 `enabled=false`，仍无法解释历史 run 为何尝试 `127.0.0.1:18060/mcp`；应检查该次执行瞬间的 managed config 与 config 快照，排查并发配置变更或其他 Codex config source，不能推定 disabled 已生效。
- Windows sandbox 限制已证实：`adapter-utils/dist/local-process-sandbox.js:282-289` 在非 Linux 上对本地 filesystem/network scope 直接抛出“currently supported only on Linux”；本机真实调用自检返回同一错误。因此 Paperclip `filesystemScope` 不是此 Windows 主机上可用的 Codex 安全边界。
- 多代理 Codex MCP/sandbox 源码复核子任务在 600 秒超时；本条结论来自本机只读源码与 run/API 证据，不把超时子任务当作成功审查。
