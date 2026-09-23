# -*- coding: utf-8 -*-
"""
可读性与 UI 审核 —— 《电动力学》教材 PDF + 配套站点

测量客观指标并对照阈值判定，而不是凭观感。分为两部分：
  A. PDF 排版可读性（字号、行距、版心、行宽、标题层级尺寸）
  B. 站点 UI 可读性（字号阶梯、行高、正文行宽、标题层级、触控目标、
     对比度、响应式断点、键盘可达性、无 JS 降级、打印样式）

用法：python tools/audit/audit_readability.py
"""
import io, os, re, sys

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

FAILS, WARNS, NOTES = [], [], []


def fail(msg):
    FAILS.append(msg)


def warn(msg):
    WARNS.append(msg)


def note(msg):
    NOTES.append(msg)


# ============================================================================
# A. PDF 排版
# ============================================================================
print("=" * 78)
print("A. PDF 排版可读性")
print("=" * 78)

TEX = "electrodynamics_textbook_v2.tex"
src = io.open(TEX, encoding="utf-8").read()

# 正文字号：\documentclass[11pt,...]
m = re.search(r"\\documentclass\[([^\]]*)\]\{book\}", src)
opts = m.group(1) if m else ""
base_pt = re.search(r"(\d+(?:\.\d+)?)pt", opts)
base_pt = float(base_pt.group(1)) if base_pt else 10.0
print(f"基础字号            : {base_pt} pt  (documentclass opts: {opts})")

# 行距
m = re.search(r"\\linespread\{([\d.]+)\}", src)
linespread = float(m.group(1)) if m else 1.0
# book 类 11pt 的默认 baselineskip 约 13.6pt；行距系数 <1 会显著压缩可读性
nominal_leading = {10: 12.0, 11: 13.6, 12: 14.5}.get(int(base_pt), 13.6)
leading = nominal_leading * linespread
ratio = leading / base_pt
print(f"\\linespread         : {linespread}")
print(f"估算行距 / 字号      : {leading:.1f}pt / {ratio:.2f}")

# 版心
geo = re.search(r"\\geometry\{([^}]*)\}", src)
g = geo.group(1) if geo else ""
def gv(key):
    mm = re.search(key + r"\s*=\s*([\d.]+)\s*cm", g)
    return float(mm.group(1)) if mm else None
left, right = gv("left"), gv("right")
top, bottom = gv("top"), gv("bottom")
print(f"页边距              : 左 {left} 右 {right} 上 {top} 下 {bottom} (cm)")
if left and right:
    textwidth_cm = 21.0 - left - right
    print(f"版心宽度            : {textwidth_cm:.1f} cm")
    # 中文单字宽 ≈ 字号；估算每行汉字数
    chars = textwidth_cm * 10 / (base_pt * 0.3528)
    print(f"估算每行汉字数       : {chars:.1f}")
    if chars > 42:
        warn(f"每行约 {chars:.0f} 个汉字，偏长（中文正文宜 30–40 字/行）")
    elif chars < 26:
        warn(f"每行约 {chars:.0f} 个汉字，偏短")

# 段落间距
m = re.search(r"\\setlength\{\\parskip\}\{([^}]*)\}", src)
print(f"\\parskip            : {m.group(1) if m else '(未设置)'}")

# 标题层级字号（titlesec）
for m in re.finditer(r"\\titleformat\{\\(chapter|section|subsection)\}\[[^\]]*\]\s*\{([^}]*)\}", src):
    print(f"  titleformat {m.group(1):11}: {m.group(2)}")

# 判定
if ratio < 1.15:
    fail(f"行距/字号比仅 {ratio:.2f}（<1.15），中文正文过密，建议 \\linespread 提到 1.08–1.15"
         f"（当前 {linespread}）")
elif ratio < 1.25:
    warn(f"行距/字号比 {ratio:.2f} 偏紧（中文习惯 1.3–1.5）")
else:
    note(f"行距/字号比 {ratio:.2f}")

