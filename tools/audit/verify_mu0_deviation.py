# -*- coding: utf-8 -*-
"""
Appendix C note claims: after the 2019 SI revision, mu0 deviates from
4*pi*1e-7 H/m by "about 2e-9 relative". Verify from CODATA-2018/2022 values.

mu0 = 2 * alpha * h / (c * e^2)   (exact relation in the revised SI)
"""
import math
from scipy.constants import alpha as A_2018, h as h_2018, c as c_exact, e as e_exact

print("CODATA-2018 (SI 2019 revision basis)")
mu0 = 2 * A_2018 * h_2018 / (c_exact * e_exact**2)
old = 4 * math.pi * 1e-7
print(f"  mu0 (derived)      = {mu0:.6e} H/m")
print(f"  4*pi*1e-7          = {old:.6e} H/m")
print(f"  absolute deviation = {mu0 - old:+.6e} H/m")
print(f"  RELATIVE deviation = {(mu0 - old)/old:+.6e}")
print()
print("  appendix note says '2e-9'  ->", "MATCH" if abs(abs((mu0-old)/old) - 2e-9)/2e-9 < 0.5 else "MISMATCH")

# newer CODATA
try:
    from scipy.constants import physical_constants as pc
    v = pc['vacuum mag. permeability'][0]
    print()
    print(f"scipy's mu0 value   = {v:.6e} H/m")
    print(f"  relative deviation = {(v-old)/old:+.6e}")
except Exception as ex:
    print("no scipy pc:", ex)

print()
print("NOTE: alpha, h, e were all fixed/measured such that mu0 is now a MEASURED")
print("quantity. The commonly quoted relative deviation is of order 1e-9 to 1e-10")
print("depending on the CODATA release. The book's teaching point (that mu0 is no")
print("longer exactly 4pi*1e-7) is correct regardless of the exact digit.")
