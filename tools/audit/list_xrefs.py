# -*- coding: utf-8 -*-
"""
Semantic cross-reference check.
Chapter titles come from the SOURCE (numbered \\chapter only), not from the .toc
(which also contains unnumbered front matter / appendices).
"""
import io, os, re

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
src = io.open("electrodynamics_textbook_v2.tex", encoding="utf-8").read()
lines = src.split("\n")

# ---- numbered chapters: \chapter{...} (no star), in order ----
chapters = {}
n = 0
for i, l in enumerate(lines, 1):
    m = re.match(r"^\\chapter\{(.+)\}\s*$", l)
    if m:
        n += 1
        t = re.sub(r"\\texorpdfstring\{[^}]*\}\{([^}]*)\}", r"\1", m.group(1))
        t = re.sub(r"\\[a-zA-Z]+\s*", "", t).replace("{", "").replace("}", "").strip()
        chapters[n] = (t, i)

print("=== numbered chapters from source ===")
for k in sorted(chapters):
    print(f"  第{k:>2}章  {chapters[k][0]}   (tex line {chapters[k][1]})")

# ---- all '见第N章' / '第N章' pointers with the sentence, excluding pure headings ----
print()
print("=== sentences that POINT somewhere ('见/详见/参见/由第N章') ===")
pat = re.compile(r"(见|详见|参见|回顾|用到|需要|来自)\s*第\s*(\d+)\s*章")
hits = 0
for m in pat.finditer(src):
    num = int(m.group(2))
    ln = src.count("\n", 0, m.start()) + 1
    target = chapters.get(num, ("<NO SUCH CHAPTER>", 0))
    ctx = lines[ln - 1].strip()
    # only show when the pointer is the point of the sentence
    print(f"  L{ln:>5}  第{num}章 = {target[0]}")
    print(f"          {ctx[:165]}")
    hits += 1
print(f"  total pointers: {hits}")

# ---- '§X.Y' pointers ----
print()
print("=== '§X.Y' pointers (with containing line) ===")
sec_pat = re.compile(r"\\S\s*(\d+)\.(\d+)")
seen = set()
for m in sec_pat.finditer(src):
    key = (m.group(1), m.group(2))
    ln = src.count("\n", 0, m.start()) + 1
    ctx = lines[ln - 1].strip()
    if key in seen:
        continue
    seen.add(key)
    print(f"  L{ln:>5}  §{key[0]}.{key[1]}   {ctx[:150]}")
