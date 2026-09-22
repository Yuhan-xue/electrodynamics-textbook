# -*- coding: utf-8 -*-
"""
Audit Appendix H (随堂自测答案速查) against the actual quizzes:
for each chapter, count questions per section and compare with the key's
numbering. Reports real mismatches rather than assuming.
"""
import io, re

s = io.open('electrodynamics_textbook_v2.tex', encoding='utf-8').read()

# --- actual quizzes ---
quiz_pat = re.compile(r'\\section\*\{第(\d+)章随堂自测\}(.*?)\\end\{miniquiz\}', re.S)
quizzes = {}
for m in quiz_pat.finditer(s):
    ch = int(m.group(1))
    body = m.group(2)
    # split into the three labelled sections
    secs = re.split(r'\\textbf\{[一二三]、(\w+?)(?:（[^）]*）)?\}', body)
    # secs = [pre, name1, body1, name2, body2, ...]
    info = {}
    for i in range(1, len(secs) - 1, 2):
        name, blk = secs[i], secs[i + 1]
        n_items = len(re.findall(r'^\s*\\item', blk, re.M))
        # does each question carry an inline answer?
        n_ans = blk.count('\\begin{ocg}') + blk.count('\\underline')
        info[name] = (n_items, n_ans)
    quizzes[ch] = info

print(f"{'章':>4}  {'选择题':>16} {'判断题':>16} {'填空题/计算题':>18}")
for ch in sorted(quizzes):
    inf = quizzes[ch]
    def fmt(key):
        if key not in inf:
            return '-'
        n, a = inf[key]
        return f"{n}题/{a}内嵌答案"
    fill = inf.get('填空题') or inf.get('计算题') or (0, 0)
    print(f"{ch:>4}  {fmt('选择题'):>16} {fmt('判断题'):>16} {str(fill[0])+'题/'+str(fill[1])+'内嵌答案':>18}")

print()
print("=== Appendix H key rows ===")
i = s.find('\\chapter{随堂自测答案速查}')
tbl = s[i:i + 2600]
for row in re.findall(r'第\d+章[^\\]*&.*?\\\\', tbl):
    print('  ', row.strip()[:150])
