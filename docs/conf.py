"""Sphinx configuration: SafeCruise documentation and requirements database.

Need types, link types and attributes follow brief §6.1 as refined by ADR-000.
"""

project = "SafeCruise"
author = "pb"
copyright = "2026, pb"

extensions = [
    "myst_parser",
    "sphinx.ext.graphviz",
    "sphinx_needs",
    "sphinxcontrib.test_reports",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "**/.gitkeep"]
root_doc = "index"
html_theme = "alabaster"
html_title = "SafeCruise"

# ADRs and other Markdown pages link to repository files outside docs/ (the brief, PLAN.md,
# sources). MyST cannot resolve those, so its check is off; tests/tools/test_md_links.py
# checks every relative Markdown link against the repository instead.
suppress_warnings = ["myst.xref_missing"]

# --- sphinx-needs: need types (brief §6.1; HE_ from ADR-004) --------------------------
_NEED_TYPES = [
    # directive, title, prefix, colour, style
    ("stk", "Stakeholder need", "STK_", "#BFD8D2", "node"),
    ("he", "Hazardous event", "HE_", "#F5CBA7", "node"),  # ADR-004
    ("sg", "Safety goal", "SG_", "#F28C8C", "node"),
    ("sys", "System requirement", "SYS_", "#BFD8F2", "node"),
    ("fsr", "Functional safety requirement", "FSR_", "#F5B7A1", "node"),
    ("tsr", "Technical safety requirement", "TSR_", "#F9D29D", "node"),
    ("aou", "Assumption of use", "AOU_", "#D7BDE2", "node"),
    ("swr", "Software requirement", "SWR_", "#A9DFBF", "node"),
    ("arc", "Architecture element", "ARC_", "#D5DBDB", "component"),
    ("tc", "Test case specification", "TC_", "#FCF3CF", "node"),
]
needs_types = [
    {"directive": d, "title": t, "prefix": p, "color": c, "style": s}
    for d, t, p, c, s in _NEED_TYPES
]

needs_id_required = True
needs_id_regex = r"^(STK|HE|SG|SYS|FSR|TSR|AOU|SWR|ARC|TC)_[A-Z0-9]+(_[A-Z0-9]+)*$"

# --- Attributes (brief §6.1, ADR-000 D-17/D-18, ADR-004) -------------------------------
# asil: QM, A-D or decomposed, e.g. B(D). safe_state and ftti_ms on SG_. level and
# method on TC_. Allowed values are enforced by tools/ears_lint.py (M2), not here.
# HE_ carries its operational situation, malfunction, the S/E/C ratings and one rationale
# per rating; tools/hara_check.py checks them against the ASIL table.
needs_extra_options = [
    "asil",
    "verification_method",
    "safe_state",
    "ftti_ms",
    "level",
    "method",
    "situation",
    "malfunction",
    "severity",
    "severity_rationale",
    "exposure",
    "exposure_rationale",
    "controllability",
    "controllability_rationale",
]

# draft | approved; only pb sets approved (ADR-000 D-17).
needs_statuses = [
    {"name": "draft", "description": "Written, not yet approved by pb."},
    {"name": "approved", "description": "Approved by pb."},
]

# --- Link types (brief §6.1) ------------------------------------------------------------
needs_extra_links = [
    {"option": "satisfies", "incoming": "is satisfied by", "outgoing": "satisfies"},
    {"option": "derives_from", "incoming": "is derived into", "outgoing": "derives from"},
    {"option": "allocated_to", "incoming": "is allocated", "outgoing": "is allocated to"},
    {"option": "verifies", "incoming": "is verified by", "outgoing": "verifies"},
]

# needs.json is written by `sphinx-build -b needs` and, for the published site, by HTML builds.
needs_build_json = True

# Trace diagrams (needflow) are drawn with Graphviz `dot` from the toolchain image (ADR-005).
needs_flow_engine = "graphviz"
graphviz_output_format = "svg"
