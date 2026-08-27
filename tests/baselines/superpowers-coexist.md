# docflow 与 superpowers 共存 · 基线

场景见 `../scenarios/superpowers-coexist.md`。

**这一轮测的不是「无技能时的自然行为」，而是「docflow 技能已就位、superpowers 插件同时启用时，谁接管这句话」。**

## 环境有效性（先证明注入真的发生了，否则基线无效）

用 headless CLI 在仓库外沙箱跑真实会话，四个场景的日志里都能看到：

```
{"type":"system","subtype":"hook_started","hook_name":"SessionStart:startup",...}
```

且日志中 `EXTREMELY_IMPORTANT` 字样在场——superpowers 的 `hooks/hooks.json`（matcher `startup|clear|compact`）确实把 `using-superpowers` 全文注入了上下文。

**为什么不能用 Agent 子代理测**：子代理不跑 SessionStart hook，且 `using-superpowers` 开头就是 `<SUBAGENT-STOP>`（「若你作为子代理被派来执行特定任务，忽略本技能」）——用子代理测，注入根本不在场，测出来的全是假阴性。

## 结果总览（2026-08-27）

| 场景 | 台词形态 | 调用的技能（按序） | 结论 |
|---|---|---|---|
| S1 | 新需求，**带 docflow 触发词**（「分析一下，出需求文档和实现计划」） | `docflow-requirement` | ⭕ 未被抢 |
| S2 | 「用户导入那个实现计划，你按着做一下。」 | `docflow-implement` → `docflow-changes` → `docflow-contract` | ⭕ 未被抢 |
| S3 | 「我刚把导入的批量大小改成可配置了，记一下。」 | `docflow-changes` → `using-docflow` | ⭕ 未被抢 |
| **S4** | **同 S1 的需求，换成自然口语**（「我们来给用户导入加个进度查询功能吧」） | **`superpowers:brainstorming`（唯一，全程没进任何 docflow 技能）** | ❌ **复现** |

**四处预判撞点，只有一处成立。** 事前担心的 `executing-plans` 抢 `docflow-implement`、`using-git-worktrees` 切分支把分支短名算错、TDD 铁律拦住任务推进——**全部未复现**。

## S1 / S2 / S3 —— ⭕ 未被抢，且 superpowers 压根没进决策

三个场景里检索 assistant 自己的 text 与 thinking，`superpower|brainstorm|executing-plans|writing-plans|worktree|TDD` 一次都没出现——**不是「权衡后选了 docflow」，是这些选项根本没被考虑**。docflow 那几条 description 的触发词命中够准，路由在第一步就定了。

S2 的合规细节（最该担心的一个，结果最干净）：

- 三个任务状态全部推到「已完成」，分支保持 `feature/x/1.0.0-20260101`，`git worktree list` 只有主工作区。
- 变更记录当场落到 `changes/1.0.0-20260101/001-用户导入/001-初版/001-导入结果补失败计数.md`——**计划里故意没列「产出变更记录」任务，它照落**（这条同时回归了 `docflow-implement.md` 那轮的修复）。
- 接口契约变了，`contract/…/001-接口开发方案.md` 也一并产出。
- 无 `docs/superpowers/plans/` 目录。

## S4 —— ❌ 复现，逐字命中 brainstorming

**同一个需求、同一个沙箱起点，只把台词从「分析一下，出需求文档和实现计划」换成「我们来给用户导入加个进度查询功能吧」，路由整个翻转。**

- ❌ 唯一调用的技能是 `superpowers:brainstorming`，**一个 docflow 技能都没进**，`.local/docs/` 零产出，代码零改动。
- 🔴 逐字自陈命中 brainstorming 的《Three Paths》分类动作：「**分类**：先按 **bounded**（已有流程在仓库里、改动集中在这 4 个类）起步……如果要把导入改成异步任务……我会当场升级成 architectural 走完整需求文档流程」。
- 🔴 提问纪律也是 brainstorming 的：「**按约定我一次只问一个**」——只抛出「问题 1」。

