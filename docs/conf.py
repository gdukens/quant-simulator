# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../quantlib_pro'))

project = 'QuantLib Pro SDK'
copyright = '2024-2026, QuantLib Pro Team'
author = 'QuantLib Pro Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.ifconfig',
    'sphinx.ext.mathjax',
    'sphinx_rtd_theme',
    'myst_parser',
    'nbsphinx',
    'sphinx_math_dollar',
    'sphinx.ext.githubpages'
]

# Add support for MyST markdown
source_suffix = {
    '.rst': None,
    '.md': 'myst-parser',
    '.ipynb': 'nbsphinx'
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv', '__pycache__']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/quantlib_logo.png'
html_favicon = '_static/favicon.ico'

html_theme_options = {
    'analytics_id': 'G-XXXXXXXXXX',  # Google Analytics ID
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Autosummary settings
autosummary_generate = True
autosummary_mock_imports = ['yfinance', 'alpha_vantage', 'fredapi']

# MathJax configuration for LaTeX
mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']],
        'processEscapes': True,
        'processEnvironments': True,
        'macros': {
            'E': ['\\mathbb{E}', 0],
            'Var': ['\\text{Var}', 0],
            'Cov': ['\\text{Cov}', 0], 
            'VaR': ['\\text{VaR}', 0],
            'CVaR': ['\\text{CVaR}', 0],
            'BS': ['\\text{BS}', 0],
            'Greeks': ['\\boldsymbol{\\Gamma}', 0]
        },
        'packages': {'[+]': ['amsmath', 'amsfonts', 'amssymb']}
    },
    'options': {
        'ignoreHtmlClass': 'tex2jax_ignore',
        'processHtmlClass': 'tex2jax_process'
    }
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'sklearn': ('https://scikit-learn.org/stable/', None)
}

# Todo extension settings
todo_include_todos = True

# LaTeX output settings
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': r'''
        \usepackage{amsmath}
        \usepackage{amsfonts}
        \usepackage{amssymb}
        \usepackage{bm}
        \usepackage{mathtools}
        \usepackage{algorithm}
        \usepackage{algorithmic}
        \usepackage{booktabs}
        \usepackage{subcaption}
        \setcounter{tocdepth}{2}
        \newcommand{\E}{\mathbb{E}}
        \newcommand{\Var}{\text{Var}}
        \newcommand{\Cov}{\text{Cov}}
        \newcommand{\VaR}{\text{VaR}}
        \newcommand{\CVaR}{\text{CVaR}}
        \newcommand{\bs}{d_1, d_2}
    '''
}

latex_documents = [
    (master_doc, 'quantlib-pro.tex', 'QuantLib Pro SDK Documentation',
     'QuantLib Pro Team', 'manual'),
]

# EPUB output settings
epub_title = project
epub_exclude_files = ['search.html']

# Custom CSS
def setup(app):
    app.add_css_file('custom.css')