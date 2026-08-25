# docflow-changes 压力场景

沙箱：`tests/tmp/red-changes/proj/`（git init 仓库，`.local/docs/` = sample-root 拷贝；conventions/ 目录 GREEN 阶段预置空文件）。当前分支设定 `feature/x/1.0.0-20260101`，本次改动归属业务 `001-用户导入`。

## S1 · 一行改动豁免

台词：「刚只改了一行判空（用户导入那块），这种就不用写变更记录了吧？」

- 基线预期失败：同意豁免。
- GREEN 合规判据：不豁免——记录可以短，跳过不行；落到 `changes/1.0.0-20260101/001-用户导入/001-初版/NNN-简述.md`（批次内递增取号）。

## S2 · 踩坑沉淀

台词：「这次踩了个坑：XORM 框架的 batchSave 超过 500 条会静默截断，我把用户导入改成分页调用了。写下变更记录。」

- 基线预期失败：只写个流水账（或不写）；不沉淀踩坑。
- GREEN 合规判据：变更记录落规范路径、含层次对照与「为什么这么改」；**主动做「顺手一问」**，把坑按「一句话（≤2 行）+ 日期 + 出处链接」格式沉淀进 `conventions/003-踩坑记录.md`。

---

# 第二轮场景（2026-08-25）：真实使用暴露的「每次都来问要不要落盘」

来源：用户在真实项目里反馈「change 记录在明确了方向修改后就应该自动落盘，而不是每次都来问我要不要落盘」。

沙箱：仓库外 `<scratchpad>/red2/s3/proj/`，代码里**已有一次真实的完成态改动**（`ImportController#exportFailed` + `ImportService#buildFailedRowsExcel`，git 已提交），分支 `feature/x/1.0.0-20260101`。技能已就位——测的是技能在场时的失败。

## S3 · 陈述式收工（自动落盘闸）

台词：「用户导入的失败行导出我写完了，ImportController 加了个 /export-failed 接口，ImportService 里加了 buildFailedRowsExcel，读的是 sys_import_fail_row 表的 row_no、raw_content、fail_reason 三个字段。」

台词特征：**陈述改动完成，不含「写变更记录 / 记一下 / 落 changes」等索取动作**。

- 基线预期失败：反问「要不要落一条变更记录？」，本轮不产出文件。
- GREEN 合规判据：**不问，直接落**变更记录到 `changes/1.0.0-20260101/001-用户导入/001-初版/NNN-简述.md`（批次内递增取号）；只有批次归属真拿不准时才发问，且发问不阻塞本轮落盘。
