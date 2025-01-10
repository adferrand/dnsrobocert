from os.path import abspath, dirname, join

import tomllib

with open(join(dirname(dirname(abspath(__file__))), "pyproject.toml"), "rb") as file_h:
    metadata = tomllib.load(file_h)

master_doc = "index"
project = "DNSroboCert"
version = release = metadata["project"]["version"]
author = "Adrien Ferrand"
copyright = "2022, Adrien Ferrand"

extensions = [
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "lexicon": ("https://dns-lexicon.github.io/dns-lexicon/", None),
}

html_theme = "piccolo_theme"
html_theme_options = {
    "source_url": 'https://github.com/dns-lexicon/dns-lexicon/'
}
