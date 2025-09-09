import os
import sys
from sphinx.ext.autodoc.mock import mock

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(".."))

# ============================== PROJECT INFO ===============================

project = "Ignis"
copyright = "2024, linkfrg"
author = "linkfrg"
REPO_URL = "https://github.com/ignis-sh/ignis"
DOCS_URL = "https://ignis-sh.github.io/ignis/latest"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_click",
    "_ext.ignis_directives",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "gtk": ("https://lazka.github.io/pgi-docs/Gtk-4.0", None),
    "gio": ("https://lazka.github.io/pgi-docs/Gio-2.0", None),
    "glib": ("https://lazka.github.io/pgi-docs/GLib-2.0", None),
    "gdkpixbuf": ("https://lazka.github.io/pgi-docs/GdkPixbuf-2.0", None),
    "nm": ("https://lazka.github.io/pgi-docs/NM-1.0", None),
    "gobject": ("https://lazka.github.io/pgi-docs/GObject-2.0", None),
    "pygobject": ("https://pygobject.gnome.org", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
suppress_warnings = ["config.cache"]

# ============================ AUTODOC/TYPEHINTS ============================

autodoc_mock_imports = ["gi", "loguru", "setuptools", "click", "cairo"]
autodoc_member_order = "bysource"

smartquotes = False
napoleon_use_param = True

typehints_use_signature = True
typehints_use_signature_return = True
typehints_defaults = "comma"
always_use_bars_union = True

# =============================== VERSIONING ================================

with mock(autodoc_mock_imports):
    import ignis

    json_url = f"{DOCS_URL}/_static/switcher.json"

    DOC_TAG = os.getenv("DOC_TAG")

    if DOC_TAG == "latest" or DOC_TAG is None:
        version_match = "dev"
    elif DOC_TAG == "stable":
        version_match = "v" + ignis.__version__.replace(".dev0", "")
    else:
        version_match = DOC_TAG

    release = version_match

# ============================== HTML OPTIONS ===============================

html_title = "Ignis documentation"
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_theme_options = {
    "use_edit_page_button": True,
    "logo": {
        "text": "Ignis",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": REPO_URL,
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        }
    ],
    "show_version_warning_banner": True,
    "navbar_align": "left",
    "navbar_center": ["version-switcher", "navbar-nav"],
    "secondary_sidebar_items": {
        "**/*": ["page-toc", "edit-this-page", "sourcelink"],
    },
    "switcher": {
        "json_url": json_url,
        "version_match": version_match,
    },
    "pygments_light_style": "tango",
    "pygments_dark_style": "monokai",
}

html_context = {
    "github_user": "ignis-sh",
    "github_repo": "ignis",
    "github_version": "main",
    "doc_path": "docs/",
}
