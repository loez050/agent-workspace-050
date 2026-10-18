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
