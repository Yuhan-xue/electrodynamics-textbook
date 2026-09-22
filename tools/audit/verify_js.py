# -*- coding: utf-8 -*-
"""Validate the JS in each html page (syntax only) using Node, and confirm the
errata data block parses."""
import io, os, re, subprocess, glob, sys, tempfile

ok = True
for f in sorted(glob.glob('html/*.html')) + ['html/assets/site.js', 'html/book-data.js']:
    s = io.open(f, encoding='utf-8').read()
    blocks = []
    if f.endswith('.js'):
        blocks.append(s)
    else:
        for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S):
            blocks.append(m.group(1))
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        tmp = os.path.join(tempfile.gettempdir(), '_dsh_syntax_check.js')
        io.open(tmp, 'w', encoding='utf-8').write(b)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        status = 'OK' if r.returncode == 0 else 'SYNTAX ERROR'
        if r.returncode != 0:
            ok = False
            print(f'{f} block#{i}: {status}')
            print('   ', (r.stderr or '').strip().split('\n')[0])
        else:
            print(f'{f} block#{i}: {status} ({len(b)} chars)')

# confirm the errata array literal evaluates and has the expected shape
s = io.open('html/errata.html', encoding='utf-8').read()
m = re.search(r'window\.ERRATA = (\[.*?\n\]);', s, re.S)
if m:
    io.open(os.path.join(tempfile.gettempdir(), '_dsh_errata_check.js'), 'w', encoding='utf-8').write(
        'global.window={};' + 'window.ERRATA = ' + m.group(1) + ';\n'
        'const e=window.ERRATA;'
        'console.log("entries",e.length);'
        'const ids=new Set(e.map(x=>x.id));'
        'console.log("uniqueIds",ids.size);'
        'console.log("missingFields",e.filter(x=>!x.id||!x.sev||!x.title||!x.issue||!x.fix||!x.status).length);'
        'const s={};e.forEach(x=>s[x.sev]=(s[x.sev]||0)+1);console.log("severity",JSON.stringify(s));'
        'const t={};e.forEach(x=>t[x.status]=(t[x.status]||0)+1);console.log("status",JSON.stringify(t));')
    r = subprocess.run(['node', os.path.join(tempfile.gettempdir(), '_dsh_errata_check.js')], capture_output=True, text=True)
    print('\n--- errata data check ---')
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        ok = False

print('\nALL OK' if ok else '\nPROBLEMS FOUND')
sys.exit(0 if ok else 1)
