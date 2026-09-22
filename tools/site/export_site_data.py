# -*- coding: utf-8 -*-
"""
Regenerate html/book-data.js from the book itself.

Self-contained: reads the LaTeX source (structure) and the compiled .toc
(real page numbers). Run from the repository root:

    latexmk -xelatex electrodynamics_textbook_v2.tex   # refresh .toc
    python tools/site/export_site_data.py

The site never hand-maintains page numbers, so its navigation cannot drift
away from the book.
"""
import io, json, os, re, sys, glob, collections

TEX = "electrodynamics_textbook_v2.tex"
OUT = "html/book-data.js"

FRONT = {"符号说明", "全书高频公式速查表", "前言"}
BODY = ["数学预备知识", "静电学基础", "电介质与静电边界条件", "静电学边值问题",
        "静磁学", "磁介质", "麦克斯韦方程组", "电磁波的传播", "电磁波的辐射",
        "相对论电动力学"]
ENVS = ["theorem", "definition", "corollary", "example", "insight", "warning",
        "history", "review", "tip", "miniquiz", "chapterreview", "impEqbox"]


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        cut = None
        for k, ch in enumerate(line):
            if ch == "%" and (k == 0 or line[k - 1] != "\\"):
                cut = k
                break
        out.append(line if cut is None else line[:cut])
    return "\n".join(out)


def parse_braced(src, i):
    if i >= len(src) or src[i] != "{":
        return None, i
    depth, start = 0, i + 1
    while i < len(src):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start:i], i + 1
        i += 1
    return src[start:], len(src)


def find_toc():
    """Locate the .toc from the last compile (root or .build/)."""
    for c in [TEX.replace(".tex", ".toc"),
              os.path.join(".build", TEX.replace(".tex", ".toc"))]:
        if os.path.exists(c):
            return c
    for c in glob.glob("**/*.toc", recursive=True):
        if "electrodynamics" in os.path.basename(c):
            return c
    return None


def main():
    if not os.path.exists(TEX):
        sys.exit(f"error: {TEX} not found — run from the repository root")

    raw = io.open(TEX, encoding="utf-8").read()
    src = strip_comments(raw)
    n_lines = raw.count("\n") + 1

    toc_path = find_toc()
    if not toc_path:
        sys.exit("error: no .toc found. Compile the book first, e.g.\n"
                 "       latexmk -xelatex electrodynamics_textbook_v2.tex")
    print("using TOC:", toc_path)

    # ---- chapters / sections with real page numbers ----
    entries = []
    pat = re.compile(r"\\contentsline\s*\{(chapter|section|subsection)\}"
                     r"\{(.*?)\}\{(\d+)\}\{([^}]*)\}")
    for line in io.open(toc_path, encoding="utf-8").read().split("\n"):
        m = pat.search(line)
        if not m:
            continue
        level, title, page, _anchor = m.groups()
        title = re.sub(r"\\numberline\s*\{[^}]*\}", "", title)
        title = re.sub(r"\\[a-zA-Z]+\s*", "", title).replace("{", "").replace("}", "").strip()
        entries.append({"level": level, "title": title, "page": int(page)})

    chapters, cur = [], None
    for e in entries:
        if e["level"] == "chapter":
            cur = {"title": e["title"], "page": e["page"], "sections": []}
            chapters.append(cur)
        elif e["level"] == "section" and cur is not None:
            cur["sections"].append({"title": e["title"], "page": e["page"]})

    def kind_of(t):
        if t in FRONT:
            return "front"
        return "chapter" if t in BODY else "appendix"

    for c in chapters:
        c["kind"] = kind_of(c["title"])
    ci = ai = 0
    for c in chapters:
        if c["kind"] == "chapter":
            ci += 1
            c["number"] = ci
        elif c["kind"] == "appendix":
            c["letter"] = chr(ord("A") + ai)
            ai += 1

    # ---- structure counts straight from the source ----
    token_re = re.compile(r"\\(begin|end)\{(" + "|".join(ENVS) + r")\}")
    stacks = collections.defaultdict(list)
    blocks = []
    for m in token_re.finditer(src):
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            stacks[env].append(m.end())
        elif stacks[env]:
            blocks.append((stacks[env].pop(), m.start(), env))

    counts = collections.Counter(env for _s, _e, env in blocks)

    bounds = []
    for n, line in enumerate(src.split("\n"), 1):
        if line.startswith("\\chapter"):
            bounds.append((n, parse_braced(line, line.find("{"))[0] or ""))

    def chapter_of(lineno):
        name = None
        for bn, title in bounds:
            if bn > lineno:
                break
            name = title
        return name

    per_chapter = collections.defaultdict(list)
    diffs = collections.Counter()
    for body_start, body_end, env in sorted(blocks):
        if env != "example":
            continue
        lineno = src.count("\n", 0, body_start) + 1
        body = src[body_start:body_end]
        dm = re.search(r"\\difficulty\{([^}]*)\}", body)
        d = dm.group(1) if dm else None
        diffs[d] += 1
        per_chapter[chapter_of(lineno)].append({"line": lineno, "difficulty": d})

    for c in chapters:
        c["examples"] = per_chapter.get(c["title"], [])
        c["counts"] = {}

    facts = {
        "pages": None,
        "texLines": n_lines,
        "chapters": sum(1 for c in chapters if c["kind"] == "chapter"),
        "appendices": sum(1 for c in chapters if c["kind"] == "appendix"),
        "examples": counts.get("example", 0),
        "examplesByDifficulty": {k: v for k, v in diffs.items() if k},
        "theorems": counts.get("theorem", 0),
        "definitions": counts.get("definition", 0),
        "insights": counts.get("insight", 0),
        "warnings": counts.get("warning", 0),
        "tips": counts.get("tip", 0),
        "miniquizzes": counts.get("miniquiz", 0),
        "version": "v2.16",
    }

    try:
        import pypdf
        pdf = TEX.replace(".tex", ".pdf")
        for cand in (pdf, os.path.join(".build", pdf)):
            if os.path.exists(cand):
                facts["pages"] = len(pypdf.PdfReader(cand).pages)
                break
    except Exception:
        pass
    if facts["pages"] is None:
        facts["pages"] = max(c["page"] for c in chapters)

    data = {"facts": facts, "chapters": chapters}
    os.makedirs("html", exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("/* 自动生成 —— 请勿手改。\n")
        f.write("   数据源：electrodynamics_textbook_v2.tex 结构 + 编译产物 .toc 实际页码\n")
        f.write("   重新生成：python tools/site/export_site_data.py  */\n")
        f.write("window.BOOK = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"wrote {OUT}")
    print(f"  {facts['pages']} pages · {facts['chapters']} chapters · "
          f"{facts['appendices']} appendices · {facts['examples']} examples "
          f"({facts['examplesByDifficulty']})")
    print(f"  source: {n_lines} lines")


main()
