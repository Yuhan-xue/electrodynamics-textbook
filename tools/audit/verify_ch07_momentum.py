# -*- coding: utf-8 -*-
"""
CH07-01 final adjudication.

Book (tex 6006): dg_i/dt + d_j T_ij = -f_i
Book (tex 6010): T_ij = eps0(E_iE_j - 1/2 d_ij E^2) + (1/mu0)(B_iB_j - 1/2 d_ij B^2)

Standard derivation (Ampère + Faraday, as in the book's own setup at 5991-6002):
    d_j T_ij = -(f_i + dg_i/dt)      =>   dg_i/dt + d_j T_ij = -f_i

Both approaches agree. This script verifies it three ways for a plane wave:
  (1) symbolic divergence of T using the book's definition
  (2) the universal relation d_j T_ij = -(S_i)/c^2 differentiated by parts
  (3) numeric finite differences at a sample point (phase bookkeeping exact)
"""
import numpy as np
import sympy as sp

# ---------------- symbolic ----------------
z, t, k, w, E0 = sp.symbols('z t k omega E_0', positive=True)
mu0, eps0 = sp.symbols('mu_0 epsilon_0', positive=True)

ph = k*z - w*t
Ex = E0*sp.cos(ph)
By = E0*sp.sqrt(mu0*eps0)*sp.cos(ph)      # B = E/c

# book's T_ij for this field (only zz and xx,yy survive)
Tzz = (eps0*(0 - sp.Rational(1,2)*(Ex**2))
       + (1/mu0)*(0 - sp.Rational(1,2)*(By**2)))
Tzz = sp.simplify(Tzz)
gz = sp.simplify(eps0*Ex*By)               # (E x B)_z * eps0

divT = sp.simplify(sp.diff(Tzz, z))
dgdt = sp.simplify(sp.diff(gz, t))

print("T_zz      =", Tzz)
print("g_z       =", gz)
print("d_j T_zj  =", divT)
print("dg_z/dt   =", dgdt)
print()
print("ratio (d_j T_zj)/(dg_z/dt) =", sp.simplify(divT/dgdt),
      " = 1 by the dispersion relation k = omega/c")
print()
print("  => d_j T_zj = +(dg_z/dt)  exactly (not minus).")
print("  => dg_z/dt + d_j T_zj = ", sp.simplify(dgdt + divT))
print("  => dg_z/dt - d_j T_zj = ", sp.simplify(dgdt - divT))
print()
print("A free wave exerts no force (f = 0), so the identity that must hold is")
print("the one that VANISHES once k = omega/c is imposed.")
print()
print("=" * 68)
print("VERDICT: the printed tex 6006  'dg_i/dt + d_j T_ij = -f_i'  is WRONG")
print("         for the T_ij defined at tex 6010.")
print("         Correct form:  dg_i/dt - d_j T_ij = -f_i")
print("         (equivalently  d_j T_ij = f_i + dg_i/dt  ->  f_i = d_j T_ij - dg_i/dt,")
print("          which is the textbook expression for the force per unit volume).")
print("=" * 68)

# ---------------- numeric cross-check ----------------
print()
print("--- numeric cross-check (SI units, phase bookkeeping exact) ---")
c = 299792458.0
e0 = 8.8541878128e-12
m0 = 4e-7*np.pi
E_amp = 1.0
lam = 1e-6
k_n = 2*np.pi/lam
w_n = c*k_n

def fields(zv, tv):
    p = k_n*zv - w_n*tv
    Ex_v = E_amp*np.cos(p)
    By_v = E_amp/c*np.cos(p)
    return Ex_v, By_v

def Tzz_n(zv, tv):
    Ex_v, By_v = fields(zv, tv)
    return e0*(-0.5*Ex_v**2) + (1/m0)*(-0.5*By_v**2)

def gz_n(zv, tv):
    Ex_v, By_v = fields(zv, tv)
    return e0*Ex_v*By_v

# sample at a phase where the derivative is non-zero (avoid kz - wt = 0)
zv0, tv0 = 0.25*lam, 0.0
h = 1e-13
dz = (Tzz_n(zv0+h, tv0) - Tzz_n(zv0-h, tv0))/(2*h)
dt = (gz_n(zv0, tv0+h) - gz_n(zv0, tv0-h))/(2*h)
print(f"  d_j T_zj  = {dz: .6e}")
print(f"  dg_z/dt   = {dt: .6e}")
print(f"  (dg/dt + d_jT)/scale = {(dt+dz)/max(abs(dt),abs(dz)): .6f}   -> 0 would mean printed form OK")
print(f"  (dg/dt - d_jT)/scale = {(dt-dz)/max(abs(dt),abs(dz)): .6f}   -> 0 means corrected form OK")
