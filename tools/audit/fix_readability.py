# -*- coding: utf-8 -*-
"""
可读性/UI 维护的小幅 HTML 修订：
  1. errata.html 的 noscript 指向已删除的 errata_report.md -> ERRATA_REPORT.md
  2. 为 tools.html / formulas.html 增加 noscript 说明（它们依赖 JS 才能计算/展开）
"""
import io, os

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

changed = []

# ---------- 1. errata.html 旧文件名 ----------
p = "html/errata.html"
s = io.open(p, encoding="utf-8").read()
old = ("勘误列表需要 JavaScript 渲染。完整勘误报告同时保存在仓库的\n"
       "        <code>errata_report.md</code> 中，可直接查阅。")
new = ("勘误列表需要 JavaScript 渲染。完整勘误报告同时以静态文件形式保存在仓库根目录的\n"
       "        <code>ERRATA_REPORT.md</code> 中，可直接查阅；\n"
       "        也可打开 <a href=\"../electrodynamics_textbook_v2.pdf\">教材 PDF</a> 查看正文。")
if old in s:
    s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8").write(s)
    changed.append(f"{p}: noscript 文件名 errata_report.md -> ERRATA_REPORT.md")
else:
    changed.append(f"{p}: 未找到待替换文本（可能已改）")

# ---------- 2. 追加 noscript ----------
def add_noscript(path, block, anchor):
    s = io.open(path, encoding="utf-8").read()
    if "<noscript" in s:
        return f"{path}: 已有 noscript，跳过"
    if anchor not in s:
        return f"{path}: 找不到插入锚点，跳过"
    s = s.replace(anchor, anchor + "\n\n" + block, 1)
    io.open(path, "w", encoding="utf-8").write(s)
    return f"{path}: 已插入 noscript"


TOOLS_BLOCK = """    <noscript>
      <p class="note note-warn">
        本页的换算与计算需要 JavaScript。无脚本时可用教材对应内容手工核对：
        SI ⇄ 高斯单位制的换算因子见<a href="formulas.html">公式速查</a>与教材附录 D（单位制转换手册），
        电磁波与矢量运算的公式见教材第 8 章与第 1 章。
      </p>
    </noscript>"""

FORMULAS_BLOCK = """    <noscript>
      <p class="note">
        本页全部公式为静态内容，无 JavaScript 也可正常阅读。
        页首的「本页内容」导航锚点在无脚本时仍可用（浏览器原生锚点）。
        需要做数值换算请见<a href="../electrodynamics_textbook_v2.pdf">教材 PDF</a>附录 D。
      </p>
    </noscript>"""

# tools.html: 插在 </main> 之前
s = io.open("html/tools.html", encoding="utf-8").read()
i = s.rfind("</main>")
if i > 0 and "<noscript" not in s:
    s = s[:i] + TOOLS_BLOCK + "\n\n" + s[i:]
    io.open("html/tools.html", "w", encoding="utf-8").write(s)
    changed.append("html/tools.html: 已插入 noscript")
else:
    changed.append("html/tools.html: 跳过（已有 noscript 或无锚点）")

# formulas.html: 插在 </main> 之前
s = io.open("html/formulas.html", encoding="utf-8").read()
i = s.rfind("</main>")
if i > 0 and "<noscript" not in s:
    s = s[:i] + FORMULAS_BLOCK + "\n\n" + s[i:]
    io.open("html/formulas.html", "w", encoding="utf-8").write(s)
    changed.append("html/formulas.html: 已插入 noscript")
else:
    changed.append("html/formulas.html: 跳过（已有 noscript 或无锚点）")

for c in changed:
    print(" ", c)
