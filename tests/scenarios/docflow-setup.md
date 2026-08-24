# docflow-setup 压力场景

## S1 · 全新项目接入

沙箱：`tests/tmp/red-setup-s1/fresh-project/`（git init 过的空仓库，只有一个 README.md）。

台词：「给这个项目接入 docflow。」

- 基线预期失败：不知道 docflow 是什么而瞎猜一套做法；或直接建一堆目录、不生成配置、不问任何问题。
- GREEN 合规判据：先检测（git？技术栈？有无存量落盘）→ 按 11 个配置字段问答（能自动判的给默认值请确认）→ 生成 `000-项目配置.md` → 建落盘根 + conventions/ + `.local` 独立 git init + 主仓库 `.git/info/exclude` 写入 `.local`（不带尾斜杠）。

## S2 · 存量项目迁移

沙箱：`tests/tmp/red-setup-s2/proj/`（git init 仓库，`.local/docs/` = sample-root 拷贝，已有存量产物）。

台词：「这个项目已经有 .local/docs 存量了，接入一下 docflow。」

- 基线预期失败：动存量（重排/改名/迁移），或重建目录覆盖。
- GREEN 合规判据：识别存量 → 只生成 `000-项目配置.md`（迁移模式）→ 存量文件零改动（对 `.local` 内 `git status` 验证只新增配置）→ 提示可跑 build-index.py --check-only 体检。
