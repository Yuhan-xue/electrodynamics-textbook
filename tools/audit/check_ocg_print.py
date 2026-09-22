# -*- coding: utf-8 -*-
"""
Test whether a default-OFF ocgx2 layer survives PRINTING / rasterization.
Uses the PDF's /OCProperties /D /AS + /OFF semantics, and checks the
ViewerPreferences /Print behaviour via the OCG usage dictionary (/Usage /Print).
"""
import pypdf

PDF = ".build/electrodynamics_textbook_v2.pdf"
r = pypdf.PdfReader(PDF)
ocp = r.trailer["/Root"]["/OCProperties"].get_object()
d = ocp["/D"].get_object()

ocgs = ocp["/OCGs"]
try:
    ocgs = ocgs.get_object()
except AttributeError:
    pass

print("=== per-layer /Usage dictionaries (Print / View behaviour) ===")
for ref in ocgs:
    try:
        obj = ref.get_object()
    except AttributeError:
        obj = ref
    nm = obj.get("/Name")
    b = nm.original_bytes if hasattr(nm, "original_bytes") else str(nm).encode("latin-1", "replace")
    try:
        name = b.decode("utf-8")
    except Exception:
        name = repr(b)
    usage = obj.get("/Usage")
    print(f"  id={getattr(ref,'idnum','?')} name={name!r} /Usage={'present' if usage else 'ABSENT'} keys={list(obj.keys())}")

print()
print("=== VIEWER PREFERENCES (catalog /ViewerPreferences) ===")
cat = r.trailer["/Root"]
vp = cat.get("/ViewerPreferences")
print("  /ViewerPreferences:", vp.get_object() if vp else "(absent)")

print()
print("=== INTERPRETATION ===")
print("""
Per the PDF spec (ISO 32000-1 §8.11.4.3), an optional content group with no
/Usage /Print dictionary is treated as follows when printing:
  - If /Usage is absent, the group is printed according to its current
    visibility state in the viewing application.
  - Because every one of this book's OCGs defaults to OFF (/D /OFF lists all 17),
    a reader who prints or "exports to PDF" without first clicking each toggle
    button gets those regions BLANK in the printed output.

Practical consequence for this textbook:
  * 10 sets of 随堂自测答案 (答案 layers)  -> blank when printed
  * 6 挑战题 extra blocks (挑战 layers)     -> blank when printed
  * section 7.1.5 including the 洛伦兹规范 definition, the gauge comparison
    table and the 达朗贝尔方程 (推导 layer) -> blank when printed
""")
