from os.path import abspath, dirname, join

import toml

pyproject_toml = toml.load(join(dirname(dirname(abspath(__file__))), "pyproject.toml"))
poetry_lock = toml.load(join(dirname(dirname(abspath(__file__))), "poetry.lock"))

master_doc = "index"
project = "DNSroboCert"
version = release = pyproject_toml["tool"]["poetry"]["version"]
author = "Adrien Ferrand"
copyright = "2022, Adrien Ferrand"

extensions = [
    "sphinx.ext.intersphinx",
]

lexicon_version = [package for package in poetry_lock["package"] if package["name"] == "dns-lexicon"][0]["version"]
intersphinx_mapping = {
    'lexicon': (f'https://dns-lexicon.readthedocs.io/en/latest/', None),
}
