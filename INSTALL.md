# 安装 docflow

> **本文档写给 AI agent。** 把这份文档的地址丢给任意 coding agent（Claude Code / Codex / Copilot CLI / Gemini CLI），让它读完并自动完成安装。人类照着做也一样。

安装做的事很简单：把本仓库 `skills/` 下的技能目录，软链进 agent 的技能目录。**但简单不等于容易做对**，先读下面这段。

## 给 agent 的执行须知（必读，别跳）

这个安装有**四种失败方式，退出码全是 0**，你不会收到任何错误信号：

| 失败方式                              | 后果                                                         | 你看到的         |
| ------------------------------------- | ------------------------------------------------------------ | ---------------- |
| 目标位置已存在同名**真实目录**        | `ln -sfn` 不替换它，而是把软链建到它**内部**；旧内容继续生效 | `exit 0`，无输出 |
| 当前工作目录不是包根（bash）          | glob 不展开，建出一个名叫 `*` 的垃圾软链                     | `exit 0`         |
| 工作目录错、但恰好有 `skills/` 子目录 | 软链存活，指向空目录，读不到 `SKILL.md`                      | `exit 0`         |
| 用 `$(pwd)` 拼路径但中途换过目录      | 链接指向错误位置                                             | `exit 0`         |

**所以：命令没报错 ≠ 装好了。** 必须跑完第 3 步的自检、亲眼看到 `✅ 安装成功` 才能向用户报告成功。这不是可选的谨慎，是这个安装唯一的正确性信号。

三条纪律：

1. **全程用绝对路径**，不要依赖当前工作目录，不要用 `$(pwd)`。
2. **撞见冲突就停下问用户**，不要自作主张删除用户已有的目录。
3. **自检失败就如实报告**，不要把「命令跑完了」说成「装好了」。

## 第 1 步：拿到仓库

如果用户本地已经有这个仓库（很常见——你可能正在这个仓库里工作），**跳过这步**，直接用它，不要重新 clone。重复 clone 会产生两份副本，之后用户改 A 份、agent 加载 B 份，排查起来很痛苦。

没有的话再 clone，路径随意：

```bash
git clone https://github.com/lynchjjjj/docflow ~/tools/docflow
```

## 第 2 步：确定包根的绝对路径

包根 = 含有 `skills/`、`scripts/`、`README.md` 的那一层。拿到它的绝对路径：

```bash
cd <仓库路径> && pwd -P
```

记下输出，下一步要用。**注意**：如果仓库是通过软链访问的，`pwd -P` 会解析成真实路径，这正是我们要的。

## 第 3 步：安装 + 自检（一次执行）

把下面整段的 `__PKG__` 替换成第 2 步拿到的绝对路径，然后用 **bash** 执行。安装和自检合在一起，跑完直接给结论：

```bash
PKG="__PKG__"

# 前置检查：包根必须对
if [ ! -d "$PKG/skills" ]; then
  echo "✗ 包根不对：$PKG/skills 不存在，请回到第 2 步"; exit 1
fi

INSTALLED=0; SKIPPED=0; CONFLICT=0
for T in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$T" || exit 1
  for SRC in "$PKG"/skills/*/; do
    SRC="${SRC%/}"; NAME="$(basename "$SRC")"; DEST="$T/$NAME"
    if [ -L "$DEST" ]; then
      CUR="$(readlink "$DEST")"; CUR="${CUR%/}"
      if [ "$CUR" = "$SRC" ]; then SKIPPED=$((SKIPPED+1)); continue; fi
      rm -f "$DEST"                      # 指向别处的旧软链，可安全替换
    elif [ -e "$DEST" ]; then
      echo "✗ 冲突：$DEST 已存在且不是软链，跳过"
      CONFLICT=$((CONFLICT+1)); continue
    fi
    ln -s "$SRC" "$DEST" && INSTALLED=$((INSTALLED+1))
  done
done
echo "── 新建 ${INSTALLED}，已是最新 ${SKIPPED}，冲突 ${CONFLICT}"

# 自检：确认每个位置「确实是指向本包的软链」且读得到 SKILL.md。
# 只查 SKILL.md 存在是不够的——冲突位置若是旧版拷贝，里面也有 SKILL.md，会假通过。
OK=0; FAIL=0
for T in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  for SRC in "$PKG"/skills/*/; do
    SRC="${SRC%/}"; NAME="$(basename "$SRC")"; DEST="$T/$NAME"
    CUR=""; if [ -L "$DEST" ]; then CUR="$(readlink "$DEST")"; CUR="${CUR%/}"; fi
    if [ "$CUR" = "$SRC" ] && [ -f "$DEST/SKILL.md" ]; then
      OK=$((OK+1))
    else
      echo "✗ ${DEST} 没有指向本包，或读不到 SKILL.md"; FAIL=$((FAIL+1))
    fi
  done
done
echo "── 自检：${OK} 个正确，${FAIL} 个失败"
if [ "$FAIL" -eq 0 ] && [ "$CONFLICT" -eq 0 ]; then
  echo "✅ 安装成功"
else
  echo "❌ 安装未完成，见上面的 ✗ 行"
fi
```

脚本是**幂等**的：已经指向本包的软链会跳过，重复执行安全，更新后再跑一次也没问题。

只用 Claude Code、不想装到 `~/.agents/skills`？把 `for T in` 那行改成只留 `"$HOME/.claude/skills"`。

## 第 4 步：向用户汇报

看到 `✅ 安装成功` 后，告诉用户这四件事：

1. **装了哪些技能**（`ls ~/.claude/skills/ | grep -E 'docflow|using-docflow'`）。
2. **要重启 agent 会话才会加载**——当前会话扫不到新技能，这是最常见的「装了没反应」原因。
3. **怎么开始用**：进任意项目说「接入 docflow」，会引导生成项目配置并建落盘骨架。
4. **怎么更新**：仓库里 `git pull` 即可，软链自动生效，不用重装。

## 冲突了怎么办

看到 `✗ 冲突：... 已存在且不是软链`，说明那个位置有用户自己的同名技能目录。**不要直接删。** 拿给用户看，问清楚：

```bash
ls -la <冲突路径>          # 里面是什么
cat <冲突路径>/SKILL.md    # 是不是旧版本
```

- 是本包的旧版本（手工拷贝的） → 用户同意后 `rm -rf` 再重跑第 3 步。
- 是用户自己写的同名技能 → 冲突的是名字。要么用户改名保留自己那份，要么放弃装这一个。**这个必须用户定。**

## 卸载

只删软链，不碰仓库：

```bash
for T in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  for f in "$T"/docflow-* "$T"/using-docflow; do
    [ -L "$f" ] && rm -f "$f"
  done
done
```

`[ -L ]` 保证只删软链——万一某个位置是真实目录（用户自己的东西），不会被误删。

## 按需选装

技能之间低耦合，可以只装一部分：把第 3 步内层循环的 `"$PKG"/skills/*/` 换成你要的那几个，例如只要变更记录功能：

```bash
for SRC in "$PKG"/skills/using-docflow "$PKG"/skills/docflow-changes; do
```

唯一的公共依赖是入口技能 `using-docflow`（总规则的单一事实源），装任何一个技能都要带上它。