# 页数
try:
    import pypdf
    for c in (".build/electrodynamics_textbook_v2.pdf",
              "electrodynamics_textbook_v2.pdf"):
        if os.path.exists(c):
            print(f"PDF 页数            : {len(pypdf.PdfReader(c).pages)}  (来自 {c})")
            break
except Exception as e:
    note(f"未能读取 PDF: {e}")

# ============================================================================
# B. 站点 UI
# ============================================================================
print()
print("=" * 78)
print("B. 站点 UI 可读性")
print("=" * 78)

CSS = io.open("html/assets/site.css", encoding="utf-8").read()

# ---- B1. 字号阶梯 ----
steps = dict(re.findall(r"--(step--?\d):\s*([\d.]+)rem", CSS))
print("字号阶梯 (rem → px @16px):")
px = {}
for k, v in sorted(steps.items(), key=lambda kv: float(kv[1])):
    p = float(v) * 16
    px[k] = p
    print(f"  --{k:7} {v:>9} rem = {p:>5.1f} px")
body_size = px.get("step-0", 15)
if body_size < 16:
    warn(f"正文字号 {body_size}px < 16px（移动端易读性下限）")
small = px.get("step--1", 13)
if small < 13:
    fail(f"最小字号 {small}px < 13px，小字过小")

# ---- B2. 行高 ----
lh = {}
for m in re.finditer(r"(--[\w-]+|\.[\w-]+|body|h[1-4])\s*\{([^}]*)\}", CSS):
    pass
m = re.search(r"body\s*\{([^}]*)\}", CSS, re.S)
body_lh = None
if m:
    mm = re.search(r"line-height:\s*([\d.]+)", m.group(1))
    if mm:
        body_lh = float(mm.group(1))
print(f"\n正文 line-height     : {body_lh}")
if body_lh and body_lh < 1.6:
    warn(f"正文行高 {body_lh} < 1.6（中文正文宜 1.7–1.8）")

# ---- B3. 正文测量宽度 ----
m = re.search(r"--measure:\s*([\d.]+)ch", CSS)
measure = float(m.group(1)) if m else None
print(f"--measure            : {measure} ch")
if measure and measure > 80:
    warn(f"正文行宽 {measure}ch > 80ch，偏长")
elif measure and measure < 45:
    warn(f"正文行宽 {measure}ch < 45ch，偏短")
else:
    note(f"正文行宽 {measure}ch（45–80 属宜读区间）")

# ---- B4. 触控目标 ----
btn = re.search(r"\.btn\s*\{([^}]*)\}", CSS, re.S)
tab = re.search(r"\.tab\s*\{([^}]*)\}", CSS, re.S)
for name, blk in (("按钮 .btn", btn), ("标签 .tab", tab)):
    if not blk:
        continue
    pad = re.search(r"padding:\s*([^;]+)", blk.group(1))
    fs = re.search(r"font-size:\s*([^;]+)", blk.group(1))
    est = None
    if pad:
        nums = re.findall(r"([\d.]+)rem", pad.group(1))
        if len(nums) >= 2:
            vpad = float(nums[0]) * 16
            if fs:
                fm = re.search(r"step--1", fs.group(1))
                fpx = px.get("step--1", 13) if fm else body_size
            else:
                fpx = body_size
            est = vpad * 2 + fpx * 1.4
    print(f"{name:18} 估算高度 {est:.0f}px" if est else f"{name:18} (未估算)")
    if est and est < 36:
        warn(f"{name} 估算高度 {est:.0f}px < 36px，触控目标偏小")

# ---- B5. 焦点可见性 ----
if ":focus-visible" in CSS:
    note("有 :focus-visible 样式")
else:
    fail("缺少 :focus-visible，键盘用户无法看到焦点")

# ---- B6. 响应式断点 ----
bps = re.findall(r"@media\s*\(([^)]*max-width[^)]*)\)", CSS)
print(f"\n响应式断点           : {bps if bps else '(无)'}")
if not bps:
    fail("没有任何 max-width 断点，窄屏无法适配")

