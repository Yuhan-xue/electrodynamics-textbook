# -*- coding: utf-8 -*-
"""
Build a machine-readable structural index of the textbook.
Robust approach: tokenize ALL \begin{env}/\end{env} pairs with a stack, then
extract each block's title/label/difficulty and resolve its page from the .aux.

Outputs: .build/index.json, .build/toc.json (consumed by later tooling)
"""
import io, json, os, re, collections

TEX = "electrodynamics_textbook_v2.tex"
AUX = ".build/electrodynamics_textbook_v2.aux"
TOC = ".build/electrodynamics_textbook_v2.toc"

ENVS = ["theorem", "definition", "corollary", "example", "insight", "warning",
        "history", "review", "tip", "miniquiz", "chapterreview", "impEqbox"]


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def strip_comments(text):
    """Remove unescaped % comments, preserving line count."""
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
    """If src[i]=='{' return (content, index_after_close), else (None, i)."""
    if i >= len(src) or src[i] != "{":
        return None, i
    depth = 0
    start = i + 1
    while i < len(src):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start:i], i + 1
        i += 1
    return src[start:], len(src)


def label_pages(aux_text):
    """label -> page. Indexes both the full label and its post-colon suffix,
    so `ex:dot-example-v2` is reachable as `dot-example-v2`."""
    pages = {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^{}]*)\}\{(\d+)\}", aux_text):
        label, page = m.group(1), int(m.group(3))
        if label.endswith("@cref"):
            continue
        pages[label] = page
        if ":" in label:
            pages.setdefault(label.split(":", 1)[1], page)
    return pages


def parse_toc(path):
    entries = []
    pat = re.compile(
        r"\\contentsline\s*\{(chapter|section|subsection)\}"
        r"\{(.*?)\}\{(\d+)\}\{([^}]*)\}")
    for line in read(path).split("\n"):
        m = pat.search(line)
        if not m:
            continue
        level, title, page, anchor = m.groups()
        title = re.sub(r"\\numberline\s*\{[^}]*\}", "", title)
        title = re.sub(r"\\[a-zA-Z]+\s*", "", title)
        title = title.replace("{", "").replace("}", "").strip()
        entries.append({"level": level, "title": title,
                        "page": int(page), "anchor": anchor})
    return entries


def main():
    src = strip_comments(read(TEX))
    pages = label_pages(read(AUX))
    toc_entries = parse_toc(TOC)

    # ---- structural bounds (chapters / sections) ----
    bounds = []
    for n, line in enumerate(src.split("\n"), 1):
        for kw, kind in (("\\chapter", "chapter"), ("\\section", "section")):
            if line.startswith(kw) and not line.startswith(kw + "ection"):
                pass
        if line.startswith("\\chapter"):
            bounds.append((n, "chapter", parse_braced(line, line.find("{"))[0] or ""))
        elif line.startswith("\\section"):
            bounds.append((n, "section", parse_braced(line, line.find("{"))[0] or ""))
        elif line.startswith("\\subsection"):
            bounds.append((n, "subsection", parse_braced(line, line.find("{"))[0] or ""))

    def context(lineno):
        ch = sec = None
        for (bn, kind, title) in bounds:
            if bn > lineno:
                break
            if kind == "chapter":
                ch, sec = title, None
            elif kind == "section":
                sec = title
        return ch, sec

    # ---- stack-based environment pairing ----
    token_re = re.compile(r"\\(begin|end)\{(" + "|".join(ENVS) + r")\}")
    stacks = collections.defaultdict(list)
    blocks = []
    for m in token_re.finditer(src):
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            stacks[env].append(m.end())
        else:
            if not stacks[env]:
                continue
            body_start = stacks[env].pop()
            blocks.append((body_start, m.start(), env))

    env_blocks = []
    for body_start, body_end, env in sorted(blocks):
        lineno = src.count("\n", 0, body_start) + 1
        # arguments immediately follow \begin{env}
        i = body_start
        args = []
        while len(args) < 2:
            while i < len(src) and src[i] in " \t\r\n":
                i += 1
            if i < len(src) and src[i] == "{":
                val, i = parse_braced(src, i)
                args.append(val)
            else:
                break
        # body begins after the arguments
        real_start = body_start
        if args:
            j = body_start
            for _ in range(len(args)):
                while j < len(src) and src[j] in " \t\r\n":
                    j += 1
                _, j = parse_braced(src, j)
            real_start = j
        body = src[real_start:body_end]
        dm = re.search(r"\\difficulty\{([^}]*)\}", body)
        ch, sec = context(lineno)
        label = args[1] if len(args) > 1 else ""
        env_blocks.append({
            "env": env,
            "title": args[0] if args else "",
            "label": label,
            "line": lineno,
            "chapter": ch,
            "section": sec,
            "difficulty": dm.group(1) if dm else None,
            "page": pages.get(label),
            "nchars": len(body),
            "body": body,
        })

    counts = collections.Counter(e["env"] for e in env_blocks)
    print("environment counts:", dict(sorted(counts.items())))
    ex = [e for e in env_blocks if e["env"] == "example"]
    print(f"examples: {len(ex)}")
    print("difficulty dist:", dict(collections.Counter(e["difficulty"] or "(none)" for e in ex)))
    print("examples missing page:", sum(1 for e in ex if e["page"] is None))
    print("blocks missing page:", sum(1 for e in env_blocks if e["page"] is None))
    print("blocks with empty body:", sum(1 for e in env_blocks if e["nchars"] == 0))

    chapters = []
    for e in env_blocks:
        if e["chapter"] is None:
            continue
        if not chapters or chapters[-1]["title"] != e["chapter"]:
            chapters.append({"title": e["chapter"], "blocks": []})
        chapters[-1]["blocks"].append(e)

    print()
    for c in chapters:
        print(f'  {c["title"]:<22} blocks={len(c["blocks"]):3d}')

    with io.open(".build/index.json", "w", encoding="utf-8") as f:
        json.dump({"blocks": env_blocks, "chapters": chapters,
                   "bounds": bounds, "toc": toc_entries},
                  f, ensure_ascii=False, indent=1)
    print("\nwrote .build/index.json")


main()
