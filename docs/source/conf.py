# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'multifit'
copyright = '2026, J. S. Heines'
author = 'J. S. Heines'
#from multifit.__about__ import __version__
#version = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
 #   'sphinx.ext.apidoc',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon'
    ]

templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
        'members': True,
        'member-order': 'bysource',
        'show-inheritance': True,
        }

#apidoc_modules = [
#        {
#            'path': '../../src/multifit',
#            'destination': 'pages/',
#            'separate_modules': True,
#            'no_headings': True,
#            'automodule_options': {
#                'members', 'show-inheritance',
#                }
#            }
#        ]

#autosummary_generate = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_logo = '../logo.svg'
html_static_path = ['_static']

html_theme_options = {
#        'headfont': 'Montserrat Alternates',
#        'bodyfont': 'Montserrat Alternates'
    }
