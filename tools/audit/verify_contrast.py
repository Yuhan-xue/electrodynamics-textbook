# -*- coding: utf-8 -*-
"""
Compute WCAG 2.1 contrast ratios for the severity badge foregrounds against
their actual rendered backgrounds (badge bg = colour at 15% over the page bg),
in BOTH the light and dark schemes.
"""
def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rel_lum(rgb):
    r, g, b = (srgb_to_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(fg, bg):
    l1, l2 = rel_lum(fg), rel_lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def over(fg, bg, alpha):
    """composite fg at `alpha` over bg"""
    return tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))

AA = 4.5
print("=== LIGHT scheme (page bg #fbfaf7) ===")
page = hexc('#fbfaf7')
light = {
    'blocker': '#7a1414',
    'high':    '#8a3d10',
    'medium':  '#6b5310',
    'low':     '#4a545e',
    'old-high(before fix)': '#b4531a',
}
for name, c in light.items():
    fg = hexc(c)
    bg = over(fg, page, 0.15)
    r = contrast(fg, bg)
    print(f"  {name:22} fg={c}  bg={('#%02x%02x%02x' % bg)}  ratio={r:5.2f}  {'PASS' if r>=AA else 'FAIL'}")

print()
print("=== other light-scheme text tokens vs page bg ===")
for name, c in [('--ink', '#1b1c1e'), ('--ink-2', '#4a4d52'), ('--ink-3', '#767a80'),
                ('--accent', '#7a1f2b'), ('--e-field', '#c0392b'), ('--b-field', '#2f4b9b'),
                ('--k-vector', '#1f7a4d'), ('--energy', '#b06800')]:
    r = contrast(hexc(c), page)
    print(f"  {name:12} {c}  ratio={r:5.2f}  {'PASS' if r>=AA else 'FAIL'}")

print()
print("=== DARK scheme (page bg #14151a) ===")
page_d = hexc('#14151a')
dark = {'blocker': '#e07a7a', 'high': '#e09a5e', 'medium': '#cbb35f', 'low': '#9aa3ad'}
for name, c in dark.items():
    fg = hexc(c)
    bg = over(fg, page_d, 0.15)
    r = contrast(fg, bg)
    print(f"  {name:10} fg={c}  bg={('#%02x%02x%02x' % bg)}  ratio={r:5.2f}  {'PASS' if r>=AA else 'FAIL'}")
print()
print("  dark-scheme other tokens:")
for name, c in [('--ink', '#ecebe8'), ('--ink-2', '#b9bcc2'), ('--ink-3', '#8b8f96'),
                ('--accent', '#e79aa4'), ('--e-field', '#e8705f'), ('--b-field', '#7f9ce8'),
                ('--k-vector', '#5cbe8a'), ('--energy', '#dda43f')]:
    r = contrast(hexc(c), page_d)
    print(f"    {name:12} {c}  ratio={r:5.2f}  {'PASS' if r>=AA else 'FAIL'}")
