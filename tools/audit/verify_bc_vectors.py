# -*- coding: utf-8 -*-
"""
Verify the two vector forms of the magnetic tangential boundary condition
claimed equivalent in Ch6 §「磁学边界条件」.

Setup: interface = xy-plane, n̂ = ẑ points from region 1 (z<0) to region 2 (z>0).
Take K_f = K x̂. Then the physical statement is H_2t - H_1t = K_f (along x).
Check what each vector form predicts for H_1 - H_2.
"""
import numpy as np

n = np.array([0.0, 0.0, 1.0])
K = np.array([1.0, 0.0, 0.0])          # free surface current along x

# Form A: n̂ × (H1 - H2) = K_f
#   => H1 - H2 must satisfy ẑ × (H1-H2) = x̂
#   Solutions: H1-H2 = ŷ + (any multiple of ẑ)  since ẑ × ŷ = -x̂ ... check sign
cands = {
    'yhat': np.array([0.0, 1.0, 0.0]),
    '-yhat': np.array([0.0, -1.0, 0.0]),
    'xhat': np.array([1.0, 0.0, 0.0]),
    '-xhat': np.array([-1.0, 0.0, 0.0]),
}
print("Form A: n̂ × (H1 − H2) = K_f  with n̂=ẑ, K_f=x̂")
for name, d in cands.items():
    lhs = np.cross(n, d)
    ok = np.allclose(lhs, K)
    print(f"   H1−H2 = {name:6} -> n̂×(H1−H2) = {lhs}   {'MATCH' if ok else ''}")

print()
print("Form B: H_1∥ − H_2∥ = K_f × n̂")
Kn = np.cross(K, n)
print(f"   K_f × n̂ = {Kn}")
for name, d in cands.items():
    ok = np.allclose(d, Kn)
    print(f"   H1−H2 = {name:6} -> {'MATCH' if ok else ''}")

print()
print("Scalar statement: H_2t − H_1t = K_f  ⇒  H_1t − H_2t = −K_f = −x̂")
print("   So H1 − H2 must have tangential part  −x̂.")
print()
print("CONCLUSION")
print("  Form A gives H1−H2 = −ŷ, whose tangential part is −ŷ (perpendicular to K).")
print("  Form B gives H1−H2 = −ŷ as well.  The two vector forms agree with each other.")
print("  But the SCALAR statement (H_2t − H_1t = K_f, tangential part −x̂) is NOT")
print("  the same as the vector forms unless 'tangential' is read as 'the component")
print("  along K_f × n̂'.  Both are standard; they differ only in which tangential")
print("  direction 't' denotes.  The book must state that convention explicitly.")
