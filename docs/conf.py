from os.path import abspath, dirname, join

import toml

root_path = dirname(dirname(abspath(__file__)))
pyproject_toml = toml.load(join(root_path, "pyproject.toml"))

master_doc = "index"
project = "DNSroboCert"
version = release = pyproject_toml["tool"]["poetry"]["version"]
author = "Adrien Ferrand"
copyright = "2022, Adrien Ferrand"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_immaterial",
]

intersphinx_mapping = {
    "lexicon": ("https://dns-lexicon.readthedocs.io/en/latest", None),
}

html_theme = "sphinx_immaterial"

html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "site_url": "https://pypi.org/project/dnsrobocert/",
    "repo_url": "https://github.com/adferrand/dnsrobocert/",
    "repo_name": "DNSroboCert",
    "edit_uri": "blob/master/docs",
    "globaltoc_collapse": True,
    "features": [
        "navigation.expand",
        # "navigation.tabs",
        # "toc.integrate",
        "navigation.sections",
        # "navigation.instant",
        # "header.autohide",
        "navigation.top",
        # "navigation.tracking",
        # "search.highlight",
        "search.share",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "announce.dismiss",
    ],
    "toc_title_is_page_title": True,
}
