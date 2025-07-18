# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Nether'
copyright = '2025, Arjuna Systems'
author = 'Arjuna Systems'
release = '0.20.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

extensions.append('sphinx_multiversion')

# Build configuration for sphinx-multiversion
smv_tag_whitelist = r'^v.*$'  # Only build tags starting with 'v'
smv_branch_whitelist = r'^(main|dev|release/.*)$'  # Build these branches
smv_remote_whitelist = r'^origin$'

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# Use index.md as the documentation entry point
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
