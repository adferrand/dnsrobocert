import pkg_resources


def get_version():
    try:
        distribution = pkg_resources.get_distribution(__name__)
    except pkg_resources.DistributionNotFound:
        return "dev"
    else:
        return distribution.version


__version__ = get_version()
