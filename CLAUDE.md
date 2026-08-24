# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

本仓库是 **docflow**——一个把开发文档落盘流程打包成的 **skills 包**，不是应用代码。产物是 11 个 Markdown 技能 + 1 个零依赖 python3 索引脚本。改这个仓库 = 改「规则文本」，所以下面的约束比代码风格更重要。

## 常用命令

```bash
# 跑测试（唯一的自动化测试，纯标准库、无 pytest）
python3 tests/test_build_index.py          # 打印 PASS 即通过；失败抛 AssertionError

# 手工跑索引脚本
python3 scripts/build-index.py <落盘根>                 # 生成 <落盘根>/INDEX.md
python3 scripts/build-index.py <落盘根> --check-only    # 只体检，警告打 stderr，有警告 exit 1
python3 scripts/build-index.py <落盘根> --types requirement,changes,contract,sql

# 本地安装（软链，改完立即生效，无需重装）
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.claude/skills/$(basename "$d"); done
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.agents/skills/$(basename "$d"); done
```

测试用 `tests/fixtures/sample-root/`（含病态样本：承接悬空、业务撞号、老两层形态、多批次元信息回退）拷进 `tests/tmp/` 后跑，`tests/tmp/` 已 gitignore。加断言就直接往 `main()` 里加。

提交信息格式：`feat|test|docs|fix: <中文简述>`。

## 架构：三个耦合点

**1. `using-docflow` 是目录/编号/批次规则的单一事实源。**
四层目录 `<落盘根>/<产物类型>/<分支短名>/<NNN-业务>/<NNN-批次>/<NNN-文件>`、编号规则、「什么时候开新批次」的判据只写在 `skills/using-docflow/SKILL.md`。其余 10 个技能一律在开头用 `**REQUIRED BACKGROUND:** …见 using-docflow` 引用，**不抄写**。规则要改只改这一处；发现别处出现了重复的规则表述，那是要删的重复，不是要同步的副本。

**2. 元信息行是脚本与模板之间的硬契约。**
需求文档头部四行（`- 编号：` / `- 分支：` / `- 一句话目标：` / `- 承接自：`）格式定死：`scripts/build-index.py` 的 `RE_GOAL` / `RE_FOLLOWS` 正则靠它抓取（只看前 30 行），`skills/docflow-requirement/references/templates.md` 负责产出它。**动其中一边必须同时动另一边并加测试断言。**

**3. 项目个性全住各项目自己的 `000-项目配置.md`，包内保持项目无关。**
落盘根、分支短名规则、启用产物类型、目录名映射、变更记录层次映射等 11 个字段由 `docflow-setup` 问答生成。包里**不得出现任何具体项目的值**（表名、租户号、分支前缀、内部工具名）——这类内容属于使用方项目的配置或约定库。所有技能的第一步都是「开工三读」：读项目配置 → 读约定库 → 读模板；配置不存在就停下引导用户跑 `docflow-setup`。

其他结构性事实：

- **索引是缓存不是账本**：`INDEX.md` 随时可由脚本重算，不手工维护；技能里凡涉及「查历史」都必须给出无 python3 时的 `ls` + `grep` 降级路径（见 `using-docflow`《没有 python3 的机器怎么办》），不能让流程卡在脚本上。
- **`docflow-setup` 会记录「接入包版本」**（`git describe`），升级检查模式靠对比它与 `CHANGELOG.md` 得出迁移建议——所以凡影响存量落盘产物的改动（模板字段、目录规则、配置字段增减）必须在 CHANGELOG 里显式标「迁移提示」。
- 技能之间低耦合、可单点安装，唯一公共依赖是 `using-docflow`。新增技能时不要制造新的横向依赖。

## 写技能时的纪律

- **语言**：SKILL.md 正文与 `description` 用中文（技术标识符保留英文），frontmatter 的 `name` 用英文 kebab-case 且与目录名一致。
- **`description` 只写触发条件与触发词**，不摘要工作流；写清楚「什么时候不该用它、该用哪个」（参考 `docflow-evolve` / `docflow-trace` 互相划界的写法）。
- **RED → GREEN 流程（铁律）**：新技能或改防御条款前，先派子代理在**包仓库之外**的沙箱跑无技能基线，场景文案存 `tests/scenarios/<skill>.md`，逐字基线存 `tests/baselines/<skill>.md`，然后写技能、同场景重跑验证。**没有观察到的失败就不写防御条款**——`tests/baselines/README.md` 记着一次沙箱建在仓库内部导致基线失真的教训（子代理读到了未实现的计划文档）。
- 基线还揭示过一类**形状错误**（判断力对但把约定写成 68 行小论文）：这类问题用**正向配方**修（规定条目长什么样），不用禁令堆。见 `tests/baselines/docflow-retro.md`。
- 篇幅参考：SKILL.md 55–150 行，长模板拆到 `references/` 下按需读取。
