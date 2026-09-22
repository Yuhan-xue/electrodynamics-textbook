/* ==========================================================================
   电动力学 · 配套站点 —— 共享行为层
   所有内容在无 JS 时均可读；本文件只做渐进增强。
   依赖：book-data.js（window.BOOK）
   ========================================================================== */
(function () {
  'use strict';

  var BOOK = window.BOOK || { facts: {}, chapters: [] };

  /* ---------- 工具 ---------- */
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function chapterLabel(c) {
    if (c.kind === 'chapter') return '第' + c.number + '章';
    if (c.kind === 'appendix') return '附录' + c.letter;
    return '前置';
  }

  /* ---------- PDF 路径（页面在 html/ 下，PDF 在仓库根） ---------- */
  var PDF = '../electrodynamics_textbook_v2.pdf';
  function pdfPage(p) { return PDF + '#page=' + p + '&zoom=page-width'; }

  /* ---------- 1. 阅读器：真实目录 + PDF 定位 ---------- */
  function initReader() {
    var tocHost = $('#tocPane');
    var frame = $('#pdfFrame');
    if (!tocHost) return;

    var groups = { front: [], chapter: [], appendix: [] };
    BOOK.chapters.forEach(function (c) { (groups[c.kind] || groups.chapter).push(c); });

    var groupTitles = { front: '前置', chapter: '正文', appendix: '附录' };
    var order = ['front', 'chapter', 'appendix'];

    order.forEach(function (kind) {
      var list = groups[kind];
      if (!list || !list.length) return;
      var ul = el('ul', { class: 'toc-list' });
      list.forEach(function (c) {
        var a = el('a', {
          href: pdfPage(c.page),
          'data-page': String(c.page),
          target: 'pdfFrame'
        }, [
          el('span', { text: chapterLabel(c) + '　' + c.title }),
          el('span', { class: 'pg', text: 'p.' + c.page })
        ]);
        ul.appendChild(el('li', null, [a]));

        // 章内小节（折叠在章下，保持目录可扫读）
        if (c.sections && c.sections.length) {
          var sub = el('ul', { class: 'toc-list', style: 'margin-left:.85rem' });
          c.sections.forEach(function (s) {
            sub.appendChild(el('li', null, [
              el('a', {
                href: pdfPage(s.page), 'data-page': String(s.page), target: 'pdfFrame'
              }, [
                el('span', { text: s.title }),
                el('span', { class: 'pg', text: s.page })
              ])
            ]));
          });
          ul.appendChild(el('li', null, [sub]));
        }
      });
      var g = el('div', { class: 'toc-group' }, [
        el('h3', { text: groupTitles[kind] }), ul
      ]);
      tocHost.appendChild(g);
    });

    // 点击目录项：同步 iframe（target 已处理），并高亮当前项
    tocHost.addEventListener('click', function (ev) {
      var a = ev.target.closest('a[data-page]');
      if (!a) return;
      $$('#tocPane a[aria-current]').forEach(function (x) { x.removeAttribute('aria-current'); });
      a.setAttribute('aria-current', 'true');
      var pg = $('#curPage');
      if (pg) pg.textContent = 'p.' + a.dataset.page;
    });

    // 上一章 / 下一章
    var flat = [];
    BOOK.chapters.forEach(function (c) { flat.push({ title: chapterLabel(c) + ' ' + c.title, page: c.page }); });
    var idx = 0;

    function go(d) {
      var n = idx + d;
      if (n < 0 || n >= flat.length) return;
      idx = n;
      var t = flat[idx];
      if (frame) frame.src = pdfPage(t.page);
      var info = $('#chapterInfo');
      if (info) info.textContent = t.title;
      var pg = $('#curPage');
      if (pg) pg.textContent = 'p.' + t.page;
      var prev = $('#prevBtn'), next = $('#nextBtn');
      if (prev) prev.disabled = idx === 0;
      if (next) next.disabled = idx === flat.length - 1;
      var match = $('#tocPane a[data-page="' + t.page + '"]');
      if (match) {
        $$('#tocPane a[aria-current]').forEach(function (x) { x.removeAttribute('aria-current'); });
        match.setAttribute('aria-current', 'true');
      }
    }
    var prev = $('#prevBtn'), next = $('#nextBtn');
    if (prev) prev.addEventListener('click', function () { go(-1); });
    if (next) next.addEventListener('click', function () { go(1); });

    document.addEventListener('keydown', function (e) {
      if (e.target.matches('input, textarea, select')) return;
      if (e.key === 'ArrowLeft') go(-1);
      if (e.key === 'ArrowRight') go(1);
    });

    if (frame) frame.src = pdfPage(flat[0].page);
    var info = $('#chapterInfo');
    if (info) info.textContent = flat[0].title;
    if (prev) prev.disabled = true;
  }

  /* ---------- 2. 首页：事实数字 ---------- */
  function initFacts() {
    $$('[data-fact]').forEach(function (n) {
      var key = n.dataset.fact;
      var v = BOOK.facts[key];
      if (v !== undefined) n.textContent = String(v);
    });
  }

  /* ---------- 3. 进度：本地存储 ---------- */
  function initProgress() {
    var boxes = $$('input[data-progress]');
    if (!boxes.length) return;
    var KEY = 'edyn.progress.v2';
    var saved = [];
    try { saved = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { saved = []; }

    function sync() {
      var done = boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.dataset.progress; });
      try { localStorage.setItem(KEY, JSON.stringify(done)); } catch (e) { /* 隐私模式：忽略 */ }
      var bar = $('#progressBar > span');
      var txt = $('#progressText');
      var pct = Math.round(done.length / boxes.length * 100);
      if (bar) bar.style.width = pct + '%';
      if (txt) txt.textContent = '已完成 ' + done.length + ' / ' + boxes.length + '（' + pct + '%）';
    }
    boxes.forEach(function (b) {
      b.checked = saved.indexOf(b.dataset.progress) !== -1;
      b.addEventListener('change', sync);
    });
    sync();
  }

  /* ---------- 4. 单位制换算（SI ⇄ 高斯） ---------- */
  // 因子由基本定义独立推导（脚本 .build/verify_units.py 可重跑）：
  //   1 statC：两个 1 statC 点电荷相距 1 cm 斥力为 1 dyn
  //            ⇒ 1 statC = 3.335641×10⁻¹⁰ C ⇔ 1 C = 2.99792458×10⁹ statC
  //            （与 e = 4.803205×10⁻¹⁰ esu 交叉验证，比值 1.000000）
  //   1 statV = 1 erg/statC = 299.792458 V ⇒ 1 V/m = 3.33564095×10⁻⁵ statV/cm
  //   高斯制 ∇·E = 4πρ、D = E + 4πP、B = H + 4πM（教材附录 D 自述，tex 8414–8415）
  //        ⇒ D 带 4π、P 不带；1 Oe 由「真空中 H[Oe] = B[G]」定义 ⇒ 1 Oe = 79.577472 A/m
  //   磁化强度按磁矩密度：1 A·m² = 10³ emu，1 m³ = 10⁶ cm³ ⇒ 1 A/m = 10⁻³ emu/cm³
  //   物理自检：σ = 1 C/m² 的无限大带电面，两条路径给出同一个 E
  //            （SI 算完再换算 vs 高斯制直接 4πσ_G），比值 1.00000000
  var C_STAT = 2.99792458e9;   // 1 C = C_STAT statC
  var UNIT_FACTORS = {
    E:   { f: 1e6 / 2.99792458e10,        unitSI: 'V/m',  unitCGS: 'statV/cm',  name: '电场强度 E' },
    D:   { f: 4 * Math.PI * C_STAT / 1e4, unitSI: 'C/m²', unitCGS: 'statC/cm²', name: '电位移 D' },
    P:   { f: C_STAT / 1e4,               unitSI: 'C/m²', unitCGS: 'statC/cm²', name: '极化强度 P' },
    B:   { f: 1e4,                        unitSI: 'T',    unitCGS: 'G',         name: '磁感应强度 B' },
    H:   { f: 4 * Math.PI * 1e-3,         unitSI: 'A/m',  unitCGS: 'Oe',        name: '磁场强度 H' },
    M:   { f: 1e-3,                       unitSI: 'A/m',  unitCGS: 'emu/cm³',   name: '磁化强度 M' },
    Q:   { f: C_STAT,                     unitSI: 'C',    unitCGS: 'statC',     name: '电荷 q' },
    Phi: { f: 1e8,                        unitSI: 'Wb',   unitCGS: 'Mx',        name: '磁通量 Φ' }
  };

  // 启动时自检：任一因子偏离预期即在控制台告警（防止再次出现量级错误）
  (function selfCheck() {
    var expect = { E: 3.33564095e-5, D: 3.76730314e6, P: 2.99792458e5, B: 1e4,
                   H: 1.25663706e-2, M: 1e-3, Q: 2.99792458e9, Phi: 1e8 };
    Object.keys(expect).forEach(function (k) {
      var got = UNIT_FACTORS[k].f;
      if (Math.abs(got / expect[k] - 1) > 1e-6) {
        if (window.console && console.error) {
          console.error('[单位换算] 因子校验失败 ' + k + ': 实际 ' + got + '，预期 ' + expect[k]);
        }
      }
    });
  })();

  function initUnitTool() {
    var host = $('#unitTool');
    if (!host) return;

    function build(direction) {
      var qtySel = $('#uQty' + direction), valIn = $('#uVal' + direction);
      var out = $('#uOut' + direction);
      if (!qtySel) return;

      Object.keys(UNIT_FACTORS).forEach(function (k) {
        qtySel.appendChild(el('option', { value: k, text: UNIT_FACTORS[k].name }));
      });

      function unitLabels() {
        var d = UNIT_FACTORS[qtySel.value];
        $('#uFrom' + direction).textContent = direction === 'SI' ? d.unitSI : d.unitCGS;
        $('#uTo' + direction).textContent = direction === 'SI' ? d.unitCGS : d.unitSI;
      }
      qtySel.addEventListener('change', function () { unitLabels(); out.textContent = ''; });
      unitLabels();

      var btn = $('#uGo' + direction);
      if (btn) btn.addEventListener('click', function () {
        var d = UNIT_FACTORS[qtySel.value];
        var v = parseFloat(valIn.value);
        if (!isFinite(v)) { out.innerHTML = '<span class="err">请输入有效数值。</span>'; return; }
        var r = direction === 'SI' ? v * d.f : v / d.f;
        out.innerHTML = '<span class="val">' + fmt(r) + '</span> ' +
          (direction === 'SI' ? d.unitCGS : d.unitSI);
      });
    }
    build('SI');
    build('GS');
  }

  function fmt(x) {
    if (x === 0) return '0';
    var a = Math.abs(x);
    if (a >= 1e6 || a < 1e-4) return x.toExponential(6).replace(/e([+-])(\d+)/, '×10^$1$2');
    return String(parseFloat(x.toPrecision(7)));
  }

  /* ---------- 5. 电磁波参数 ---------- */
  function initWaveTool() {
    var host = $('#waveTool');
    if (!host) return;
    var C = 299792458;

    var known = $('#wKnown'), val = $('#wVal'), med = $('#wMed'), out = $('#wOut');
    var custom = $('#wCustom');

    med.addEventListener('change', function () {
      if (custom) custom.hidden = med.value !== 'custom';
    });

    function epsMu() {
      if (med.value === 'custom') {
        var er = parseFloat($('#wEr').value), ur = parseFloat($('#wUr').value);
        return { er: isFinite(er) ? er : 1, ur: isFinite(ur) ? ur : 1 };
      }
      var table = { vacuum: [1, 1], air: [1.0006, 1], water: [80, 1], glass: [4.0, 1] };
      var t = table[med.value] || [1, 1];
      return { er: t[0], ur: t[1] };
    }

    $('#wGo').addEventListener('click', function () {
      var v = parseFloat(val.value);
      if (!isFinite(v) || v <= 0) { out.innerHTML = '<span class="err">请输入正的数值。</span>'; return; }
      var em = epsMu();
      var vp = C / Math.sqrt(em.er * em.ur);   // 相速
      var f, lam, k;
      if (known.value === 'f')      { f = v; lam = vp / f; k = 2 * Math.PI / lam; }
      else if (known.value === 'lambda') { lam = v; f = vp / lam; k = 2 * Math.PI / lam; }
      else                          { k = v; lam = 2 * Math.PI / k; f = vp / lam; }

      var z0 = 376.730313668;
      var z = z0 * Math.sqrt(em.ur / em.er);
      out.innerHTML =
        '<div>频率 <span class="val">' + fmt(f) + '</span> Hz</div>' +
        '<div>波长 <span class="val">' + fmt(lam) + '</span> m</div>' +
        '<div>波数 <span class="val">' + fmt(k) + '</span> rad/m</div>' +
        '<div>相速 <span class="val">' + fmt(vp) + '</span> m/s　' +
        '<span class="hint">（真空 2.998×10⁸ m/s 的 ' + (vp / C * 100).toFixed(4) + '%）</span></div>' +
        '<div>波阻抗 <span class="val">' + fmt(z) + '</span> Ω</div>';
    });

    // 频率 ↔ 波长 快捷对照
    var ref = $('#wRef');
    if (ref) {
      var rows = [
        ['工频', 50], ['中波广播', 1e6], ['调频广播', 1e8],
        ['WiFi 2.4G', 2.4e9], ['可见光 550nm', C / 550e-9],
        ['X 射线 0.1nm', C / 0.1e-9]
      ];
      var tb = el('tbody');
      rows.forEach(function (r) {
        tb.appendChild(el('tr', null, [
          el('td', { text: r[0] }),
          el('td', { class: 'num', text: fmt(r[1]) }),
          el('td', { class: 'num', text: fmt(C / r[1]) })
        ]));
      });
      ref.appendChild(tb);
    }
  }

  /* ---------- 6. 矢量运算 ---------- */
  function readVec(ids) {
    var v = ids.map(function (id) { var n = $('#' + id); return n ? parseFloat(n.value) : NaN; });
    return v.every(function (x) { return isFinite(x); }) ? v : null;
  }
  function showVec(node, label, v, unit) {
    node.innerHTML = label + ' = (' +
      v.map(function (x) { return '<span class="val">' + fmt(x) + '</span>'; }).join(', ') +
      ')' + (unit ? ' ' + unit : '');
  }

  function initVectorTool() {
    var host = $('#vectorTool');
    if (!host) return;

    // 标签页
    $$('.tab', host).forEach(function (tab) {
      tab.addEventListener('click', function () {
        $$('.tab', host).forEach(function (t) { t.setAttribute('aria-selected', 'false'); });
        tab.setAttribute('aria-selected', 'true');
        $$('[role="tabpanel"]', host).forEach(function (p) { p.hidden = true; });
        var panel = $('#' + tab.getAttribute('aria-controls'));
        if (panel) panel.hidden = false;
      });
    });

    var out1 = $('#vecOut1'), out2 = $('#vecOut2');

    $('#vecNorm').addEventListener('click', function () {
      var a = readVec(['ax', 'ay', 'az']);
      if (!a) { out1.innerHTML = '<span class="err">请填满三个分量。</span>'; return; }
      var n = Math.hypot(a[0], a[1], a[2]);
      out1.innerHTML = '|A| = <span class="val">' + fmt(n) + '</span>' +
        (n > 0 ? '　单位矢量 Â = (' + a.map(function (x) { return '<span class="val">' + fmt(x / n) + '</span>'; }).join(', ') + ')' : '');
    });

    $('#vecDot').addEventListener('click', function () {
      var a = readVec(['a2x', 'a2y', 'a2z']), b = readVec(['b2x', 'b2y', 'b2z']);
      if (!a || !b) { out2.innerHTML = '<span class="err">请填满两组分量。</span>'; return; }
      var d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
      var na = Math.hypot(a[0], a[1], a[2]), nb = Math.hypot(b[0], b[1], b[2]);
      var ang = (na > 0 && nb > 0) ? Math.acos(Math.max(-1, Math.min(1, d / (na * nb)))) * 180 / Math.PI : NaN;
      out2.innerHTML = 'A·B = <span class="val">' + fmt(d) + '</span>' +
        (isFinite(ang) ? '<div>夹角 θ = <span class="val">' + ang.toFixed(4) + '°</span></div>' : '');
    });

    $('#vecCross').addEventListener('click', function () {
      var a = readVec(['a2x', 'a2y', 'a2z']), b = readVec(['b2x', 'b2y', 'b2z']);
      if (!a || !b) { out2.innerHTML = '<span class="err">请填满两组分量。</span>'; return; }
      var c = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
      var wrap = el('div');
      showVec(wrap, 'A×B', c);
      wrap.appendChild(el('div', {
        html: '<span class="hint">|A×B| = ' + fmt(Math.hypot(c[0], c[1], c[2])) + '</span>'
      }));
      out2.innerHTML = '';
      out2.appendChild(wrap);
    });
  }

  /* ---------- 7. 勘误页：章节下拉据实生成 ---------- */
  function initErrataForm() {
    var sel = $('#errChapter');
    if (!sel) return;
    BOOK.chapters.forEach(function (c) {
      sel.appendChild(el('option', {
        value: chapterLabel(c) + ' ' + c.title,
        text: chapterLabel(c) + ' ' + c.title + '（p.' + c.page + '）'
      }));
    });
    var form = $('#errataForm');
    if (form) form.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = $('#errataMsg');
      if (msg) {
        msg.hidden = false;
        msg.textContent = '已在本机记录（演示模式，未发送到服务器）。真实反馈请提交到 Git 仓库 Issue。';
      }
      form.reset();
    });
  }

  /* ---------- 启动 ---------- */
  function boot() {
    initFacts();
    initReader();
    initProgress();
    initUnitTool();
    initWaveTool();
    initVectorTool();
    initErrataForm();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
