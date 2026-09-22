# -*- coding: utf-8 -*-
"""
CH08-03 verification: the correct dn/domega for the Lorentz model, and whether
the book's printed formula can ever be negative.

Lorentz: chi = A / (w0^2 - w^2 - i gamma w),  A = N e^2/(eps0 m)
n = Re sqrt(1 + chi)
Book (tex 7039): Re chi = A (w0^2 - w^2)/D ,  D = (w0^2-w^2)^2 + gamma^2 w^2
                 dn/dw  = A * 2w / D                     <-- printed
Claimed near resonance: dn/dw < 0 (anomalous dispersion)
"""
import numpy as np

w0, gamma, A = 1.0, 0.08, 0.05

def Re_chi(w):
    D = (w0**2 - w**2)**2 + gamma**2 * w**2
    return A * (w0**2 - w**2) / D

def n_real(w):
    chi = A / (w0**2 - w**2 - 1j * gamma * w)
    return np.real(np.sqrt(1 + chi))

def numeric_dn(w, h=1e-6):
    return (n_real(w + h) - n_real(w - h)) / (2 * h)

def book_formula(w):
    D = (w0**2 - w**2)**2 + gamma**2 * w**2
    return A * 2 * w / D

def dRechi_dw(w):
    """Analytic derivative of Re chi (the -i gamma w term gives the extra piece)."""
    D = (w0**2 - w**2)**2 + gamma**2 * w**2
    return A * 2 * w * ((w0**2 - w**2)**2 - gamma**2 * w0**2) / D**2

print(f"w0={w0}, gamma={gamma}, A={A}")
print(f"{'w':>8} {'numeric dn/dw':>16} {'Rechi-approx':>16} {'book formula':>16}")
for w in [0.5, 0.8, 0.95, 1.0, 1.05, 1.2, 1.5]:
    print(f"{w:8.3f} {numeric_dn(w):16.6f} {dRechi_dw(w):16.6f} {book_formula(w):16.6f}")

print()
print("=== sign check near resonance (the physically decisive test) ===")
for w in [0.95, 0.98, 1.0, 1.02, 1.05]:
    num = numeric_dn(w)
    print(f"  w={w}: numeric dn/dw = {num:+.6f}  -> {'ANOMALOUS (<0)' if num < 0 else 'normal (>0)'}"
          f"   | book formula = {book_formula(w):+.6f} (always >0)")

print()
print("=== can the printed formula EVER be negative? ===")
ws = np.linspace(0.01, 3.0, 200000)
vals = book_formula(ws)
print(f"  min of printed formula over w in (0,3] = {vals.min():.3e}  (A>0, w>0, D>0)")
print("  => the printed formula is strictly POSITIVE everywhere, so it cannot")
print("     produce the claimed dn/dw < 0 near resonance.")
print()
print("=== does the corrected numerator term reproduce the numeric sign? ===")
for w in [0.95, 0.98, 1.0, 1.02, 1.05]:
    corrected = dRechi_dw(w)
    print(f"  w={w}: corrected = {corrected:+.6f}  numeric = {numeric_dn(w):+.6f}  "
          f"{'MATCH' if np.sign(corrected)==np.sign(numeric_dn(w)) else 'MISMATCH'}")
