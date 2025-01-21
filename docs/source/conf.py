# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import os
import sys

sys.path.insert(0, os.path.abspath("../../suraida"))

import suraida

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "suraida"
copyright = "2024 and later, Jens Koch"
author = "Jens Koch"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "sphinx_design",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.viewcode",
    "sphinx.ext.ifconfig",
    "nbsphinx",
    "sphinx.ext.mathjax",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
    "sphinx_copybutton",
]

# The master toctree document.
master_doc = "contents"

templates_path = ["_templates"]

exclude_patterns = [
    "_build",
    "_templates",
    "tmp",
    "**.ipynb_checkpoints",
    "Thumbs.db",
    ".DS_Store",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

import pydata_sphinx_theme

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_show_sourcelink = False
html_sourcelink_suffix = ""
html_static_path = ["_static"]
html_css_files = ["theme_overrides.css", "pygments.css"]

html_logo = "./_static/suraida-logo.svg"
html_favicon = "./_static/suraida-thumbnail.png"

language = "en"

autodoc_mock_imports = ["numpy"]
autosectionlabel_prefix_document = True
autosummary_generate = True

# Options for sphinx_autodoc_typehints
set_type_checking_flag = True
simplify_optional_unions = True

html_theme_options = {
    "logo": {
        "alt_text": "suraida logo",
        "image_light": "suraida-logo.svg",
        "image_dark": "suraida-logo.svg",
        "link": "../index",
    },
    "github_url": "https://github.com/scqubits/suraida",
    "twitter_url": "https://twitter.com/scqubits",
    "icon_links": [
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/suraida/",
            "icon": "fas fa-box",
        },
        {
            "name": "conda",
            "url": "https://anaconda.org/conda-forge/suraida",
            "icon": "fas fa-box-open",
        },
    ],
    "use_edit_page_button": False,
    "navbar_start": ["navbar-logo"],
    "navbar_end": ["navbar-icon-links"],
    "navigation_depth": 5,
    "show_nav_level": 3,
    "collapse_navigation": True,
}

html_sidebars = {
    "contribute/index": [
        "search-field",
        "sidebar-nav-bs",
        "custom-template",
    ],  # This ensures we test for custom sidebars
    "demo/no-sidebar": [],
}

highlight_language = "python"
# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "algol_nu"

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = False

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# If true, section author and module author directives will be shown in the
# output. They are ignored by default.
show_authors = True

# A list of ignored prefixes for module index sorting.
todo_include_todos = True

napoleon_numpy_docstring = True
napoleon_use_admonition_for_notes = True

nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc=figure.dpi=96",
]

nbsphinx_prompt_width = "0ex"
nbsphinx_codecell_lexer = "ipython3"
# The following only to be enabled for debugging purposes
# nbsphinx_allow_errors = True
