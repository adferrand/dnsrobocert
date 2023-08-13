from importlib.metadata import PackageNotFoundError, metadata


def get_version():
    try:
        distribution = metadata(__name__)
    except PackageNotFoundError:
        return "dev"
    else:
        return distribution["Version"]


__version__ = get_version()
