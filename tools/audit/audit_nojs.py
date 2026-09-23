# -*- coding: utf-8 -*-
"""Determine, per page, how much content survives with JS disabled."""
import io, os, re

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

for f in sorted(x for x in os.listdir("html") if x.endswith(".html")):
    s = io.open(os.path.join("html", f), encoding="utf-8").read()
    body = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    # visible text with tags stripped
    txt = re.sub(r"<[^>]+>", " ", body)
    txt = re.sub(r"\s+", " ", txt).strip()
    empties = re.findall(r'<(\w+)[^>]*\bid="([\w-]+)"[^>]*>\s*</\1>', body)
    print(f"{f:20} 静态正文 {len(txt):6} 字符", end="")
    if empties:
        print("  | JS 填充的空容器:", ", ".join(f"<{t}#{i}>" for t, i in empties[:6]))
    else:
        print()
