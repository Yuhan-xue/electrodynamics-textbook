# -*- coding: utf-8 -*-
"""
Verify the rebuilt site: link integrity, asset presence, HTML hygiene, and that
book-data.js is CONSISTENT with the compiled artefacts (rather than checking
hard-coded numbers, which legitimately change as the book grows).
"""
import io, os, re, glob, sys, json

# run from anywhere: resolve the repo root (two levels up from this file)
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

ROOT = "html"
problems = []
pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))

# ---- links ----
for f in pages:
    s = io.open(f, encoding="utf-8").read()
    base = os.path.dirname(f)
    for m in re.finditer(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', s):
        u = m.group(1)
        if u.startswith(("#", "mailto:", "data:", "javascript:")):
            continue
        p = u.split("#")[0].split("?")[0]
        if p and not os.path.exists(os.path.normpath(os.path.join(base, p))):
            problems.append(f"{os.path.basename(f)}: broken link -> {u}")

# ---- per-page hygiene ----
for f in pages:
    s = io.open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    if "assets/site.css" not in s:
        problems.append(f"{name}: missing shared stylesheet link")
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", s, re.S):
        if len(m.group(1).strip()) > 400:
            problems.append(f"{name}: large inline <style> block "
                            f"({len(m.group(1))} chars)")
    if "<html lang=" not in s:
        problems.append(f"{name}: missing lang attribute")
    if 'name="viewport"' not in s:
        problems.append(f"{name}: missing viewport meta")
    hits = re.findall(r'\son(?:click|change|load|submit|input)\s*=', s)
    if hits:
        problems.append(f"{name}: {len(hits)} inline event handler(s)")

# ---- PDF present ----
pdf = "electrodynamics_textbook_v2.pdf"
if not os.path.exists(pdf):
    problems.append("PDF referenced by reader.html does not exist")

# ---- book-data.js consistent with the compiled artefacts ----
bd_txt = io.open(os.path.join(ROOT, "book-data.js"), encoding="utf-8").read()
bd = json.loads(re.search(r"window\.BOOK = (\{.*\});", bd_txt, re.S).group(1))
facts = bd["facts"]

try:
    import pypdf
    real_pages = len(pypdf.PdfReader(pdf).pages)
    if facts["pages"] != real_pages:
        problems.append(f"book-data pages={facts['pages']} but PDF has {real_pages}")
except Exception as e:
    problems.append(f"could not read PDF: {e}")

if facts["chapters"] != 10:
    problems.append(f"chapters={facts['chapters']} (expected 10)")
if facts["appendices"] != 9:
    problems.append(f"appendices={facts['appendices']} (expected 9)")

tex = io.open("electrodynamics_textbook_v2.tex", encoding="utf-8").read()
n_ex = len(re.findall(r"\\begin\{example\}", tex))
if facts["examples"] != n_ex:
    problems.append(f"book-data examples={facts['examples']} but tex has {n_ex}")

for c in bd["chapters"]:
    if not isinstance(c.get("page"), int) or c["page"] < 1:
        problems.append(f"chapter {c['title']!r} has bad page {c.get('page')}")

print(f"pages checked : {len(pages)}")
print(f"PDF present   : {os.path.exists(pdf)}")
print(f"facts         : {facts['pages']}p, {facts['chapters']} chapters, "
      f"{facts['appendices']} appendices, {facts['examples']} examples")
print(f"problems      : {len(problems)}")
for p in problems:
    print("   -", p)
sys.exit(1 if problems else 0)
