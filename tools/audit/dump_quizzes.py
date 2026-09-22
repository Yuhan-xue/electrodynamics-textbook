# -*- coding: utf-8 -*-
"""
Per chapter, list the inline answers in document order (these correspond 1:1
to the questions, since every question has exactly one 答案 block or underline).
This is enough to rebuild Appendix H with correct sequential numbering.
"""
import io, re

s = io.open('electrodynamics_textbook_v2.tex', encoding='utf-8').read()
quiz_pat = re.compile(r'\\section\*\{第(\d+)章随堂自测\}(.*?)\\end\{miniquiz\}', re.S)

for m in quiz_pat.finditer(s):
    ch = int(m.group(1))
    body = m.group(2)
    print('=' * 76)
    print(f'第{ch}章')
    print('=' * 76)

    # 1. explicit 答案 blocks, in order, tagged by section
    marks = []
    for mm in re.finditer(r'\\textbf\{([一二三])、[^}]*\}', body):
        marks.append((mm.start(), mm.group(1)))
    def section_of(pos):
        cur = '?'
        for p, k in marks:
            if p <= pos:
                cur = k
            else:
                break
        return cur

    n = 0
    for mm in re.finditer(r'答案[：:]\s*(.*?)\}', body, re.S):
        n += 1
        a = re.sub(r'\s+', ' ', mm.group(1)).strip()
        print(f'  {n:2d} [{section_of(mm.start())}] {a[:100]}')

    # 2. underlined inline answers (fill-in-the-blank), in order
    inl = [(mm.start(), mm.group(1).strip())
           for mm in re.finditer(r'\\underline\{([^}]*)\}', body) if mm.group(1).strip()]
    for pos, val in inl:
        n += 1
        print(f'  {n:2d} [{section_of(pos)}] (inline) {val[:80]}')
    print()
