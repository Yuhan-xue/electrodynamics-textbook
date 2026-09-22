# -*- coding: utf-8 -*-
"""
Publish the v2.16 release on the Gitea instance, with release notes and
attached assets (PDF + LaTeX source + errata report).

Run from the repository root:  python tools/site/publish_release.py
"""
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

BASE = "http://zsyq.hxlab.tech:3000/api/v1"
REPO = "yuhanxue/electrodynamics-textbook"
USER, PASSWORD = "deepseek", "deepseek"
TAG = "v2.16"
NAME = "v2.16 独立复核与勘误：修正 52 项（含 2 blocker）"

AUTH = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


def api(method, path, payload=None, raw=None, content_type=None):
    url = BASE + path
    data = None
    headers = {"Authorization": "Basic " + AUTH}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = content_type or "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)


BODY = """\
《电动力学》自学教材 **v2.16**——独立复核与勘误版。

## 本版规格

| 项目 | 数值 |
|---|---|
| 页数 | **179**（上一版 172，新增内容 +7） |
| 正文 | 10 章 + 9 个附录 |
| 例题 | 50 道（基础 21 / 提高 24 / 挑战 5） |
| 定理 / 定义 | 64 / 28 |
| 综合练习题 | 50 道（全部附 [分析]+[解答]+[量纲校验]） |

**编译验证**：0 错误 · 0 Overfull · 0 Underfull · 0 未定义引用 · 0 缺失字形

## 本轮修正 52 项（2 blocker / 10 high / 40 medium+low）

已修正全部 blocker 与关键 high，无遗留项（唯一一项刻意保留，见文末）。

### blocker

- **第10章对同一个不变量给出两个相反的值**：重复定理把 `F_μνF^μν` 写成 `2(E²/c²−B²)`，
  而本章其余 5 处一致为 `2(B²−E²/c²)`；连带的「不变量符号→场型」结论表**三条全部反向**。
- **配套站点单位换算器 5 个因子错量级**（E 小 10⁶、D 大 100、P 错 4π、H 取倒数、M 大 79577）。
  已按基本定义重推全部 8 个因子，并加入加载时自检。

### high（节选）

- **§7.1.5 整节（含小节标题）被包在默认关闭的可折叠图层内**——含洛伦兹规范定义、
  两规范对比表与达朗贝尔方程。
- **全部 17 个图层缺 `/Usage` 字典** ⇒ 打印/导出会丢失 10 组自测答案、6 个挑战题块与 §7.1.5。
  改用 `[printocg=always]` 修复，现 17/17 均为 `PrintState=/ON`。
- **TE₁₀ 主模的 `H_z` 符号错**（`+i` 应为 `−i`）：印出的三分量不能同时满足 Faraday 与 Ampere。
- **洛伦兹色散 `dn/dω` 漏掉决定符号的因子**：原式恒正，无法得出同段要求的反常色散。
- **铁磁平面例题把 H 的法向性误记为「B 只有法向分量」**。
- **附录 D 电荷换算方向与数值双错**，且与同句的数值自相矛盾。
- **第1章章首学习路径 8 处小节号全错**；**正电荷处电势高低说反了**。

### 新增内容（两处「承诺未交付」补齐）

- **新增 §4.4 格林函数法**：该方法原被列为第4章三大方法之一并在自测中考查，
  却全章无推导无例题。新节含定义、由格林第二恒等式导出的形式解、
  Dirichlet/Neumann 两种边界条件处理（含 Neumann 不能取 `∂G/∂n=0` 的理由）、
  「镜像法=最简单的格林函数构造」的洞见，以及接地导体球格林函数完整例题。
- **新增 §9.3 天线方向性与方向图**：原两处承诺「天线方向性」、自测考 `F(θ,φ)`，
  但全书从未定义 `F`。新节给出定义、三种天线方向性函数、方向性系数 `D=4π/∮F dΩ`
  （偶极 1.5、半波 1.64）。

### 其他修正

动量守恒方程符号、柱坐标分离变量二维/三维情形混淆、位移电流定义统一、
波导例题简并判断（`b=a/2` 实为标准设计点而非应避开）、附录 E 两条辐射功率比例式
各漏一个 `c` 的幂、附录 C 常数表补 `ħ`/`Z₀`、边界条件 `n̂` 一符两义、
术语统一（`ρ_b`/`J_M`/李纳--维谢尔）、附录 H 第1章答案行缺漏。

## 复核方法

- **不采信仓库自述**：对 v2.15 声称的关键 8 项修正全部重新独立验证
  （结论：**全部正确**——束缚电荷符号、超导球磁场、达朗贝尔算符 9 处统一、
  交流电容器坡印廷功率、辐射功率 17.33 W、εFF 系数、F^{i0} 符号、TE₁₀ 表面电流）。
- **数值与符号结论一律独立复算**，每条附可重跑脚本（见 `tools/audit/`，共 21 个）。
- **可证伪性优先**：每条问题至少给出一个独立判据（反例、量纲、极限、物理自洽性）。
- **发现并撤回 1 条自己的误报**：曾称速查表 `B = μ(H+M)` 与正文矛盾，
  经打印精确源码确认原文是宏 `\\muz`（=`\\mu_0`），该行本来正确。误报已撤回，
  并把「凡涉及自定义宏必须先展开」写入 `STYLE_GUIDE.md`。

## 配套站点

`html/` 为按**编译产物实测目录**重建的交互站点（上一版站点描述的是一本不同的书，
章节目录含「传输线/波导/等离子体」，且 PDF 阅读器从未加载 PDF、勘误页为虚构数据）。
现站点含：在线阅读（真实目录 + 可用 PDF 定位）、学习路线、公式速查、计算工具、勘误记录。
7 页面链接零断裂，配色对比度全部达 WCAG AA，导航数据由编译产物自动生成。

## 一项刻意保留未改

附录 I「教材章节对照表」中郭硕鸿《电动力学》的具体章序：离线环境无法核实原书目录，
故未擅自改动数字，改为在表前加显著提示「章号随版次而异，应以各书目录为准」。
**这是刻意保留而非遗漏**。

---

*修正明细逐条列于 `ERRATA_REPORT.md` 与站点 `html/errata.html`（33 条结构化条目，含原文、问题分析、修正方案与判据）。*
"""


