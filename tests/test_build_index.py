"""build-index.py 的验收测试（python3 标准库，直接 `python3 tests/test_build_index.py` 运行）。"""
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "sample-root"
SCRIPT = ROOT.parent / "scripts" / "build-index.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def main():
    tmp = ROOT / "tmp" / "sample-root"
    if tmp.parent.exists():
        shutil.rmtree(tmp.parent)
    shutil.copytree(FIXTURE, tmp)

    r = run(str(tmp))
    assert r.returncode == 0, f"正常模式应 exit 0，实际 {r.returncode}：{r.stderr}"
    index_path = tmp / "INDEX.md"
    assert index_path.exists(), "应生成 INDEX.md"
    index = index_path.read_text(encoding="utf-8")

    # 业务行：跨类型聚合（001-用户导入 同时有 requirement/changes/sql）
    assert "001-用户导入" in index, "业务应入索引"
    assert "requirement,changes,sql" in index, "产物列应跨类型聚合"
    # 老两层形态照样入索引，批次数标 0（老形态）
    assert "002-权限过滤" in index, "老形态业务应入索引"
    assert "0（老形态）" in index, "老形态批次数应标注"
    # 一句话目标与承接链入表
    assert "Excel 批量导入用户" in index, "一句话目标应入表"
    assert "1.0.0-20260101/001-用户导入" in index, "承接列应含上游路径"
    # 两类警告（文案关键词 + 涉事对象）
    assert "悬空" in index and "0.9.0-20251201" in index, "应报承接悬空"
    assert "撞号" in index and "002-报表导出" in index and "002-撞号业务" in index, "应报业务撞号"
    # 勿手改声明
    assert "自动生成" in index, "应有自动生成声明"
    # 多批次：最新批次没写元信息时，应回退到更早批次去取
    assert "初版写了目标，后续批次没写" in index, "元信息应能从更早批次回退取到"

    # 承接路径写成行内代码（带反引号）照样认，不报悬空
    assert "004-反引号承接 的「承接自」" not in index, "反引号包着的承接路径不应报悬空"

    # --check-only：不写文件、有警告 exit 1
    index_path.unlink()
    r2 = run(str(tmp), "--check-only")
    assert r2.returncode == 1, f"--check-only 有警告应 exit 1，实际 {r2.returncode}"
    assert not index_path.exists(), "--check-only 不应写 INDEX.md"
    assert "悬空" in r2.stderr and "撞号" in r2.stderr, "警告应打到 stderr"

    # 约定库体检：续行算进条目字数；归档目录不计
    assert "约定条目超长" in r2.stderr and "002-编码约定.md 有 1 条" in r2.stderr, \
        f"应报 1 条超长（续行计入、归档不计）：{r2.stderr}"
    assert "归档" not in r2.stderr, "归档目录不应被体检"
    assert "约定库超预算" not in r2.stderr, "默认预算下样本不应超预算"
    # 预算可由参数调：条数上限 2、单文件字符上限 100 时两项都报
    r3 = run(str(tmp), "--check-only", "--conv-max-entries", "2", "--conv-max-file-chars", "100")
    assert "共 3 条，上限 2" in r3.stderr, f"应报条数超预算：{r3.stderr}"
    assert "上限 100" in r3.stderr, f"应报字数超预算：{r3.stderr}"
    # 调高单条上限后不再报超长
    r4 = run(str(tmp), "--check-only", "--conv-max-chars", "1000")
    assert "约定条目超长" not in r4.stderr, "上限调高后不应报超长"
    # 约定库警告也进 INDEX.md 的警告节
    run(str(tmp))
    assert "约定条目超长" in index_path.read_text(encoding="utf-8"), "约定库警告应写进索引"

    print("PASS")


if __name__ == "__main__":
    main()