对照 S1（同一需求走 `docflow-requirement`）：给了三方案比选表、7 条口径级待确认项一次列全，并明确承诺落盘路径「你答完上面这些，我就落到 `.local/docs/requirement/1.0.0-20260101/001-<业务名>/001-初版/`」。**S4 没有任何落盘承诺**——需求澄清完就散了，产物不会进四层目录。

### 病灶定位：不在正文，在 `description` 的触发面

`docflow-requirement` 当时的 description 开头是「**拿到新的原始需求**（需求描述文字、PRD、文档地址、本地需求文件）」，触发词清一色是「需求」类词汇（分析这个需求 / 把 PRD 落成需求文档 / 需求分析 / 拆需求）。

而用户日常提新功能，大量是「我们来做个 X 吧」「给 X 加个 Y」这种**口语功能诉求**——它不长得像「拿到原始需求」，却精准落在 `brainstorming` 的 description（「any creative work - creating features, building components, adding functionality」）和 `using-superpowers`《Skill Priority》逐字点名的例子（「"Let's build X" → superpowers:brainstorming first」）上。

**所以修法是扩 `docflow-requirement` 的触发面，不是加防御条款。** 正文层不动——S4 里 `docflow-requirement/SKILL.md` 根本没被加载过，往正文写任何东西都不会被读到。

---

# GREEN 验证（2026-08-27，扩了 `docflow-requirement` 的触发面之后）

**改动只有一处**：`docflow-requirement` 的 `description` 开头由「拿到新的原始需求（需求描述文字、PRD、文档地址、本地需求文件）」改为「有新功能诉求进来……不论对方是给了 PRD / 需求文档 / 文档地址 / 本地需求文件，还是**只用一句口语提**（「我们来做个 X 吧」「给 X 加个 Y 功能」「X 这块要支持 Z」）」，触发词补上对应的口语形态，并加一句「本技能自带需求澄清与方案比选，新功能诉求直接进本技能，不必先走通用的头脑风暴 / 方案探讨类技能」。

**刻意不点名 superpowers**——写成对任何同类技能都成立的表述，本包不与外部生态耦合。实测证明这样就够。

**`SKILL.md` 正文一个字没动。**

## G4 · 同 S4 的沙箱起点、同一句台词 —— ✅ 通过

- ⭕ 调用链变成 `docflow-requirement` → `using-docflow`，**`superpowers:brainstorming` 零出现**（连 assistant 的 thinking 里都检索不到 `superpower|brainstorm|bounded|architectural|spike` 任何一个词）。
- ⭕ 开口就宣告归属：「**我用 docflow-requirement 走需求分析落盘流程。**先读总规则和项目配置，同时摸一下现有代码。」
- ⭕ 走的是 docflow 的澄清形态而非 brainstorming 的：**待确认项一次列全**（口径 5 条 + 方案选型 2 条，每条附推荐），对照 S4 的「按约定我一次只问一个」。
- ⭕ 明确承诺落盘路径与边界：「这些定完我就落需求文档和实现计划到 `.local/docs/requirement/1.0.0-20260101/001-用户导入进度查询/001-初版/`，**本轮不写代码**」——业务号 001 正确（该沙箱 requirement 无存量），且守住了「只做到 requirement 就停」。
- ⭕ 无 `docs/superpowers/plans/`，分支未变。

## 这轮基线附带确认的两件事

1. **docflow 与 superpowers 可以共存，不需要卸载或禁用**。四个撞点里三个本来就不冲突，剩下一个用扩触发面解决。
2. **抢占只可能发生在路由层（`description`）**。凡是 docflow 技能已经被选中的场景，superpowers 的注入完全没进入决策——所以修这类问题永远先看 `description`，别往正文加防御条款（正文那时根本没被加载）。
