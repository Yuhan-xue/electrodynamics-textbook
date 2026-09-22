# -*- coding: utf-8 -*-
"""
Systematic cross-reference audit:
 1. every \\ref/\\eqref/\\cref target must exist in the .aux
 2. every hard-coded 「第N章」「§X.Y」 textual reference must point at a
    chapter/section that actually has that number and topic

Run from the repo root AFTER a compile (needs the .aux and .toc).
"""
import io, os, re, sys, glob

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def read(p):
    return io.open(p, encoding="utf-8").read()


tex = read("electrodynamics_textbook_v2.tex")

# ---------- locate aux/toc ----------
aux = toc = None
for cand in ("electrodynamics_textbook_v2.aux", ".build/electrodynamics_textbook_v2.aux"):
    if os.path.exists(cand):
        aux = cand
        break
for cand in ("electrodynamics_textbook_v2.toc", ".build/electrodynamics_textbook_v2.toc"):
    if os.path.exists(cand):
        toc = cand
        break
if not aux or not toc:
    sys.exit("need .aux and .toc — compile first")

aux_txt = read(aux)

# ---------- 1. label existence ----------
defined = set(re.findall(r"\\newlabel\{([^}]+)\}", aux_txt))
used = set()
for m in re.finditer(r"\\(?:ref|eqref|cref|Cref|pageref)\{([^}]*)\}", tex):
    for lab in m.group(1).split(","):
        used.add(lab.strip())
missing = sorted(l for l in used if l and l not in defined)
print("=== 1. undefined label references ===")
print(f"  labels defined : {len(defined)}")
print(f"  distinct used  : {len(used)}")
print(f"  MISSING        : {len(missing)}")
for m in missing:
    # find the line
    for i, line in enumerate(tex.split("\n"), 1):
        if m in line and ("\\ref" in line or "\\eqref" in line or "\\cref" in line):
            print(f"     line {i}: {m}  |  {line.strip()[:110]}")
            break

# ---------- 2. textual chapter / section references ----------
# build the real numbering from the .toc
sections = {}   # '3.2' -> title   (chapter.section)
subs = {}
chapters = {}
cur_ch = 0
sec_in_ch = 0
sub_in_sec = 0
for line in read(toc).split("\n"):
    m = re.search(r"\\contentsline\s*\{(chapter|section|subsection)\}\{(.*?)\}\{(\d+)\}", line)
    if not m:
        continue
    level, title, _pg = m.groups()
    title = re.sub(r"\\numberline\s*\{([^}]*)\}", r"\1", title)
    num = None
    mm = re.match(r"^([\d.]+)\s*(.*)$", title)
    if mm and re.match(r"^[\d.]+$", mm.group(1)):
        num = mm.group(1).rstrip(".")
        title = mm.group(2)
    title = re.sub(r"\\[a-zA-Z]+\s*", "", title).replace("{", "").replace("}", "").strip()
    if level == "chapter":
        cur_ch += 1
        sec_in_ch = 0
        chapters[cur_ch] = title
    elif level == "section" and num:
        sec_in_ch += 1
        sections[num] = title
    elif level == "subsection" and num:
        subs[num] = title

print()
print(f"=== 2. textual '第N章' references  (全书共 {len(chapters)} 章) ===")
bad_ch = []
for m in re.finditer(r"第\s*(\d+)\s*章", tex):
    n = int(m.group(1))
    if n not in chapters:
        line = tex.count("\n", 0, m.start()) + 1
        bad_ch.append((line, m.group(0)))
print(f"  references to non-existent chapters: {len(bad_ch)}")
for line, tok in bad_ch:
    print(f"     line {line}: {tok}")

print()
print("=== 3. textual '§X.Y' references ===")
bad_sec = []
for m in re.finditer(r"\\S\s*([\d]+\.[\d.]+)", tex):
    num = m.group(1).rstrip(".")
    line = tex.count("\n", 0, m.start()) + 1
    ok = num in sections or num in subs
    if not ok:
        bad_sec.append((line, num))
print(f"  references to non-existent sections: {len(bad_sec)}")
for line, num in bad_sec:
    print(f"     line {line}: §{num}")

print()
print("=== 4. chapters (for reference) ===")
for k in sorted(chapters):
    print(f"  第{k:>2}章  {chapters[k]}")
