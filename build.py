#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notes.md -> index.html

单一数据源：所有内容只写在 notes.md 里，本脚本负责生成网页。
不要再手改 index.html，它每次都会被整个覆盖。

用法：
    python build.py            # 只生成 index.html
    python build.py --push     # 生成 + 提交 + 推送（Pages 会自动重新部署）

notes.md 支持的写法：
    ## 分类名                  -> 一个卡片分区
    | 操作 | 方法 |            -> 一行条目（表头行自动跳过）
    | **操作** | 方法 |         -> 加粗的条目会高亮显示
    > 备注文字                 -> 分区底部的提示块
    `Ctrl+Shift+C`             -> 自动渲染成键盘键帽
    `D:\\某个路径`              -> 自动渲染成等宽代码
    **加粗**                   -> 加粗
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "notes.md"
OUT = ROOT / "index.html"

HEADER_WORDS = {"操作", "场景"}
MODIFIERS = {"Win", "Ctrl", "Alt", "Shift", "Tab", "Esc", "Enter", "Space"}


# ---------- 行内格式 ----------

def is_keyboard(s: str) -> bool:
    """判断一段反引号内容是不是快捷键。"""
    if re.search(r"(Ctrl|Alt|Shift|Win)\+", s):
        return True
    if s in MODIFIERS:
        return True
    if len(s) == 1 and s in "+-.":
        return True
    if re.fullmatch(r"F\d{1,2}", s):
        return True
    return False


def code_span(s: str) -> str:
    if is_keyboard(s):
        parts = s.split("+")
        return "+".join("<kbd>%s</kbd>" % html.escape(p) for p in parts)
    return "<code>%s</code>" % html.escape(s)


def inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", lambda m: code_span(m.group(1)), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


# ---------- 解析 notes.md ----------

def parse(md: str):
    sub_lines = []
    sections = []
    cur = None

    for raw in md.splitlines():
        line = raw.rstrip()

        if line.startswith("# "):
            continue

        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "items": [], "notes": []}
            sections.append(cur)
            continue

        if line.startswith("|"):
            if cur is None:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            if cells[0] in HEADER_WORDS:
                continue
            if re.fullmatch(r"[-: ]+", cells[0] or ""):
                continue
            cur["items"].append((cells[0], cells[1]))
            continue

        if line.startswith(">"):
            txt = line.lstrip(">").strip()
            if not txt:
                continue
            if cur is None:
                sub_lines.append(txt)
            else:
                cur["notes"].append(txt)
            continue

    return sub_lines, sections


# ---------- 渲染 ----------

def render_section(sec) -> str:
    out = ["    <section>"]
    n = len(sec["items"])
    out.append('      <h2>%s <span class="count">%d 条</span></h2>'
               % (html.escape(sec["title"]), n))

    for k, v in sec["items"]:
        hot = k.strip().startswith("**")
        cls = "item hot" if hot else "item"
        out.append('      <div class="%s">' % cls)
        out.append('        <div class="k">%s</div>' % inline(k))
        out.append('        <div class="v">%s</div>' % inline(v))
        out.append("      </div>")

    notes = [x for x in sec["notes"] if x]
    if notes:
        out.append('      <div class="note">')
        out.append("        " + "<br>".join(inline(x) for x in notes))
        out.append("      </div>")

    out.append("    </section>")
    return "\n".join(out)


CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    background: #0e1013; color: #e6e8eb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    line-height: 1.65; -webkit-font-smoothing: antialiased; padding: 0 0 60px;
  }
  .wrap { max-width: 780px; margin: 0 auto; padding: 0 18px; }
  header { padding: 44px 0 26px; border-bottom: 1px solid #23282f; margin-bottom: 30px; }
  .kicker {
    font-size: 11px; letter-spacing: .18em; text-transform: uppercase;
    color: #4d9fff; margin-bottom: 12px; display: flex; align-items: center; gap: 7px;
  }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: #3ecf8e; display: inline-block; }
  h1 { font-size: clamp(24px, 6vw, 34px); font-weight: 600; letter-spacing: -.025em; line-height: 1.25; }
  .sub { color: #8b939e; font-size: 13.5px; margin-top: 9px; }
  .search-box { margin-top: 22px; position: relative; }
  .search-box svg {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    width: 15px; height: 15px; stroke: #6d7681; fill: none; stroke-width: 2;
  }
  #q {
    width: 100%; padding: 12px 14px 12px 40px;
    background: #171a1f; border: 1px solid #2a2f36; border-radius: 10px;
    color: #e6e8eb; font-size: 14.5px; font-family: inherit; outline: none; transition: border-color .15s;
  }
  #q::placeholder { color: #5f6873; }
  #q:focus { border-color: #4d9fff88; }
  section { margin-bottom: 34px; }
  h2 {
    font-size: 15px; font-weight: 600; color: #e6e8eb;
    padding-bottom: 10px; margin-bottom: 12px; border-bottom: 1px solid #23282f;
    display: flex; align-items: baseline; gap: 9px;
  }
  h2 .count { font-size: 11.5px; color: #5f6873; font-weight: 400; }
  .item {
    display: grid; grid-template-columns: 190px 1fr; gap: 16px;
    padding: 11px 14px; border-radius: 8px;
    border-left: 2px solid transparent; transition: background .12s;
  }
  .item:hover { background: #15181d; }
  .item.hot { border-left-color: #4d9fff; background: #131820; }
  .item.hot:hover { background: #161d27; }
  .k { font-size: 13.5px; color: #c3cad3; font-weight: 500; }
  .item.hot .k { color: #e6e8eb; }
  .v { font-size: 13.5px; color: #98a1ac; }
  .v b { color: #e6e8eb; font-weight: 500; }
  .v em { color: #f0a04b; font-style: normal; }
  kbd {
    display: inline-block; font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 12px; line-height: 1.5; padding: 1px 6px; margin: 0 1px;
    background: #23282f; color: #cfd6de;
    border: 1px solid #3a424b; border-bottom-width: 2px;
    border-radius: 5px; white-space: nowrap;
  }
  .note {
    margin-top: 14px; padding: 13px 15px;
    background: #14181e; border: 1px solid #23282f; border-radius: 9px;
    font-size: 12.8px; color: #8b939e;
  }
  .note strong { color: #c3cad3; font-weight: 500; }
  .note code {
    font-family: ui-monospace, Consolas, monospace; font-size: 11.5px;
    background: #1d232b; padding: 1px 5px; border-radius: 4px; color: #a8b0ba;
    word-break: break-all;
  }
  .empty { display: none; text-align: center; padding: 50px 20px; color: #5f6873; font-size: 14px; }
  footer {
    margin-top: 46px; padding-top: 20px; border-top: 1px solid #23282f;
    font-size: 12.5px; color: #5f6873; line-height: 1.8;
  }
  footer .principle {
    margin-top: 12px; padding: 12px 15px;
    background: #131820; border-left: 2px solid #4d9fff; border-radius: 0 8px 8px 0;
    color: #98a1ac;
  }
  @media (max-width: 560px) {
    header { padding: 32px 0 22px; }
    .item { grid-template-columns: 1fr; gap: 4px; padding: 10px 12px; }
    .k { font-size: 13.5px; }
    .v { font-size: 13px; }
    kbd { font-size: 11.5px; }
  }
"""

JS = """
  (function () {
    var q = document.getElementById('q');
    var sections = Array.prototype.slice.call(document.querySelectorAll('main section'));
    var empty = document.getElementById('empty');
    q.addEventListener('input', function () {
      var kw = q.value.trim().toLowerCase();
      var total = 0;
      sections.forEach(function (sec) {
        var shown = 0;
        Array.prototype.forEach.call(sec.querySelectorAll('.item'), function (it) {
          var hit = !kw || it.textContent.toLowerCase().indexOf(kw) !== -1;
          it.style.display = hit ? '' : 'none';
          if (hit) shown++;
        });
        sec.style.display = shown ? '' : 'none';
        total += shown;
      });
      empty.style.display = total ? 'none' : 'block';
    });
  })();
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电脑小技能清单</title>
<meta name="description" content="Windows 11 日常操作速查：快捷键、截图、任务栏、GitHub。">
<style>%s</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="kicker"><span class="dot"></span>Windows 11 · 持续更新</div>
    <h1>电脑小技能清单</h1>
    <p class="sub">%s</p>
    <div class="search-box">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-4-4"></path></svg>
      <input id="q" type="text" placeholder="搜一下：截图、任务栏、快捷键、GitHub…" autocomplete="off">
    </div>
  </header>

  <main>
%s

    <div class="empty" id="empty">没找到。换个词试试，比如「截图」「任务栏」。</div>

  </main>

  <footer>
    Windows 11 · 内容持续补充<br>
    遇到新技巧直接加进 notes.md，重新生成即可。
    <div class="principle">不确定的操作先问，别硬试；重要的东西先备份。</div>
  </footer>

</div>
<script>%s</script>
</body>
</html>
"""


def main():
    if not SRC.exists():
        sys.exit("找不到 notes.md：%s" % SRC)

    md = SRC.read_text(encoding="utf-8")
    sub_lines, sections = parse(md)

    if not sections:
        sys.exit("notes.md 里没有解析到任何 ## 分类，检查格式")

    total_items = sum(len(s["items"]) for s in sections)
    body = "\n\n".join(render_section(s) for s in sections)
    sub = " ".join(sub_lines) if sub_lines else "日常操作速查。"

    out_html = TEMPLATE % (CSS, html.escape(sub), body, JS)
    OUT.write_text(out_html, encoding="utf-8")

    print("已生成 %s" % OUT.name)
    print("分类 %d 个，条目 %d 条，文件 %.1f KB"
          % (len(sections), total_items, len(out_html.encode("utf-8")) / 1024))
    for s in sections:
        print("  - %-16s %d 条" % (s["title"], len(s["items"])))

    if "--push" in sys.argv:
        for cmd in (["git", "add", "index.html", "notes.md", "README.md"],
                    ["git", "commit", "-m", "更新清单内容"],
                    ["git", "push"]):
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
            print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else cmd[0])
            if r.returncode != 0 and cmd[1] != "commit":
                sys.exit("命令失败：%s" % " ".join(cmd))
        print("已推送，Pages 约 1-2 分钟后生效")


if __name__ == "__main__":
    main()
