# -*- coding: utf-8 -*-
"""
Regenerate README's factual numbers from the compiled artefacts and source,
so the README cannot drift from the book. Rewrites only the numbers it owns.
"""
import io, os, re

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

TEX = "electrodynamics_textbook_v2.tex"
src = io.open(TEX, encoding="utf-8").read()
n_lines = src.count("\n") + 1

# ---- page count + chapter start pages from the compiled PDF/TOC ----
import pypdf
pdf = None
for c in (".build/electrodynamics_textbook_v2.pdf", "electrodynamics_textbook_v2.pdf"):
    if os.path.exists(c):
        pdf = c
        break
n_pages = len(pypdf.PdfReader(pdf).pages)

toc = None
for c in (".build/electrodynamics_textbook_v2.toc", "electrodynamics_textbook_v2.toc"):
    if os.path.exists(c):
        toc = io.open(c, encoding="utf-8", errors="replace").read()
        break

chapters = []          # [(num, title, page)]  numbered chapters only
if toc:
    ap_seen = False
    n = 0
    for m in re.finditer(r"\\contentsline \{chapter\}\{(.*?)\}\{(\d+)\}", toc):
        title, page = m.group(1), int(m.group(2))
        if "numberline" in title:
            n += 1
            t = re.sub(r"\\numberline \{[^}]*\}", "", title)
            t = re.sub(r"\\[a-zA-Z]+\s*", "", t).replace("{", "").replace("}", "").strip()
            chapters.append((n, t, page))
        else:
            ap_seen = True

# ---- block counts from source ----
def count(env):
    return len(re.findall(r"\\begin\{" + env + r"\}", src))

facts = {
    "pages": n_pages,
    "lines": n_lines,
    "examples": count("example"),
    "theorems": count("theorem"),
    "definitions": count("definition"),
    "insights": count("insight"),
    "warnings": count("warning"),
    "tips": count("tip"),
    "miniquiz": count("miniquiz"),
}
diffs = {}
for b in re.findall(r"\\begin\{example\}(.*?)\\end\{example\}", src, re.S):
    m = re.search(r"\\difficulty\{([^}]*)\}", b)
    if m:
        diffs[m.group(1)] = diffs.get(m.group(1), 0) + 1

print("computed facts:")
for k, v in facts.items():
    print(f"  {k:12} {v}")
print(f"  difficulties {diffs}")
print(f"  chapters     {[(c[0], c[2]) for c in chapters]}")

# ---- rewrite README ----
p = "README.md"
r = io.open(p, encoding="utf-8").read()
orig = r

r = r.replace("LaTeX 源文件（完整可编译，8918 行）",
              f"LaTeX 源文件（完整可编译，{n_lines} 行）")
r = r.replace("编译产物（XeLaTeX，172 页）",
              f"编译产物（XeLaTeX，{n_pages} 页）")

# facts table rows
def set_row(text, label, value):
    pat = re.compile(r"(\|\s*" + re.escape(label) + r"\s*\|\s*)[^|]*(\|)")
    return pat.sub(lambda m: m.group(1) + str(value) + " " + m.group(2), text, count=1)

r = set_row(r, "页数", n_pages)
r = set_row(r, "源文件行数", n_lines)
r = set_row(r, "例题", f"{facts['examples']}（基础 {diffs.get('基础', 0)} / "
                       f"提高 {diffs.get('提高', 0)} / 挑战 {diffs.get('挑战', 0)}）")
r = set_row(r, "定理", facts["theorems"])
r = set_row(r, "定义", facts["definitions"])
r = set_row(r, "物理洞见", facts["insights"])
r = set_row(r, "常见误区", facts["warnings"])
r = set_row(r, "学习提示", facts["tips"])
r = set_row(r, "随堂自测", f"{facts['miniquiz']} 组")

# chapter start-page table
for num, title, page in chapters:
    pat = re.compile(r"(\|\s*" + str(num) + r"\s*\|\s*" + re.escape(title) + r"\s*\|\s*)\d+(\s*\|)")
    r = pat.sub(lambda m: m.group(1) + str(page) + m.group(2), r, count=1)

if r != orig:
    io.open(p, "w", encoding="utf-8").write(r)
    print(f"\nupdated {p}")
else:
    print(f"\n{p} already up to date")
