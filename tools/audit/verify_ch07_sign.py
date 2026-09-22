# -*- coding: utf-8 -*-
"""
Settle CH07-01 cleanly. Direct analytic differentiation + matched finite
differences, no sympy simplification subtleties.
"""
import numpy as np

pi = np.pi
e0 = 8.8541878128e-12
m0 = 4e-7*pi
c = 1/np.sqrt(m0*e0)

E0 = 1.0
lam = 1e-6
k = 2*pi/lam
w = c*k                      # vacuum dispersion relation

# --- analytic, step by step ---
# T_zz = -eps0 Ex^2/2 - By^2/(2 mu0),  Ex = E0 cos(p), By = E0/c cos(p), p = kz - wt
#       = -eps0 E0^2 cos^2(p)/2 - E0^2 cos^2(p)/(2 mu0 c^2)
# note 1/(mu0 c^2) = eps0  ->  T_zz = -eps0 E0^2 cos^2(p)
coef = -e0*E0**2
print("T_zz = %.6e * cos^2(p)" % coef)

# d/dz T_zz = coef * 2 cos(p) * (-sin(p)) * k = -2 k coef cos sin
# g_z = eps0 Ex By = eps0 E0^2/c cos^2(p)
gcoef = e0*E0**2/c
print("g_z  = %.6e * cos^2(p)" % gcoef)
# d/dt g_z = gcoef * 2 cos(p) * (+sin(p)) * w = 2 w gcoef cos sin   [since d/dt cos(p) = +w sin(p)]

print()
print("analytic  d_j T_zj = -2*k*coef*cos(p)sin(p)")
print("analytic  dg_z/dt  = +2*w*gcoef*cos(p)sin(p)")
ratio_analytic = (-2*k*coef) / (2*w*gcoef)
print("analytic ratio (d_jT)/(dg/dt) = %.10f" % ratio_analytic)
print("  check: -k*coef/(w*gcoef) with coef=-e0 E0^2, gcoef=e0 E0^2/c")
print("       = k*e0*E0^2 / (w * e0*E0^2/c) = k*c/w = 1  since w = c k")
print()

# --- matched finite differences ---
# NOTE: gcoef ~ 3e-20, so differencing g directly loses all significance
# (the difference is ~1e-34, below the ulp of 1e-20). Differentiate the
# dimensionless envelope cos^2(p) instead, then scale analytically.
def p(z, t): return k*z - w*t
def env(z, t): return np.cos(p(z, t))**2          # dimensionless O(1)
def Tzz(z, t): return coef*env(z, t)
def gz(z, t):  return gcoef*env(z, t)

z0 = 0.137*lam          # avoid symmetry points
t0 = 0.0
# CRITICAL: the step must be small compared with the wavelength/period but
# large enough that the envelope change exceeds double precision (~1e-16).
# An earlier attempt used h=1e-11 on lam=1e-6 (k*h ~ 6e4 rad) -> random phases;
# a later one used h=lam*1e-7 (phase change ~1e-8) -> difference lost in the
# 16-digit rounding of cos^2, i.e. pure noise. Use a 1e-6-relative step in the
# *argument* by scaling each derivative with its own natural step.
hz = lam*1e-6           # k*hz ~ 6.3e-6 rad
ht = (2*pi/w)*1e-6      # w*ht ~ 6.3e-6 rad
denv_dz = (env(z0+hz, t0) - env(z0-hz, t0))/(2*hz)
denv_dt = (env(z0, t0+ht) - env(z0, t0-ht))/(2*ht)
dz = coef*denv_dz       # d_j T_zj
dt = gcoef*denv_dt      # dg_z/dt

print("numeric   d_j T_zj = % .8e" % dz)
print("numeric   dg_z/dt  = % .8e" % dt)
print("analytic  d_j T_zj = % .8e" % (-2*k*coef*np.cos(p(z0, t0))*np.sin(p(z0, t0))))
print("analytic  dg_z/dt  = % .8e" % (2*w*gcoef*np.cos(p(z0, t0))*np.sin(p(z0, t0))))
print("numeric ratio (d_jT)/(dg/dt) = %.8f" % (dz/dt))
print()
print("ratio = +1  ->  dg/dt - d_jT = 0  ->  CORRECTED form is right")
print("ratio = -1  ->  dg/dt + d_jT = 0  ->  printed form is right")
print()
print("=> numeric ratio =", round(dz/dt, 6), " (analytic: 1.0)")
