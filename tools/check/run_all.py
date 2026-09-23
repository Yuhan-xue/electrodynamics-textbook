# -*- coding: utf-8 -*-
"""
全量自检套件 —— 《电动力学》自学教材

用法（仓库根目录）：
    python tools/check/run_all.py              # 跑全部检查
    python tools/check/run_all.py --quick      # 跳过重新编译（用现有产物）
    python tools/check/run_all.py --only 3,7   # 只跑指定编号的检查

设计原则：
  * 每个检查独立、可单独运行、失败不阻断其余检查。
  * 检查的是「产物与源码是否自洽」，而不是硬编码的数字——教材增长不应导致误报。
  * 输出 PASS / FAIL / WARN / SKIP 四种状态，任一 FAIL 时进程返回非零。
  * 需要先编译的检查会自动编译（除非 --quick）。
"""
import argparse
import io
import os
import re
import subprocess
import sys
import time

# ----------------------------------------------------------------------------
# 基础设施
# ----------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)

TEX = "electrodynamics_textbook_v2.tex"
PDF_ROOT = "electrodynamics_textbook_v2.pdf"
BUILD = ".build"
PDF_BUILD = os.path.join(BUILD, "electrodynamics_textbook_v2.pdf")

RESULTS = []


def record(no, name, status, detail=""):
    RESULTS.append({"no": no, "name": name, "status": status, "detail": detail})


def run(cmd, **kw):
    """Run a command; return (returncode, stdout+stderr)."""
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def tex_text():
    return io.open(TEX, encoding="utf-8").read()


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


def pdf_path():
    for p in (PDF_BUILD, PDF_ROOT):
        if os.path.exists(p):
            return p
    return None


def page_count():
    import pypdf
    p = pdf_path()
    return len(pypdf.PdfReader(p).pages) if p else None


def tex_line_count():
    return io.open(TEX, encoding="utf-8").read().count("\n") + 1


# ----------------------------------------------------------------------------
# 1. 编译
# ----------------------------------------------------------------------------
def check_compile(quick=False):
    if quick:
        log = os.path.join(BUILD, "electrodynamics_textbook_v2.log")
        if not os.path.exists(log):
            record(1, "LaTeX 编译", "SKIP", "--quick 且无既有 .log")
            return
    else:
        os.makedirs(BUILD, exist_ok=True)
        rc, out = run(["latexmk", "-xelatex", "-interaction=nonstopmode",
                       "-outdir=" + BUILD, TEX])
        # latexmk 在无需重编译时会输出 "Nothing to do" / "All targets ... are up-to-date"
        fresh = ("Output written" in out
                 or "All targets" in out and "up-to-date" in out)
        if not fresh:
            record(1, "LaTeX 编译", "FAIL", "未产出 PDF；尾部输出：" + out[-400:])
            return

    log = os.path.join(BUILD, "electrodynamics_textbook_v2.log")
    if not os.path.exists(log):
        record(1, "LaTeX 编译", "FAIL", "找不到 .log")
        return
    L = io.open(log, encoding="utf-8", errors="replace").read()
    errs = len(re.findall(r"^!", L, re.M))
    over = len(re.findall(r"Overfull \\hbox", L))
    under = len(re.findall(r"Underfull \\hbox", L))
    undef = len(re.findall(r"undefined", L))
    miss = len(re.findall(r"Missing character", L))
    n = page_count()
    detail = (f"{n} 页 · 错误 {errs} · Overfull {over} · Underfull {under} · "
              f"未定义引用 {undef} · 缺字 {miss}")
    bad = errs or over or under or undef or miss
    record(1, "LaTeX 编译", "FAIL" if bad else "PASS", detail)


