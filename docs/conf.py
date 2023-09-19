from os.path import abspath, dirname, join
import tomllib

root_path = dirname(dirname(abspath(__file__)))

with open(join(root_path, "pyproject.toml"), "rb") as f:
    pyproject_toml = tomllib.load(f)

master_doc = "index"
project = "DNSroboCert"
version = release = pyproject_toml["tool"]["poetry"]["version"]
author = "Adrien Ferrand"
copyright = "2022, Adrien Ferrand"

extensions = [
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    'lexicon': ('https://dns-lexicon.readthedocs.io/en/latest', None),
}
