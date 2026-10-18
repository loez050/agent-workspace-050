# Findings

## 当前官方/社区状态
- Paperclip v2026.1012.0 的内置适配器列表没有 `antigravity_local`；Gemini CLI 的旧 `gemini_local` 仍在列表中，但用户个人订阅流已迁到 Antigravity。
- 官方 Process adapter 可通过 API 配置任意同机命令，UI 下拉显示 Coming soon；仅运行命令、转发 stdout/stderr，不提供 session continuity、structured transcript 或模型用量统计。
- 社区 `@weslleycapelari/adapter-antigravity-local@1.0.0` 默认每次追加 `--dangerously-skip-permissions`，并且 Paperclip 真实任务中看到 agent 自建后台任务并等待，阻塞长时间运行；本地 adapter 包已移除。

## 写权限 smoke 结果与未解决门槛
- 写入边界实测未通过：一次 `Set-Location` 失败后 Agy 仍继续，并把 proof 写进外部 cwd；该测试无效，proof 已删除。不能据此声称 sandbox 能防止越界写。
- FIV-15 在 Paperclip 子进程内因 Google OAuth token exchange timeout 失败；不能通过跳过权限重试。
- FIV-16 Review→Approval policy 存储成功，但项目/issue workspace 配置没有读回为 per-issue isolated worktree；issue 被取消。Review policy 不是执行时写权限拦截。
- Windows Agy 的 headless `--mode=default` 不支持；支持 accept-edits/auto/plan。非交互 process 不能暂停等待 TUI diff approval。
- 因 Paperclip child credential、隔离 worktree、Windows AppContainer 边界均未验收，写入 Agent 保持暂停，不派发真实写任务。

## 真实只读接入验证

- `agy 1.3.5` 本机已登录；HTTP(S) 代理 `127.0.0.1:7890`。
- `agy --sandbox --mode plan --print` 独立只读问答可以正常回复。
- Paperclip 内置 Process 能传入 run-scoped identity；wrapper 用 `PAPERCLIP_RUN_ID` 获取准确关联的 Issue 并核对 `assigneeAgentId`，动态只读路由已在 FIV-13/FIV-14 成功。
- 动态 task flow 只在独立 wrapper 中实现，Process argv 固定指向 wrapper；任务正文不由 Paperclip 临时 scratch 自动写入，不能使用未展开的 `{{...}}` 占位符。
- 长期正式运行应保留自定义 wrapper，并把 `[READ-ONLY]` 前缀策略和 `--mode plan --sandbox` 固定在 wrapper 内；不要靠 Issue 文本自己声明安全/危险，也不要把安全边界放在普通 prompt 前缀上。



## 清理状态
- 社区 adapter 注册/安装包已移除；extensions 目录为空。
- 残留 agy 进程已结束。
- 社区 Antigravity agent 和旧 Gemini agent 已终止；临时 smoke agent 已终止。
- FIV-3/FIV-4 取消；FIV-5 setup_failed 后取消；FIV-6 process smoke 已 done。
- Hermes、Claude、Codex 设置没有修改。