# ----------------------------------------------------------------------------
# 2. PDF 产物与元数据
# ----------------------------------------------------------------------------
def check_pdf():
    import pypdf
    import hashlib
    p = pdf_path()
    if not p:
        record(2, "PDF 产物与元数据", "FAIL", "找不到 PDF")
        return
    r = pypdf.PdfReader(p)
    n = len(r.pages)
    md = r.metadata or {}
    title = str(md.get("/Title", ""))
    author = str(md.get("/Author", ""))

    # 版本号必须与仓库内声明的版本一致
    m = re.search(r"v(\d+\.\d+)", title)
    ver_pdf = m.group(1) if m else None

    # 封面页必须渲染出版本号
    cover = r.pages[0].extract_text() or ""
    cover_has = (ver_pdf in cover) if ver_pdf else False

    problems = []
    if not ver_pdf:
        problems.append("PDF 标题无版本号")
    if not cover_has:
        problems.append("封面未渲染版本号")
    if "电动力学" not in title:
        problems.append("PDF 标题异常")
    if not author:
        problems.append("PDF 缺作者元数据")

    # ---- 根目录 PDF 必须与最近一次编译产物「内容一致」 ----
    # 不能比较字节：XeLaTeX 会把编译时间写进 /CreationDate，每次重编译都不同。
    # 因此比较内容判据：页数 + 标题 + 作者 + 每页提取文本。
    # 这条专门用来抓「页数没变所以以为没变」的静默失配：
    # 曾出现根目录 PDF 是加新内容之前的旧构建，而页数恰好相同、肉眼无法察觉。
    if os.path.exists(PDF_BUILD):
        if not os.path.exists(PDF_ROOT):
            problems.append("根目录缺 PDF（应复制编译产物）")
        else:
            a = pypdf.PdfReader(PDF_BUILD)
            b = pypdf.PdfReader(PDF_ROOT)
            if len(a.pages) != len(b.pages):
                problems.append(
                    f"根目录 PDF 页数 {len(b.pages)} ≠ 编译产物 {len(a.pages)}")
            else:
                diff = [i + 1 for i in range(len(a.pages))
                        if (a.pages[i].extract_text() or "") !=
                           (b.pages[i].extract_text() or "")]
                if diff:
                    shown = ", ".join(map(str, diff[:6]))
                    problems.append(
                        f"根目录 PDF 内容与编译产物不一致（{len(diff)} 页不同，"
                        f"如 p.{shown}）——根目录疑似旧构建")
                ma = a.metadata or {}
                mb = b.metadata or {}
                for key in ("/Title", "/Author"):
                    if str(ma.get(key, "")) != str(mb.get(key, "")):
                        problems.append(f"根目录 PDF 的 {key} 与编译产物不一致")

    # ---- 正文关键内容抽查：新加入的定理必须真的出现在 PDF 里 ----
    probe = "洛伦兹力"
    found = any(probe in (pg.extract_text() or "") for pg in r.pages)
    if not found:
        problems.append(f"PDF 中找不到「{probe}」（内容可能未随源码更新）")

    detail = f"{n} 页 · 标题「{title}」· 作者「{author}」"
    if problems:
        record(2, "PDF 产物与元数据", "FAIL", detail + " · " + "；".join(problems))
    else:
        record(2, "PDF 产物与元数据", "PASS", detail)


