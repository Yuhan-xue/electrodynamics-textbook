# -*- coding: utf-8 -*-
"""
Emit per-chapter audit briefs (markdown) + a compact inventory JSON.
Each brief lists every block with line/page anchors so an auditor can jump
straight to the source without re-parsing the book.
"""
import io, json, os, re, collections

IDX = ".build/index.json"
OUTDIR = ".build/briefs"

CHAP_ORDER = ["数学预备知识", "静电学基础", "电介质与静电边界条件", "静电学边值问题",
              "静磁学", "磁介质", "麦克斯韦方程组", "电磁波的传播", "电磁波的辐射",
              "相对论电动力学"]

ENV_CN = {"theorem": "定理", "definition": "定义", "corollary": "推论",
          "example": "例题", "insight": "物理洞见", "warning": "常见误区",
          "history": "物理史话", "review": "本节要点", "tip": "学习提示",
          "miniquiz": "随堂自测", "chapterreview": "本章要点回顾", "impEqbox": "核心公式"}


def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def main():
    data = json.loads(read(IDX))
    blocks = data["blocks"]
    toc = data["toc"]
    src_lines = read("electrodynamics_textbook_v2.tex").split("\n")
    src_lines = None  # we only need anchors, not text

    os.makedirs(OUTDIR, exist_ok=True)

    # chapter -> toc page
    toc_by_title = {}
    for e in toc:
        if e["level"] == "chapter":
            toc_by_title.setdefault(e["title"], e["page"])

    by_chap = collections.OrderedDict()
    for b in blocks:
        if b["chapter"] in CHAP_ORDER:
            by_chap.setdefault(b["chapter"], []).append(b)

    inventory = {}
    for ci, ch in enumerate(CHAP_ORDER, 1):
        items = by_chap.get(ch, [])
        start_page = toc_by_title.get(ch)
        lines = [f"# 第{ci}章 {ch} — 审查简报", ""]
        lines.append(f"- 起始页：p.{start_page}")
        lines.append(f"- 结构块总数：{len(items)}")
        counts = collections.Counter(b["env"] for b in items)
        lines.append("- 块类型统计：" + "、".join(
            f"{ENV_CN.get(k, k)} {v}" for k, v in sorted(counts.items())))
        lines.append(f"- 源文件：`electrodynamics_textbook_v2.tex`（8899 行，本行号可直接定位）")
        lines.append("")
        lines.append("## 例题清单")
        lines.append("")
        lines.append("| 行号 | 页 | 难度 | 标题 | label |")
        lines.append("|---|---|---|---|---|")
        exs = [b for b in items if b["env"] == "example"]
        for b in exs:
            lines.append(f'| {b["line"]} | {b["page"]} | {b["difficulty"] or "-"} | '
                         f'{b["title"]} | `{b["label"]}` |')
        if not exs:
            lines.append("| — | — | — | （本章无例题环境） | — |")

        lines.append("")
        lines.append("## 定理 / 定义清单")
        lines.append("")
        lines.append("| 行号 | 页 | 类型 | 标题 |")
        lines.append("|---|---|---|---|")
        for b in items:
            if b["env"] in ("theorem", "definition", "corollary"):
                lines.append(f'| {b["line"]} | {b["page"]} | {ENV_CN[b["env"]]} | {b["title"]} |')

        lines.append("")
        lines.append("## 误区 / 洞见 / 提示清单（初学者相关）")
        lines.append("")
        lines.append("| 行号 | 页 | 类型 | 标题 |")
        lines.append("|---|---|---|---|")
        for b in items:
            if b["env"] in ("warning", "insight", "tip", "history", "review",
                            "miniquiz", "chapterreview"):
                lines.append(f'| {b["line"]} | {b["page"]} | {ENV_CN[b["env"]]} | {b["title"]} |')

        lines.append("")
        inv_entry = {
            "chapter_index": ci, "title": ch, "start_page": start_page,
            "counts": dict(counts),
            "examples": [{"line": b["line"], "page": b["page"],
                          "difficulty": b["difficulty"], "title": b["title"],
                          "label": b["label"]} for b in exs],
        }
        inventory[ch] = inv_entry

        with io.open(os.path.join(OUTDIR, f"ch{ci:02d}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f'wrote briefs/ch{ci:02d}.md  ({ch}, {len(items)} blocks, {len(exs)} examples)')

    with io.open(".build/inventory.json", "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=1)
    print("\nwrote .build/inventory.json")

    # global summary
    print("\n=== ALL EXAMPLES BY DIFFICULTY ===")
    dd = collections.Counter(b["difficulty"] for b in blocks if b["env"] == "example")
    print(dict(dd))


main()
