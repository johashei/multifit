# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'multifit'
copyright = '2026, J. S. Heines'
author = 'J. S. Heines'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.apidoc',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon'
    ]

templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
        'exclude-members': '__doc__',
        'member-order': 'bysource'
        }

apidoc_modules = [
        {
            'path': '../../src/multifit',
            'destination': 'pages/',
            'separate_modules': True,
            'automodule_options': {
                'members', 'show-inheritance',
                }
            }
        ]

autosummary_generate = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

#html_theme_options = {
#    ''
#    }