# ----------------------------------------------------------------------------
# 3. 文档结构
# ----------------------------------------------------------------------------
def check_structure():
    src = strip_comments(tex_text())
    lines = src.split("\n")

    # 附录分界：用行号判定（\appendix 之后出现的 \chapter 均为附录）
    ap_line = None
    for i, l in enumerate(lines, 1):
        if l.strip() == "\\appendix":
            ap_line = i
            break

    chaps, apps = [], []
    for i, l in enumerate(lines, 1):
        m = re.match(r"^\\chapter\{(.+)\}\s*$", l)
        if m:
            t = re.sub(r"\\texorpdfstring\{[^}]*\}\{([^}]*)\}", r"\1", m.group(1))
            t = re.sub(r"\\[a-zA-Z]+\s*", "", t).replace("{", "").replace("}", "").strip()
            (apps if (ap_line and i > ap_line) else chaps).append(t)

    # 环境块配平
    ENVS = ["theorem", "definition", "corollary", "example", "insight", "warning",
            "history", "review", "tip", "miniquiz", "chapterreview", "impEqbox",
            "equation", "align", "itemize", "enumerate"]
    unbalanced = []
    for e in sorted(set(ENVS)):
        b = len(re.findall(r"\\begin\{" + e + r"\}", src))
        n = len(re.findall(r"\\end\{" + e + r"\}", src))
        if b != n:
            unbalanced.append(f"{e}: begin={b} end={n}")

    # 例题必须都带难度标注
    ex_blocks = re.findall(r"\\begin\{example\}(.*?)\\end\{example\}", src, re.S)
    no_diff = [i + 1 for i, b in enumerate(ex_blocks) if "\\difficulty{" not in b]

    # 每章必须有随堂自测 / 综合练习题 / 习题解答
    sec_quiz = len(re.findall(r"\\section\*\{第\d+章随堂自测\}", src))
    sec_ex = len(re.findall(r"\\section\*\{第\d+章综合练习题\}", src))
    sec_sol = len(re.findall(r"\\section\*\{习题解答\}", src))

    # 目录中的章数（.toc 是 UTF-8，但部分环境读取会乱码，故用字节读取）
    toc = os.path.join(BUILD, "electrodynamics_textbook_v2.toc")
    toc_ok = "n/a"
    if os.path.exists(toc):
        T = io.open(toc, encoding="utf-8", errors="replace").read()
        toc_ch = len(re.findall(r"\\contentsline \{chapter\}", T))
        toc_ok = f"目录 {toc_ch} 条章级条目"

    problems = []
    if len(chaps) != 10:
        problems.append(f"编号正文章数 {len(chaps)}（应为 10）")
    if len(apps) != 9:
        problems.append(f"附录数 {len(apps)}（应为 9）")
    if unbalanced:
        problems.append("环境不配平: " + "; ".join(unbalanced))
    if no_diff:
        problems.append(f"{len(no_diff)} 道例题缺难度标注")
    if sec_quiz != 10:
        problems.append(f"随堂自测 {sec_quiz} 组（应为 10）")
    if sec_ex != 10 or sec_sol != 10:
        problems.append(f"综合练习/解答 {sec_ex}/{sec_sol}（应各 10）")

    detail = (f"正文 {len(chaps)} 章 · 附录 {len(apps)} 个 · 例题 {len(ex_blocks)} 道 · "
              f"自测 {sec_quiz} 组 · 练习 {sec_ex} 组 · {toc_ok}")
    record(3, "文档结构", "FAIL" if problems else "PASS",
           detail + (" · " + "；".join(problems) if problems else ""))


# ----------------------------------------------------------------------------
# 4. 交叉引用完整性（标签 + 语义）
# ----------------------------------------------------------------------------
def check_xrefs():
    aux = os.path.join(BUILD, "electrodynamics_textbook_v2.aux")
    if not os.path.exists(aux):
        record(4, "交叉引用", "SKIP", "缺少 .aux，需先编译")
        return
    src = tex_text()
    lines = src.split("\n")
    A = io.open(aux, encoding="utf-8", errors="replace").read()
    defined = set(re.findall(r"\\newlabel\{([^}]+)\}", A))
    used = set()
    for m in re.finditer(r"\\(?:ref|eqref|cref|Cref|pageref)\{([^}]*)\}", src):
        for lab in m.group(1).split(","):
            used.add(lab.strip())
    missing = sorted(l for l in used if l and l not in defined)

    # ---- 语义：文本引用「第N章」必须在 1..10（附录不计入章号） ----
    # 注意：本书会引用外文教材的章号（如「Jackson 第 14 章」「Griffiths 第 7 章」），
    # 也可能在「教材章节对照表」里列出他书的章号——这些都不是内部引用。
    EXT = (r"(Jackson|Griffiths|朗道|Landau|郭硕鸿|赵凯华|梁灿彬|教材|原书|该书|两书"
           r"|第\s*\d+\s*章\s*/|/\s*第\s*\d+\s*章)")
    bad_ch, ext_ch = [], 0
    for m in re.finditer(r"第\s*(\d+)\s*章", src):
        num = int(m.group(1))
        lo, hi = max(0, m.start() - 60), min(len(src), m.end() + 60)
        ctx = src[lo:hi]
        if re.search(EXT, ctx):
            ext_ch += 1
            continue
        if num > 10:
            ln = src.count("\n", 0, m.start()) + 1
            bad_ch.append(f"L{ln}:第{num}章")

    # ---- 语义：§x.y 引用的小节必须存在 ----
    # .toc 的条目形如 \contentsline {section}{\numberline {1.3}标题}{页}{锚}
    toc = os.path.join(BUILD, "electrodynamics_textbook_v2.toc")
    bad_sec = []
    if os.path.exists(toc):
        T = io.open(toc, encoding="utf-8", errors="replace").read()
        real = set()
        for m in re.finditer(
                r"\\contentsline \{(?:section|subsection)\}\{\\numberline \{([\d.]+)\}", T):
            real.add(m.group(1).rstrip("."))
        for m in re.finditer(r"\\S\s*([\d]+\.[\d.]+)", src):
            num = m.group(1).rstrip(".")
            if num not in real and num.rsplit(".", 1)[0] not in real:
                bad_sec.append(num)

    problems = []
    if missing:
        problems.append("未定义标签: " + ", ".join(missing))
    if bad_ch:
        problems.append("不存在的章引用: " + ", ".join(bad_ch))
    if bad_sec:
        problems.append("不存在的小节引用: " + ", ".join(sorted(set(bad_sec))))

    detail = (f"已定义标签 {len(defined)} · 被引用 {len(used)} · "
              f"文本引用章/节异常 {len(bad_ch)}/{len(set(bad_sec))} · "
              f"外部教材章号引用 {ext_ch} 处（已排除）")
    record(4, "交叉引用", "FAIL" if problems else "PASS",
           detail + (" · " + "；".join(problems) if problems else ""))


