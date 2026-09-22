# -*- coding: utf-8 -*-
"""Verify the rebuilt site: link integrity, asset presence, basic HTML sanity."""
import io, os, re, glob, sys

# run from anywhere: resolve the repo root (two levels up from this file)
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
ROOT = "html"
problems = []
pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))

# collect all href/src targets
for f in pages:
    s = io.open(f, encoding="utf-8").read()
    base = os.path.dirname(f)
    for m in re.finditer(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', s):
        u = m.group(1)
        if u.startswith(("#", "mailto:", "data:", "javascript:")):
            continue
        p = u.split("#")[0].split("?")[0]
        if not p:
            continue
        t = os.path.normpath(os.path.join(base, p))
        if not os.path.exists(t):
            problems.append(f"{os.path.basename(f)}: broken link -> {u}")

# every page must load the shared stylesheet and the data module
for f in pages:
    s = io.open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    if "assets/site.css" not in s:
        problems.append(f"{name}: missing shared stylesheet link")
    # no page may carry a large inline <style> block any more
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", s, re.S):
        if len(m.group(1).strip()) > 400:
            problems.append(f"{name}: contains a large inline <style> block "
                            f"({len(m.group(1))} chars) — should use assets/site.css")
    if "<html lang=" not in s:
        problems.append(f"{name}: missing lang attribute")
    if 'name="viewport"' not in s:
        problems.append(f"{name}: missing viewport meta")

# inline event handlers (a11y / CSP smell)
for f in pages:
    s = io.open(f, encoding="utf-8").read()
    hits = re.findall(r'\son(?:click|change|load|submit|input)\s*=', s)
    if hits:
        problems.append(f"{os.path.basename(f)}: {len(hits)} inline event handler(s)")

# the reader must point at a PDF that actually exists
pdf = os.path.normpath(os.path.join(ROOT, "..", "electrodynamics_textbook_v2.pdf"))
if not os.path.exists(pdf):
    problems.append("PDF referenced by reader.html does not exist")

# book-data.js must contain the verified page count
bd = io.open(os.path.join(ROOT, "book-data.js"), encoding="utf-8").read()
for needle in ['"pages": 172', '"chapters": 10', '"appendices": 9', '"examples": 49']:
    if needle not in bd:
        problems.append(f"book-data.js missing verified fact: {needle}")

print(f"pages checked: {len(pages)}")
print(f"PDF present: {os.path.exists(pdf)}")
print(f"problems: {len(problems)}")
for p in problems:
    print("   -", p)
sys.exit(1 if problems else 0)
