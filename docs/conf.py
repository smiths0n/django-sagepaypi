#!/usr/bin/env python3
import os
import sys
import django
import sagepaypi

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
django.setup()

# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Django SagePayPI'
copyright = '2019, Accent Design Group LTD'
author = 'Stuart George'

# The short X.Y version.
version = sagepaypi.__version__
# The full version, including alpha/beta/rc tags.
release = sagepaypi.__version__

language = None

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'default'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

html_theme = 'karma_sphinx_theme'

html_static_path = ['_static']
