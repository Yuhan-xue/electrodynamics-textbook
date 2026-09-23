# -*- coding: utf-8 -*-
"""Print front matter + appendix page ranges from the compiled .toc."""
import io, os, re

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
toc = None
for c in (".build/electrodynamics_textbook_v2.toc",
          "electrodynamics_textbook_v2.toc"):
    if os.path.exists(c):
        toc = io.open(c, encoding="utf-8", errors="replace").read()
        break
if not toc:
    raise SystemExit("no .toc")

entries = []
for m in re.finditer(r"\\contentsline \{chapter\}\{(.*?)\}\{(\d+)\}", toc):
    raw, pg = m.group(1), int(m.group(2))
    mm = re.match(r"\\numberline \{([^}]*)\}", raw)
    num = mm.group(1).strip() if mm else None
    t = re.sub(r"\\numberline \{[^}]*\}", "", raw)
    t = re.sub(r"\\[a-zA-Z]+\s*", "", t).replace("{", "").replace("}", "").strip()
    entries.append((num, t, pg))

FRONT = ("符号说明", "全书高频公式速查表", "前言")
print("=== chapter-level entries ===")
for num, t, pg in entries:
    kind = "front" if t in FRONT else (
        "正文" if (num and num.isdigit()) else
        "附录" if (num and num.isalpha()) else "?")
    print(f"  [{kind}] {num or '-':>3}  {t:26} p.{pg}")

front = [e for e in entries if e[1] in FRONT]
apps = [e for e in entries if e[0] and e[0].isalpha()]
body = [e for e in entries if e[0] and e[0].isdigit()]
print()
if front:
    print(f"front matter : p.{front[0][2]}–{front[-1][2]}")
if body:
    print(f"正文         : p.{body[0][2]}–{body[-1][2]}  ({len(body)} 章)")
if apps:
    print(f"附录         : p.{apps[0][2]}–{apps[-1][2]}  ({len(apps)} 个: "
          + "".join(e[0] for e in apps) + ")")
