# -*- coding: utf-8 -*-
"""
Independently re-derive the SI -> Gaussian conversion factors to confirm or
refute ui-audit.md section 5.1 before touching site.js.

Base definitions only:
  1 statC: two 1-statC charges 1 cm apart repel with 1 dyn
  1 statV = 1 erg/statC
  1 G    = 1e-4 T ;  1 Oe defined so that H[Oe] = B[G] in vacuum
  Gaussian: div E = 4*pi*rho ; D = E + 4*pi*P ; B = H + 4*pi*M
"""
import numpy as np

c = 2.99792458e8          # m/s
eps0 = 8.8541878128e-12   # F/m
mu0 = 4 * np.pi * 1e-7    # H/m
e_C = 1.602176634e-19     # C
e_esu = 4.803204712570263e-10  # statC (CODATA-ish)

print("=== step 1: charge factor from the definition of statC ===")
# F = q^2/r^2 in cgs with F in dyn, r in cm  ->  q^2 = F r^2
# 1 statC^2 = 1 dyn * cm^2 = 1e-5 N * 1e-4 m^2
q_statC_sq_SI = 1e-5 * 1e-4               # N m^2 = C^2/(4 pi eps0)
# In SI the same force is F = q^2/(4 pi eps0 r^2) => q^2 = F*4 pi eps0 r^2
one_statC_in_C = np.sqrt(q_statC_sq_SI * 4 * np.pi * eps0)
print(f"  1 statC = {one_statC_in_C:.6e} C")
print(f"  => 1 C   = {1/one_statC_in_C:.8e} statC   (call it C_STAT)")
C_STAT = 1 / one_statC_in_C
print(f"  cross-check vs e: e={e_C} C = {e_C*C_STAT:.6e} statC "
      f"(CODATA {e_esu:.6e})  -> ratio {e_C*C_STAT/e_esu:.6f}")

print()
print("=== step 2: E factor ===")
# 1 statV = 1 erg/statC = 1e-7 J / (1/C_STAT) C  = 1e-7*C_STAT V
statV_in_V = 1e-7 * C_STAT
print(f"  1 statV = {statV_in_V:.6f} V")
E_factor = 1 / (100 * statV_in_V)     # 1 V/m = ? statV/cm
print(f"  1 V/m   = {E_factor:.8e} statV/cm")
alt = 1e6 / (C_STAT * 1e2)            # equivalent form: (1/100)*C_STAT/1e... verify
print(f"  audit's form 1e6/2.99792458e10 = {1e6/2.99792458e10:.8e}")
print(f"  my earlier (buggy) 1/(100*c)   = {1/(100*c):.8e}   ratio {E_factor/(1/(100*c)):.3e}")

print()
print("=== step 3: D and P factors (P has NO 4*pi) ===")
D_factor = 4 * np.pi * C_STAT / 1e4
P_factor = C_STAT / 1e4
print(f"  D: 1 C/m^2 = {D_factor:.8e} statC/cm^2")
print(f"  P: 1 C/m^2 = {P_factor:.8e} statC/cm^2")

print()
print("=== step 4: H and M factors ===")
H_factor = 1e-3 / (4 * np.pi) * (4 * np.pi)   # placeholder, computed below properly
# 1 Oe = 1e-4 T / mu0
Oe_in_Am = 1e-4 / mu0
print(f"  1 Oe = {Oe_in_Am:.6f} A/m")
H_factor = 1 / Oe_in_Am
print(f"  H: 1 A/m = {H_factor:.8e} Oe    (= 4pi*1e-3 = {4*np.pi*1e-3:.8e})")
M_factor = 1e-3
print(f"  M: 1 A/m = {M_factor:.8e} G(emu/cm^3)")
# cross-check M via B = mu0(H+M)  <->  B = H + 4 pi M
M_factor2 = H_factor / (4 * np.pi)
print(f"  M cross-check via B relation: {M_factor2:.8e}  (must equal 1e-3)")

print()
print("=== step 5: B, Q, Phi ===")
print(f"  B: 1 T = 1e4 G")
print(f"  Q: 1 C = {C_STAT:.8e} statC")
print(f"  Phi: 1 Wb = 1e8 Mx")

print()
print("=== step 6: physical cross-check via infinite charged sheet ===")
# SI: sigma = 1 C/m^2  -> E = sigma/(2 eps0)... use the audit's full-sheet E = sigma/eps0
sigma_SI = 1.0
E_SI = sigma_SI / eps0
E_CGS_from_SI = E_SI * E_factor
# Gaussian: div E = 4 pi rho -> across a sheet, E = 4 pi sigma_G  (per the book's convention)
sigma_G = sigma_SI * P_factor      # surface charge density conversion == charge/area
E_CGS_direct = 4 * np.pi * sigma_G
print(f"  sigma = 1 C/m^2 = {sigma_G:.6e} statC/cm^2")
print(f"  E via SI then convert : {E_CGS_from_SI:.6e} statV/cm")
print(f"  E directly in Gaussian: {E_CGS_direct:.6e} statV/cm")
print(f"  ratio = {E_CGS_from_SI/E_CGS_direct:.8f}   (must be 1)")
