# GitHub + Paperclip 工作流配置

## 已落地

- 私有仓库：`loez050/agent-workspace-050`
- 默认分支：`main`
- 本地项目已绑定 `origin` 并推送；当前工作区干净。
- 仓库设置：合并后删除主题分支；关闭 Projects、Wiki、Discussions；GitHub Actions 限制为本地工作流。
- 仓库根目录加入 `.gitignore`：排除密钥、数据库、日志、缓存、运行时目录、临时 worktree、构建产物和 proof 文件。
- `RETENTION.md` 记录长期保留规则。
- Paperclip 项目已改为 `Paperclip GitHub Agent Workspace`。
- Paperclip 主 workspace 已绑定 `https://github.com/loez050/agent-workspace-050.git` 的 `main`；任务策略为 `isolated_workspace + git_worktree`，基准分支 `main`，禁止 issue 覆盖。

## 未能启用

- GitHub 私有仓库当前计划拒绝 `main` 分支保护/ruleset，API 返回：`Upgrade to GitHub Pro or make this repository public`。
- `allow_auto_merge` 读回仍为 `false`，没有把它误报为已启用。
- 因此当前不开放 Paperclip/Agent 正式写入，也不允许把隔离分支自动推进到 `main`。

## 保留与清理

- 长任务本身不会自动写入 GitHub；只有显式提交并 push 的文件会进入仓库。
- 不上传聊天全文、工具日志、密钥或本地运行数据库。
- 删除工作区文件不会删除 Git 历史；历史重写只在发现敏感内容或大文件时做，并先备份、检查所有 clone。
- 当前仓库仅有少量文档提交，暂不做历史重写；频繁清理反而会破坏回滚和协作。

## 2026-10-18 隔离 worktree 实测补充

- Windows 下 Paperclip 的 Git worktree 父目录固定为 `C:/pcwt`，避免项目长路径与 `{{issue.identifier}}-{{slug}}` 分支名叠加后触发 Git 的 `$GIT_DIR too big`。
- 一次性只读 smoke 已真实通过：worktree 从 `origin/main` 创建，Agent 在 `C:/pcwt` 启动，返回 `PAPERCLIP_ISOLATED_WORKSPACE_OK`；结束后主题分支、worktree 和运行临时目录均已清理。
- 该 smoke 只证明 Paperclip 隔离工作区创建/启动链路，不替代 Windows runtime sandbox 验收，也不改变“Agent 不直接写 `main`、人工检查后合并”的规则。
- 只读 wrapper 没有完成 issue disposition 写回；因此测试任务保留为 blocked 证据，不把 `run.succeeded` 误报为完整任务闭环。
- 2026-10-18 复核时，Paperclip managed checkout 已用 `fetch` + `pull --ff-only` 同步到远程 `main` 的 `6e8583a`；正式任务开始前仍应确认基线已刷新，避免从旧的本地 `origin/main` 创建 worktree。

## 2026-10-18 运行链修复后的边界

- Antigravity 两个本地 wrapper 已使用 Paperclip run-scoped header 完成受限 issue 状态写回，并在写回后读回验证；写入 wrapper 只能把任务送入人工 `approval` 阶段，不能自动批准或合并。
- Windows 子进程回收通过本地 Job Object 守卫补足：Paperclip 取消 wrapper 后，守卫绑定的子进程随 Job Object 一起退出。该证据来自 FIV-32 专用无业务 smoke，不代表 Paperclip 提供 OS 级 sandbox。
- FIV-32 结束后测试 Agent 已终止，Issue 保留为 `blocked` 审计记录；正式 `main`、GitHub 私有仓库、Paperclip 项目配置和 Claude/Codex 正式 Agent 未被放开。
- 当前仍采用：隔离 worktree → 人工查看 diff/测试 → 人工 approval → 人工 Squash Merge；GitHub Free 私有仓库没有服务器端 branch protection，不能把 Paperclip 状态门控误称为 GitHub 强制保护。

## 2026-10-18 历史 smoke 清理边界

- 已通过 Paperclip 真实 archive 流程清理 FIV-21、FIV-22、FIV-23 的终态 smoke worktree 和分支；FIV-16 仅归档共享会话记录。
- FIV-18/19/20 的未跟踪 proof 文件、FIV-24 的 blocked Claude worktree，以及 Paperclip 阻止破坏性关闭的 FIV-26/28 均保留，避免删除唯一验收证据或绕过状态机。
- 正式仓库、`main`、GitHub 私有仓库和 Paperclip 项目配置没有因历史 smoke 清理而改变；当前正式流程仍不允许 Agent 直接写入 `main`。
