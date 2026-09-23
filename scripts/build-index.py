#!/usr/bin/env python3
"""docflow 生成式索引：扫描落盘根，重建 INDEX.md。

索引是缓存不是账本——数据源永远是目录结构 + 文档头部元信息行，本脚本随时可重算，
不存在「忘了维护」的问题。

用法：
    python3 build-index.py <落盘根路径> [--types requirement,changes,frontend,contract,sql] [--check-only]

- 正常模式：在 <落盘根>/INDEX.md 生成索引（含警告节），exit 0。
- --check-only：不写任何文件，警告打 stderr；有警告 exit 1，无警告 exit 0。

同时体检约定库 <落盘根>/conventions/（不含归档子目录）：单条超长、单文件条数或字数超预算
各报一条警告。预算默认值见 using-docflow《约定库》，项目可在配置里改，调用时用 --conv-* 传入。
「一条」= 以 `- 【` 开头的行，连同其后缩进的续行；按字符数计（不按行数——一行可以写九百字）。

元信息行约定（与 docflow-requirement 的需求文档模板一致）：
    - 一句话目标：<...>
    - 承接自：<相对落盘根的 requirement 批次目录路径> 或 无

「最近改动」用文件 mtime（有意不用 git log：几百个业务逐个调 git 太慢，
个人本机场景 mtime 足够；clone/迁移后 mtime 失真属已知取舍）。
"""
import argparse
import re
import sys
import time
from pathlib import Path

DEFAULT_TYPES = "requirement,changes,frontend,contract,sql"
DOC_NAME = "001-需求文档.md"
RE_NNN_DIR = re.compile(r"^\d{3}-")
RE_GOAL = re.compile(r"^- 一句话目标：(.+)$")
RE_FOLLOWS = re.compile(r"^- 承接自：(.+)$")
HEAD_LINES = 30  # 元信息只看文档前 30 行
CONV_DIR = "conventions"
CONV_ARCHIVE = "归档"          # 退休条目的去处，开工不读、不计预算
CONV_ENTRY_PREFIX = "- 【"
CONV_MAX_CHARS = 150           # 单条上限（字符，含日期与出处）
CONV_MAX_ENTRIES = 50          # 单文件条数上限
CONV_MAX_FILE_CHARS = 8000     # 单文件总字符上限（非条目的正文也算）
CONV_SHOW_LINES = 5            # 超长条目警告里最多列几个行号


def numbered_subdirs(path: Path):
    """返回 path 下 NNN- 前缀的子目录，按名称排序。"""
    if not path.is_dir():
        return []
    return sorted(d for d in path.iterdir() if d.is_dir() and RE_NNN_DIR.match(d.name))


def read_meta(doc: Path):
    """从需求文档头部抓（一句话目标, 承接自）；缺失返回空串。"""
    goal, follows = "", ""
    if not doc.is_file():
        return goal, follows
    try:
        lines = doc.read_text(encoding="utf-8").splitlines()[:HEAD_LINES]
    except (OSError, UnicodeDecodeError):
        return goal, follows
    for line in lines:
        m = RE_GOAL.match(line.strip())
        if m:
            goal = m.group(1).strip()
        m = RE_FOLLOWS.match(line.strip())
        if m:
            follows = m.group(1).strip().strip("`").strip()  # 路径常被写成行内代码
    return goal, follows


def latest_mtime(path: Path):
    """path 下（含自身）全部文件的最大 mtime，格式 YYYY-MM-DD；空目录返回空串。"""
    mtimes = [p.stat().st_mtime for p in path.rglob("*") if p.is_file()]
    if not mtimes:
        return ""
    return time.strftime("%Y-%m-%d", time.localtime(max(mtimes)))


def esc(cell: str) -> str:
    """markdown 表格单元格转义。"""
    return cell.replace("|", "\\|")


def scan(root: Path, types):
    """扫描落盘根，返回（业务列表, 警告列表）。

    业务聚合键 =（分支短名目录名, NNN-业务目录名），跨类型合并。
    """
    biz_map = {}   # (branch, biz_name) -> dict
    warnings = []

    for type_name in types:
        type_dir = root / type_name
        if not type_dir.is_dir():
            continue
        for branch_dir in sorted(d for d in type_dir.iterdir() if d.is_dir()):
            biz_dirs = numbered_subdirs(branch_dir)
            # 撞号检测：同分支同类型下 NNN 前缀重复
            by_num = {}
            for b in biz_dirs:
                by_num.setdefault(b.name[:3], []).append(b.name)
            for num, names in sorted(by_num.items()):
                if len(names) > 1:
                    warnings.append(
                        f"业务撞号：{type_name}/{branch_dir.name} 下号 {num} 重复：{' / '.join(sorted(names))}")
            for biz_dir in biz_dirs:
                key = (branch_dir.name, biz_dir.name)
                info = biz_map.setdefault(key, {
                    "types": [], "batches": [], "goal": "", "follows": "", "mtime": ""})
                if type_name not in info["types"]:
                    info["types"].append(type_name)
                batches = [d.name for d in numbered_subdirs(biz_dir)]
                for b in batches:
                    if b not in info["batches"]:
                        info["batches"].append(b)
                # 元信息只认 requirement 侧；从最新批次往回找，
                # 某批次的文档没写元信息时回退到更早批次（新批次常只写增量）
                if type_name == "requirement":
                    if batches:
                        docs = [biz_dir / b / DOC_NAME
                                for b in sorted(batches, key=lambda n: n[:3], reverse=True)]
                    else:
                        docs = [biz_dir / DOC_NAME]  # 老两层形态
                    for doc in docs:
                        goal, follows = read_meta(doc)
                        info["goal"] = info["goal"] or goal
                        info["follows"] = info["follows"] or follows
                        if info["goal"] and info["follows"]:
                            break
                mtime = latest_mtime(biz_dir)
                if mtime > info["mtime"]:
                    info["mtime"] = mtime

    # 承接悬空检测
    for (branch, biz), info in sorted(biz_map.items()):
        follows = info["follows"]
        if follows and follows != "无" and not (root / follows).exists():
            warnings.append(
                f"承接悬空：requirement/{branch}/{biz} 的「承接自」指向不存在路径 {follows}")

    return biz_map, warnings


