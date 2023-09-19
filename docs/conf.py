from os.path import abspath, dirname, join

import toml

root_path = dirname(dirname(abspath(__file__)))
pyproject_toml = toml.load(root_path)

master_doc = "index"
project = "DNSroboCert"
version = release = pyproject_toml["tool"]["poetry"]["version"]
author = "Adrien Ferrand"
copyright = "2022, Adrien Ferrand"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
]

intersphinx_mapping = {
    "lexicon": ("https://dns-lexicon.readthedocs.io/en/latest", None),
}

html_theme = "sphinx_rtd_theme"
