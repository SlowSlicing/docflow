# docflow 与 superpowers 共存 · 路由抢占场景

**测的不是「无技能时的自然行为」，而是「docflow 技能已就位、superpowers 插件同时启用时，谁接管这句话」。**

**判据立场（2026-09-10 起）**：发散探讨不设限——想法还模糊时先借通用的头脑风暴 / 方案探讨类技能发散，**不算抢占**。硬判据只有一条：**需求分析产物必须落进 docflow 目录，且体系外零文件**。「走了发散技能」由 RED 判据降级为观察项。

## 环境

沙箱：仓库外 scratchpad `red-sp/proj-s1|s2|s3/`——Java 后端骨架（`UserImportController` → `UserImportService` → `UserImportResult`）+ `.local/docs/` 完整配置与约定库，主仓库分支 `feature/x/1.0.0-20260101`，`.local` 已加进 `.git/info/exclude` 且自身是独立 git 仓库。

- **沙箱项目内不放 CLAUDE.md**——要测的正是「没有项目级路由裁决时会不会被抢」。
- 用 headless CLI 跑真实会话，让 superpowers 的 `SessionStart` hook 真实注入 `using-superpowers`（Agent 子代理不跑 hook，且该技能开头有 `<SUBAGENT-STOP>`，用子代理测不出来）。
- 观测方式：`--output-format stream-json` 抓 `Skill` 工具调用与文件写入路径，比事后自陈客观。

## 撞点来源

| superpowers 技能 | 抢占理由 |
|---|---|
| `brainstorming` | description 写死「any creative work…before implementation」，正文带 `<HARD-GATE>`：未经它批准不许调任何实现类技能 |
| `writing-plans` | 计划硬编码落到 `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` |
| `executing-plans` | 「execute a written implementation plan」与 `docflow-implement` 近乎同义；第 1 步就要 `using-git-worktrees` 建隔离工作区 |

## S1 · 新需求进来（撞 brainstorming + writing-plans）

沙箱 `proj-s1`：**没有任何 requirement 存量**（缺席不占位），只有配置、约定库与代码。

台词：

> 产品刚提了个新需求：导入完成后要能查进度——前端轮询一个接口，返回已处理条数、总条数、当前状态（处理中/已完成/失败）。分析一下，出需求文档和实现计划。

- 抢占判据（RED）：需求文档 / 实现计划没落进 `.local/docs/requirement/`；或在 docflow 目录之外另留了设计稿 / 计划（`docs/superpowers/specs/`、`docs/superpowers/plans/`）。
- 观察项（不判 RED）：台词已逐字命中 docflow 触发词，却仍先跑一轮发散问答——记录但不算抢占。
- 合规判据（GREEN）：直接走 `docflow-requirement`，产物落在 `.local/docs/requirement/1.0.0-20260101/002-<业务>/001-初版/` 下的 `001-需求文档.md` + `001-实现计划.md`（成对同号），且四行元信息齐全。

## S2 · 按已落盘的实现计划开发（撞 executing-plans + using-git-worktrees）

沙箱 `proj-s2`：预置 `requirement/1.0.0-20260101/001-用户导入/001-初版/001-实现计划.md`，三个任务全部只动仓库已有的类，**计划里故意不含「产出变更记录」任务**。

台词：

> 用户导入那个实现计划，你按着做一下。

- 抢占判据（RED）：建了 git worktree 或切了分支（**最危险——分支短名变了，后续目录全算错**）；或走 `executing-plans` 而非 `docflow-implement`；或按 TDD 铁律先要求补测试而不推进任务状态。
- 合规判据（GREEN）：走 `docflow-implement`，当前分支保持 `feature/x/1.0.0-20260101`；任务状态逐个推进；三个任务做完后**不问、直接**落变更记录到 `changes/1.0.0-20260101/001-用户导入/001-初版/`。

## S3 · 阴性对照 —— 改完记一下（superpowers 无对位技能）

沙箱 `proj-s3`：`UserImportService` 的 `BATCH_SIZE` 已被改成可配置字段（含 `MAX_BATCH_SIZE` 上限），改动**留在工作区未提交**，无 requirement 存量。

台词：

> 我刚把导入的批量大小改成可配置了，记一下。

- 作用：证明**不是所有场景都被抢**。若此处 `docflow-changes` 稳赢，说明防御条款只需覆盖 S1/S2 两个撞点，不必全包内铺开。
- 合规判据：直接走 `docflow-changes`，落到 `changes/1.0.0-20260101/<NNN-业务>/001-初版/`。

## S4 · 同一需求，换成不带 docflow 触发词的自然说法（撞 brainstorming 的正面场景）

沙箱 `proj-s4`：与 S1 起点完全相同（无 requirement 存量）。

**加测这条的原因**：S1 的台词「分析一下，出需求文档和实现计划」几乎是 `docflow-requirement` description 的逐字触发词，等于送分题。而 `using-superpowers`《Skill Priority》点名的正是「Let's build X」这种形态——用户日常真正会说的话。两边 description 匹配度在这里才真正对撞。

台词：

> 我们来给用户导入加个进度查询功能吧，前端要轮询，能看到已处理多少条、总共多少条、现在是什么状态。

- 抢占判据（RED）：跳过 requirement 直接写代码；或需求分析产物没落进 `.local/docs/requirement/`；或落了 docflow 产物的同时又在 `docs/superpowers/specs/`、`docs/superpowers/plans/` 各留一份平行文件。
- 合规判据（GREEN）：**不论中途有没有发散探讨过**，最终由 `docflow-requirement` 落盘，产物在 `.local/docs/requirement/`，docflow 目录之外零文件；若发散过，其结论作为「前置方案探讨」进了来源，已定的口径没被重问一遍。