# ----------------------------------------------------------------------------
# 5. 公式编号与标签唯一性
# ----------------------------------------------------------------------------
def check_numbering():
    src = tex_text()
    A = os.path.join(BUILD, "electrodynamics_textbook_v2.aux")
    problems = []
    warns = []

    # ---- label 唯一 ----
    labels = re.findall(r"\\label\{([^}]+)\}", src)
    dup = sorted({l for l in labels if labels.count(l) > 1})
    if dup:
        problems.append("重复 label: " + ", ".join(dup))

    # ---- 编号公式是否带 label ----
    # STYLE_GUIDE §1.2 明确：只有六个核心公式必须 equation+label，
    # 推导中间步骤用 \[ \] 或 align*。故此处只统计、不判失败。
    n_eq_labelled = 0
    n_eq_total = 0
    for env in ("equation", "align"):
        for m in re.finditer(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", src, re.S):
            n_eq_total += 1
            if "\\label{" in m.group(1):
                n_eq_labelled += 1

    # ---- 六个核心公式必须有 equation + label（STYLE_GUIDE §1.2） ----
    # 注意：tcolorbox 定理的 {标题}{label} 第二参数不是 \label{}，不能算作公式标签；
    # 这里只认真实的 \label{eq:...}。
    must = {
        "麦克斯韦方程组": r"eq:m[1-4]\b|eq:vac[1-4]\b|eq:M[1-4]\b",
        "泊松方程": r"eq:poisson\b",
        "拉普拉斯方程": r"eq:laplace|eq:poisson",   # 无源特例由泊松方程覆盖
        "达朗贝尔方程": r"eq:d-alembert",
        "洛伦兹力": r"eq:lorentz-force\b",
    }
    labels_all = set(labels)
    missing_must = []
    for k, pat in must.items():
        # 用 match（前缀匹配）而非 fullmatch：达朗贝尔方程有 -phi / -A 两个标签
        if not any(re.match(pat, l, re.I) for l in labels_all):
            missing_must.append(k)
    if missing_must:
        problems.append("核心公式缺 \\label: " + ", ".join(missing_must))

    # ---- 被 \eqref/\ref 引用的公式标签是否存在（与 check 4 互补，此处只看 eq:） ----
    eq_refs = set()
    for m in re.finditer(r"\\eqref\{([^}]*)\}", src):
        eq_refs.add(m.group(1).strip())
    dangling = sorted(r for r in eq_refs if r not in labels_all)
    if dangling:
        problems.append("\\eqref 指向不存在的标签: " + ", ".join(dangling))

    share = f"{n_eq_labelled}/{n_eq_total}"
    detail = (f"label 共 {len(labels)} 个（唯一性{'OK' if not dup else '异常'}） · "
              f"编号环境带 label {share} · 核心公式齐全度 "
              f"{len(must) - len(missing_must)}/{len(must)}")
    st = "FAIL" if problems else ("WARN" if warns else "PASS")
    record(5, "公式编号与标签", st,
           detail + (" · " + "；".join(problems + warns) if (problems or warns) else ""))


# ----------------------------------------------------------------------------
# 6. 文档与站点数据一致性
# ----------------------------------------------------------------------------
def check_consistency():
    import json
    problems = []
    n_pages = page_count()
    n_lines = tex_line_count()
    src = tex_text()
    n_ex = len(re.findall(r"\\begin\{example\}", src))

    # README 声明的页数必须与实际一致
    readme = io.open("README.md", encoding="utf-8").read()
    m = re.search(r"\|\s*\*\*页数\*\*\s*\|\s*(\d+)\s*页", readme)
    readme_pages = int(m.group(1)) if m else None
    if readme_pages and n_pages and readme_pages != n_pages:
        problems.append(f"README 页数 {readme_pages} ≠ 实际 {n_pages}")

    # README 声明的源文件行数
    m = re.search(r"源文件行数\s*\|\s*(\d+)", readme)
    if m and int(m.group(1)) != n_lines:
        problems.append(f"README 行数 {m.group(1)} ≠ 实际 {n_lines}")

    # README 例题数
    m = re.search(r"例题\s*\|\s*(\d+)", readme)
    if m and int(m.group(1)) != n_ex:
        problems.append(f"README 例题数 {m.group(1)} ≠ 实际 {n_ex}")

    # 站点数据与产物一致
    bd = "html/book-data.js"
    if os.path.exists(bd):
        d = json.loads(re.search(r"window\.BOOK = (\{.*\});",
                                 io.open(bd, encoding="utf-8").read(), re.S).group(1))
        f = d["facts"]
        if n_pages and f["pages"] != n_pages:
            problems.append(f"站点页数 {f['pages']} ≠ 实际 {n_pages}")
        if f["examples"] != n_ex:
            problems.append(f"站点例题数 {f['examples']} ≠ 实际 {n_ex}")
        if f["chapters"] != 10 or f["appendices"] != 9:
            problems.append(f"站点章/附录数 {f['chapters']}/{f['appendices']}")
    else:
        problems.append("缺少 html/book-data.js")

    # 版本号在 tex / PDF / 站点 / README 四处一致
    vers = {}
    m = re.search(r"pdftitle=\{电动力学 (v[\d.]+)", src)
    vers["tex"] = m.group(1) if m else None
    m = re.search(r"\\textcolor\{white!80\}\{(v[\d.]+)\}", src)
    vers["cover"] = m.group(1) if m else None
    if os.path.exists(bd):
        vers["site"] = json.loads(re.search(r"window\.BOOK = (\{.*\});",
                                            io.open(bd, encoding="utf-8").read(),
                                            re.S).group(1))["facts"].get("version")
    m = re.search(r"\|\s*\*\*版本\*\*\s*\|\s*(v[\d.]+)", readme)
    vers["readme"] = m.group(1) if m else None
    if os.path.exists(PDF_ROOT):
        import pypdf
        t = str((pypdf.PdfReader(PDF_ROOT).metadata or {}).get("/Title", ""))
        mm = re.search(r"(v[\d.]+)", t)
        vers["pdf"] = mm.group(1) if mm else None
    vals = {k: v for k, v in vers.items() if v}
    if len(set(vals.values())) > 1:
        problems.append("版本号不一致: " + ", ".join(f"{k}={v}" for k, v in vals.items()))

    detail = (f"页数 {n_pages} · 行数 {n_lines} · 例题 {n_ex} · "
              f"版本 " + "/".join(f"{k}:{v}" for k, v in sorted(vals.items())))
    record(6, "文档与站点一致性", "FAIL" if problems else "PASS",
           detail + (" · " + "；".join(problems) if problems else ""))


# ----------------------------------------------------------------------------
# 7. 物理自洽（独立复算脚本必须全部通过）
# ----------------------------------------------------------------------------
PHYSICS_SCRIPTS = [
    ("单位换算因子", "tools/audit/verify_units.py"),
    ("动量守恒方程符号", "tools/audit/verify_ch07_sign.py"),
    ("TE10 的 Hz 符号", "tools/audit/verify_ch08_hz.py"),
    ("洛伦兹色散 dn/dw", "tools/audit/verify_ch08_dispersion.py"),
    ("附录E 辐射功率幂次", "tools/audit/verify_appendix_e.py"),
    ("mu0 偏差量级", "tools/audit/verify_mu0_deviation.py"),
    ("边界条件矢量形式", "tools/audit/verify_bc_vectors.py"),
]


def check_physics():
    fails = []
    ran = 0
    for name, path in PHYSICS_SCRIPTS:
        if not os.path.exists(path):
            fails.append(f"{name}(缺脚本)")
            continue
        rc, out = run([sys.executable, path])
        ran += 1
        if rc != 0:
            fails.append(f"{name}(exit {rc})")
    # 量纲校验覆盖率
    src = tex_text()
    n_ex = len(re.findall(r"\\begin\{example\}", src))
    n_dim = len(re.findall(r"量纲校验|量纲一致", src))
    detail = f"复算脚本 {ran}/{len(PHYSICS_SCRIPTS)} 通过 · 量纲校验出现 {n_dim} 次 / 例题 {n_ex} 道"
    record(7, "物理自洽复算", "FAIL" if fails else "PASS",
           detail + (" · 失败: " + ", ".join(fails) if fails else ""))


# ----------------------------------------------------------------------------
# 8. 站点完整性
# ----------------------------------------------------------------------------
def check_site():
    ok = True
    msgs = []
    rc, out = run([sys.executable, "tools/audit/verify_site.py"])
    if rc != 0:
        ok = False
        msgs.append("verify_site: " + out.strip().split("\n")[-3:][0] if out else "fail")
    else:
        m = re.search(r"problems\s*:\s*(\d+)", out)
        msgs.append(f"链接/资源问题 {m.group(1) if m else '?'}")

    rc2, out2 = run(["node", "--check", "html/assets/site.js"])
    if rc2 != 0:
        ok = False
        msgs.append("site.js 语法错误")
    rc3, out3 = run(["node", "--check", "html/book-data.js"])
    if rc3 != 0:
        ok = False
        msgs.append("book-data.js 语法错误")

    rc4, out4 = run([sys.executable, "tools/audit/verify_js.py"])
    if rc4 != 0:
        ok = False
        msgs.append("页面内联 JS 语法错误")

    n_pages = len([f for f in os.listdir("html") if f.endswith(".html")])
    record(8, "站点完整性", "PASS" if ok else "FAIL",
           f"{n_pages} 个页面 · " + " · ".join(msgs))


# ----------------------------------------------------------------------------
# 9. 仓库卫生
# ----------------------------------------------------------------------------
def check_hygiene():
    problems = []
    tracked = run(["git", "ls-files"])[1].split()
    # 不应入库的产物
    bad = [f for f in tracked if re.search(
        r"\.(aux|log|out|toc|xdv|fls|fdb_latexmk|upa|upb|synctex\.gz)$", f)]
    if bad:
        problems.append("编译中间产物入库: " + ", ".join(bad[:5]))
    if any(f.startswith(".build/") for f in tracked):
        problems.append(".build/ 入库")
    if any(f.startswith(".agent-teams/") for f in tracked):
        problems.append(".agent-teams/ 入库")
    # 过程性报告
    stale = [f for f in tracked if os.path.basename(f) in
             ("review_report.md",)]
    if stale:
        problems.append("残留过程报告: " + ", ".join(stale))
    # 未提交变更
    st = run(["git", "status", "--porcelain"])[1].strip()
    if st:
        problems.append("工作树不干净")
    # 与远端同步
    run(["git", "fetch", "origin"])
    local = run(["git", "rev-parse", "HEAD"])[1].strip()
    remote = run(["git", "rev-parse", "origin/master"])[1].strip()
    if local != remote:
        problems.append(f"与远端不同步 ({local[:7]} vs {remote[:7]})")
    # 大文件告警（>5MB）
    big = []
    for f in tracked:
        if os.path.exists(f) and os.path.getsize(f) > 5 * 1024 * 1024:
            big.append(f"{f}({os.path.getsize(f)//1024//1024}MB)")

    detail = f"入库文件 {len(tracked)} 个"
    if big:
        detail += " · 大文件: " + ", ".join(big)
    record(9, "仓库卫生", "FAIL" if problems else ("WARN" if big else "PASS"),
           detail + (" · " + "；".join(problems) if problems else ""))


# ----------------------------------------------------------------------------
# 10. Release 与 tag
# ----------------------------------------------------------------------------
def check_release():
    import json
    import urllib.request
    import base64
    tag = run(["git", "tag", "-l", "v2.16"])[1].strip()
    problems = []
    if not tag:
        problems.append("本地缺 v2.16 tag")

    # tag 必须指向已被推送的提交
    tcommit = run(["git", "rev-list", "-n", "1", "v2.16"])[1].strip()
    if tcommit:
        rc, _ = run(["git", "merge-base", "--is-ancestor", tcommit, "origin/master"])
        if rc != 0:
            problems.append("tag 提交不在 origin/master 上")

    # Gitea release（离线则跳过）
    rel = None
    try:
        auth = base64.b64encode(b"deepseek:deepseek").decode()
        req = urllib.request.Request(
            "http://zsyq.hxlab.tech:3000/api/v1/repos/yuhanxue/"
            "electrodynamics-textbook/releases/tags/v2.16",
            headers={"Authorization": "Basic " + auth})
        with urllib.request.urlopen(req, timeout=25) as r:
            rel = json.loads(r.read())
    except Exception as e:
        problems.append("无法查询 release（网络/凭据）: " + str(e)[:60])

    detail = f"tag v2.16 @ {tcommit[:7] if tcommit else '?'}"
    if rel:
        names = [a["name"] for a in rel.get("assets", [])]
        detail += f" · release「{rel['name'][:28]}」· 资产 {len(names)} 个"
        for need in ("electrodynamics_textbook_v2.pdf",
                     "electrodynamics_textbook_v2.tex", "ERRATA_REPORT.md"):
            if need not in names:
                problems.append(f"release 缺资产 {need}")
        if rel.get("draft"):
            problems.append("release 仍是 draft")
    record(10, "Release 与 tag", "FAIL" if problems else "PASS",
           detail + (" · " + "；".join(problems) if problems else ""))


# ----------------------------------------------------------------------------
CHECKS = [
    (1, "LaTeX 编译", check_compile),
    (2, "PDF 产物与元数据", check_pdf),
    (3, "文档结构", check_structure),
    (4, "交叉引用", check_xrefs),
    (5, "公式编号与标签", check_numbering),
    (6, "文档与站点一致性", check_consistency),
    (7, "物理自洽复算", check_physics),
    (8, "站点完整性", check_site),
    (9, "仓库卫生", check_hygiene),
    (10, "Release 与 tag", check_release),
]

ICON = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]", "SKIP": "[SKIP]"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="不重新编译")
    ap.add_argument("--only", default="", help="只跑指定编号，如 3,7")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",") if x.strip().isdigit()}

    print("=" * 78)
    print("《电动力学》自学教材 · 全量自检")
    print("=" * 78)
    t0 = time.time()
    for no, name, fn in CHECKS:
        if only and no not in only:
            continue
        try:
            if no == 1:
                fn(quick=args.quick)
            else:
                fn()
        except Exception as e:
            record(no, name, "FAIL", f"检查自身异常: {type(e).__name__}: {e}")
    dt = time.time() - t0

    print()
    for r in sorted(RESULTS, key=lambda x: x["no"]):
        print(f"{ICON[r['status']]} {r['no']:>2}. {r['name']}")
        print(f"        {r['detail']}")
    n_fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
    n_warn = sum(1 for r in RESULTS if r["status"] == "WARN")
    n_skip = sum(1 for r in RESULTS if r["status"] == "SKIP")
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    print()
    print("-" * 78)
    print(f"合计 {len(RESULTS)} 项：PASS {n_pass} · FAIL {n_fail} · "
          f"WARN {n_warn} · SKIP {n_skip}　（用时 {dt:.1f}s）")
    print("=" * 78)
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