def conv_entries(lines):
    """把约定文件拆成条目：返回 [(起始行号, 条目全文)]。

    续行 = 紧跟在条目后、以空白开头的非空行；遇到空行或顶格行即结束当前条目。
    """
    entries, current = [], None
    for i, line in enumerate(lines, 1):
        if line.startswith(CONV_ENTRY_PREFIX):
            current = [i, line.rstrip()]
            entries.append(current)
        elif current and line.strip() and line[:1] in (" ", "\t"):
            current[1] += line.strip()
        else:
            current = None
    return [tuple(e) for e in entries]


def check_conventions(root: Path, max_chars, max_entries, max_file_chars):
    """约定库体检：返回警告列表。归档子目录不计。"""
    warnings = []
    conv = root / CONV_DIR
    if not conv.is_dir():
        return warnings
    for f in sorted(conv.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        entries = conv_entries(text.splitlines())
        rel = f"{CONV_DIR}/{f.name}"
        if len(text) > max_file_chars:
            warnings.append(f"约定库超预算：{rel} 共 {len(text)} 字，上限 {max_file_chars}")
        if len(entries) > max_entries:
            warnings.append(f"约定库超预算：{rel} 共 {len(entries)} 条，上限 {max_entries}")
        long = [n for n, body in entries if len(body) > max_chars]
        if long:
            shown = "、".join(str(n) for n in long[:CONV_SHOW_LINES])
            more = " 等" if len(long) > CONV_SHOW_LINES else ""
            warnings.append(
                f"约定条目超长：{rel} 有 {len(long)} 条超过 {max_chars} 字（行 {shown}{more}）")
    return warnings


def render(root: Path, biz_map, warnings, types):
    lines = [
        "# 落盘索引（自动生成，勿手改）",
        "",
        f"> 重建命令：`python3 <docflow包>/scripts/build-index.py {root}`；重建即最新。",
        "",
        "## 业务总表",
        "",
        "| 分支短名 | 业务 | 批次数 | 最新批次 | 一句话目标 | 承接自 | 产物 | 最近改动 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (branch, biz), info in sorted(biz_map.items()):
        batches = sorted(info["batches"], key=lambda n: n[:3])
        batch_count = f"{len(batches)}" if batches else "0（老形态）"
        latest = batches[-1] if batches else ""
        # 产物列按传入类型集的顺序输出，保证稳定
        prods = ",".join(t for t in types if t in info["types"])
        lines.append("| " + " | ".join(esc(c) for c in [
            branch, biz, batch_count, latest,
            info["goal"], info["follows"], prods, info["mtime"]]) + " |")
    lines += ["", "## 警告", ""]
    if warnings:
        lines += [f"- {w}" for w in warnings]
    else:
        lines.append("无")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="docflow 生成式索引")
    parser.add_argument("root", help="落盘根路径（如 <项目>/.local/docs）")
    parser.add_argument("--types", default=DEFAULT_TYPES,
                        help=f"要扫描的产物类型目录，逗号分隔（默认 {DEFAULT_TYPES}）")
    parser.add_argument("--check-only", action="store_true",
                        help="只体检不写文件；有警告 exit 1")
    parser.add_argument("--conv-max-chars", type=int, default=CONV_MAX_CHARS,
                        help=f"约定库单条字符上限（默认 {CONV_MAX_CHARS}）")
    parser.add_argument("--conv-max-entries", type=int, default=CONV_MAX_ENTRIES,
                        help=f"约定库单文件条数上限（默认 {CONV_MAX_ENTRIES}）")
    parser.add_argument("--conv-max-file-chars", type=int, default=CONV_MAX_FILE_CHARS,
                        help=f"约定库单文件字符上限（默认 {CONV_MAX_FILE_CHARS}）")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"落盘根不存在：{root}", file=sys.stderr)
        sys.exit(2)
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    biz_map, warnings = scan(root, types)
    warnings += check_conventions(root, args.conv_max_chars, args.conv_max_entries,
                                  args.conv_max_file_chars)
    for w in warnings:
        print(w, file=sys.stderr)

    if args.check_only:
        sys.exit(1 if warnings else 0)

    (root / "INDEX.md").write_text(render(root, biz_map, warnings, types), encoding="utf-8")
    print(f"已生成 {root / 'INDEX.md'}（{len(biz_map)} 个业务，{len(warnings)} 条警告）")
    sys.exit(0)


if __name__ == "__main__":
    main()
