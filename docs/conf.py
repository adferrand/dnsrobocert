from pathlib import Path

import toml

metadata = toml.load(Path(__file__).parent.parent / "pyproject.toml")["tool"]["poetry"]
version = release = metadata["version"]
