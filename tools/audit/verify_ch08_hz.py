# -*- coding: utf-8 -*-
"""
Independent check of CH08-01 (sign of H_z in TE10) — clean phasor algebra.

Phasor convention used by the book:  A(r,t) = A_phasor(r) * e^{i(kz z - omega t)}
For this convention  d/dt -> -i*omega ,  d/dz -> +i*kz .

Maxwell (no sources, vacuum):
  (I)   curl E = -dB/dt = -mu0 dH/dt   ->  curl E = +i*omega*mu0*H
  (II)  curl H =  eps0 dE/dt           ->  curl H = -i*omega*eps0*E

Book's TE10 (tex 6617-6619):
  Ey =  E0 sin(pi x/a) e^{i(...)}
  Hx = -(kz/(omega mu0)) E0 sin(pi x/a) e^{i(...)}
  Hz = +(i pi/(omega mu0 a)) E0 cos(pi x/a) e^{i(...)}
We test the sign of Hz against equations (I)-x and (II)-x.
"""
import sympy as sp

x, z, t = sp.symbols('x z t', real=True)
a, kz, w, E0, c = sp.symbols('a kz omega E_0 c', positive=True)
mu0, eps0 = sp.symbols('mu_0 epsilon_0', positive=True)
ii = sp.I

phase = sp.exp(ii * (kz * z - w * t))
S = sp.sin(sp.pi * x / a)
C = sp.cos(sp.pi * x / a)

Ey = E0 * S * phase
Hx = -(kz / (w * mu0)) * E0 * S * phase

def curl_components(Ax, Ay, Az):
    return (
        sp.diff(Az, sp.Symbol('y', real=True)) - sp.diff(Ay, z) if False else -sp.diff(Ay, z),
        sp.diff(Ax, z) - sp.diff(Az, x),
        sp.diff(Ay, sp.Symbol('x', real=True)) - sp.diff(Ax, sp.Symbol('y', real=True)),
    )

# --- Equation (I)-x :  (curl E)_x = i w mu0 Hx ,  with Ey only
curlE_x = -sp.diff(Ey, z)                       # (curl E)_x = dEz/dy - dEy/dz, Ez=0
lhs = sp.simplify(curlE_x)
rhs = sp.simplify(ii * w * mu0 * Hx)
print("(I)-x  curlE_x =", sp.simplify(lhs / (E0 * S * phase)), "* E0 sin e^{i()}")
print("(I)-x  i w mu0 Hx =", sp.simplify(rhs / (E0 * S * phase)), "* E0 sin e^{i()}")
print("Faraday x-component satisfied by printed Hx :", sp.simplify(lhs - rhs) == 0)
print()

# --- Equation (II)-y :  (curl H)_y = -i w eps0 Ey
# (curl H)_y = dHx/dz - dHz/dx
Hz_sym = sp.Symbol('H_z_coef')                  # solve for dHz/dx
dHzdx = sp.Symbol('dHzdx')
curlH_y = sp.diff(Hx, z) - dHzdx
rhs_y = -ii * w * eps0 * Ey
sol = sp.solve(sp.Eq(curlH_y, rhs_y), dHzdx)[0]
sol = sp.simplify(sp.expand(sol / (E0 * phase)))
print("(II)-y  dHz/dx =", sp.simplify(sol), "* E0 e^{i()}")
print()
print("Book's Hz = +(i pi/(w mu0 a)) E0 cos(pi x/a) e^{i()}")
print("  => dHz/dx = -(i pi^2/(w mu0 a^2)) E0 sin(pi x/a) e^{i()}")
print("  => coefficient * a^2/(i pi^2 E0 e^{i()}) =", sp.simplify(-ii * sp.pi**2 / (w * mu0 * a**2)))
print()
derived = sp.simplify(sol)
book_dHzdx = sp.simplify(-ii * sp.pi**2 / (w * mu0 * a**2))
print("derived dHz/dx coefficient (times a^2 mu0 w/(E0 e^{i()})) :",
      sp.simplify(derived * a**2 * mu0 * w / ii))
print()
print("=== conclusion ===")
print("If the derived and book coefficients differ by a factor of -1, the book's")
print("Hz sign is wrong and must be flipped to -i.")
print("ratio book/derived =", sp.simplify(book_dHzdx / derived))
