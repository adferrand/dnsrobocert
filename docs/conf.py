from pathlib import Path

import toml

metadata = toml.load(Path(__file__).parent.parent / "pyproject.toml")["tool"]["poetry"]

master_doc = 'index'
project = "DNSroboCert"
version = release = metadata["version"]
author = "Adrien Ferrand"
copyright = "2020, Adrien Ferrand"
