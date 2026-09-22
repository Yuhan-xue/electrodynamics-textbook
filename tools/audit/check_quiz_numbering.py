# -*- coding: utf-8 -*-
"""Check which enumerate numbering each quiz section uses, to see whether the
reader-visible question numbers are continuous across 一/二/三."""
import io, re

s = io.open('electrodynamics_textbook_v2.tex', encoding='utf-8').read()
q = re.compile(r'\\section\*\{第(\d+)章随堂自测\}(.*?)\\end\{miniquiz\}', re.S)

for m in q.finditer(s):
    ch = m.group(1)
    body = m.group(2)
    opts = re.findall(r'\\begin\{enumerate\}(?:\[([^\]]*)\])?', body)
    print(f'第{ch:>2}章 enumerate 选项（按出现顺序）:')
    for o in opts:
        print(f'        [{o}]')