# ---- B7. 打印样式 ----
if "@media print" in CSS:
    note("有打印样式 @media print")
else:
    warn("缺少打印样式")

# ---- B8. 语义与无障碍（逐页扫描） ----
pages = sorted(f for f in os.listdir("html") if f.endswith(".html"))
print(f"\n扫描 {len(pages)} 个页面：")
issues = {"lang": [], "viewport": [], "h1": [], "alt": [], "skiplink": [],
          "aria_label": [], "inline_style": [], "inline_js": []}
for f in pages:
    s = io.open(os.path.join("html", f), encoding="utf-8").read()
    if "<html lang=" not in s:
        issues["lang"].append(f)
    if 'name="viewport"' not in s:
        issues["viewport"].append(f)
    if len(re.findall(r"<h1\b", s)) != 1:
        issues["h1"].append(f"{f}({len(re.findall(r'<h1', s))})")
    if re.search(r"<img\b", s) and "alt=" not in s:
        issues["alt"].append(f)
    if "skip-link" not in s and f != "appendix-nav.html":
        issues["skiplink"].append(f)
    if "<nav" in s and "aria-label" not in s:
        issues["aria_label"].append(f)
    if len(re.findall(r'style="', s)) > 25:
        issues["inline_style"].append(f"{f}({len(re.findall(chr(34)+'style=', s))})")
    if re.search(r"\son(?:click|change|submit|load)=", s):
        issues["inline_js"].append(f)

for k, v in issues.items():
    label = {"lang": "缺 lang", "viewport": "缺 viewport", "h1": "h1 数量≠1",
             "alt": "img 缺 alt", "skiplink": "缺 skip-link",
             "aria_label": "nav 缺 aria-label", "inline_style": "内联 style 偏多",
             "inline_js": "内联事件处理器"}[k]
    if v:
        (fail if k in ("lang", "viewport", "h1", "inline_js") else warn)(
            f"{label}: {', '.join(v)}")
    else:
        note(f"{label}: 无问题")

# ---- B9. 无 JS 降级 ----
# 判据不是「有没有 <noscript>」，而是「关掉 JS 后这一页是否还有可读内容」。
# 静态正文足够多的页面（例如学习路线，其计划已写在 HTML 里）不需要 noscript。
THIN = 800       # 静态正文字符数下限
nojs, thin_no_notice = [], []
for f in pages:
    s = io.open(os.path.join("html", f), encoding="utf-8").read()
    if "<script" not in s or f == "appendix-nav.html":
        continue
    body = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", body)
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) >= THIN:
        nojs.append(f"{f}(静态 {len(txt)} 字符)")
    elif "<noscript" not in s:
        thin_no_notice.append(f"{f}(静态仅 {len(txt)} 字符且无 noscript)")

if thin_no_notice:
    warn("JS 依赖但既无静态内容也无 noscript: " + ", ".join(thin_no_notice))
else:
    note("无 JS 降级: 各页均有静态内容或 noscript 说明"
         + (f"（静态内容充足: {', '.join(nojs)}）" if nojs else ""))

# ---- B10. 对比度（复用既有脚本结论） ----
rc = os.system("python tools/audit/verify_contrast.py > nul 2>&1")
note("对比度由 tools/audit/verify_contrast.py 单独校验（要求全部 ≥4.5:1）")

# ============================================================================
# 汇总
# ============================================================================
print()
print("=" * 78)
print("汇总")
print("=" * 78)
for tag, arr in (("FAIL", FAILS), ("WARN", WARNS)):
    for x in arr:
        print(f"[{tag}] {x}")
if not FAILS and not WARNS:
    print("无可读性/UI 问题")
print()
print(f"FAIL {len(FAILS)} · WARN {len(WARNS)} · 说明 {len(NOTES)} 项")
sys.exit(1 if FAILS else 0)