def main():
    # ---- 1. create the release (if it does not exist yet) ----
    st, rel = api("GET", f"/repos/{REPO}/releases/tags/{TAG}")
    if st == 200 and isinstance(rel, dict):
        print(f"release {TAG} already exists (id={rel['id']}); will only upload assets")
        rid = rel["id"]
    else:
        st, rel = api("POST", f"/repos/{REPO}/releases", {
            "tag_name": TAG,
            "target_commitish": "master",
            "name": NAME,
            "body": BODY,
            "draft": False,
            "prerelease": False,
        })
        if st not in (200, 201):
            print("FAILED to create release:", st, rel)
            sys.exit(1)
        rid = rel["id"]
        print(f"created release {TAG} (id={rid})")

    # ---- 2. upload assets ----
    assets = [
        ("electrodynamics_textbook_v2.pdf", "《电动力学》v2.16 完整教材（179 页，PDF）"),
        ("electrodynamics_textbook_v2.tex", "LaTeX 源文件（XeLaTeX 可编译）"),
        ("ERRATA_REPORT.md", "独立复核与勘误报告"),
    ]
    for path, label in assets:
        if not os.path.exists(path):
            print(f"  SKIP {path} (missing)")
            continue
        raw = io.open(path, "rb").read()
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        name = os.path.basename(path)
        st, resp = api(
            "POST",
            f"/repos/{REPO}/releases/{rid}/assets?name={urllib.parse.quote(name)}",
            raw=raw, content_type=ctype,
        )
        if st in (200, 201):
            print(f"  uploaded {name}  ({len(raw)/1024:.0f} KB)")
        else:
            print(f"  upload FAILED {name}: {st} {str(resp)[:200]}")

    # ---- 3. report final state ----
    st, rel = api("GET", f"/repos/{REPO}/releases/tags/{TAG}")
    if st == 200:
        print()
        print("=== release state ===")
        print("  tag      :", rel["tag_name"])
        print("  name     :", rel["name"])
        print("  url      :", rel.get("html_url"))
        print("  draft    :", rel["draft"], "| prerelease:", rel["prerelease"])
        print("  assets   :")
        for a in rel.get("assets", []):
            print(f"     - {a['name']}  ({a['size']/1024:.0f} KB)  {a['browser_download_url']}")


if __name__ == "__main__":
    main()
