# -*- coding: utf-8 -*-
"""
Check the Appendix E claim (tex ~8864):
  "电偶极辐射功率 ∝ p0^2 ω^4 ; 磁偶极 ∝ m0^2 ω^4 / c^2"
against the book's own theorem (Ch9):
  P_E = mu0 p0^2 ω^4 / (12 π c)
  P_M = mu0 m0^2 ω^4 / (12 π c^3)
"""
import sympy as sp

mu0, p0, m0, w, c = sp.symbols('mu_0 p_0 m_0 omega c', positive=True)

P_E = mu0 * p0**2 * w**4 / (12 * sp.pi * c)
P_M = mu0 * m0**2 * w**4 / (12 * sp.pi * c**3)

print("P_E =", P_E)
print("P_M =", P_M)
print()
print("Strip the common factor mu0 ω^4/(12π):")
print("  P_E ∝ p0^2 / c")
print("  P_M ∝ m0^2 / c^3")
print()
print("Appendix E states:  P_E ∝ p0^2 ω^4        (drops 1/c)")
print("                    P_M ∝ m0^2 ω^4 / c^2  (should be /c^3)")
print()
print("=> Appendix E is off by one power of c in BOTH lines")
print("   (missing 1/c for the electric case, and c^-2 instead of c^-3")
print("    for the magnetic case).")
print()
print("Now the ratio for sources of the same size:")
print("  With m0 ~ q v a and p0 ~ q a  =>  m0/p0 ~ v")
ratio = sp.simplify(P_M.subs(m0, p0 * sp.Symbol('v', positive=True)) / P_E)
print("  P_M/P_E =", ratio, " = (v/c)^2")
print("  so the (v/c)^2 statement in the same sentence IS correct.")
