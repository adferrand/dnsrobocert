from os.path import abspath, dirname, join

import toml

metadata = toml.load(join(dirname(dirname(abspath(__file__))), "pyproject.toml"))["tool"]["poetry"]

master_doc = 'index'
project = "DNSroboCert"
version = release = metadata["version"]
author = "Adrien Ferrand"
copyright = "2020, Adrien Ferrand"
