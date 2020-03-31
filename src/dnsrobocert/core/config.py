import logging
import os
from typing import Any, Dict, Optional, Set

import coloredlogs
import jsonschema
import pkg_resources
import yaml

from dnsrobocert.core import utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def load(config_path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(config_path):
        LOGGER.error("Configuration file {0} does not exist.".format(config_path))
        return None

    with open(config_path) as file_h:
        raw_config = file_h.read()

    try:
        config = yaml.load(raw_config, yaml.FullLoader)
    except BaseException:
        message = """
Error while validating dnsrobocert configuration:
Configuration file is not a valid YAML file.\
"""
        LOGGER.error(message)
        return None

    schema_path = pkg_resources.resource_filename("dnsrobocert", "schema.yml")
    with open(schema_path) as file_h:
        schema = yaml.load(file_h.read(), yaml.FullLoader)

    if not config:
        message = """
Error while validating dnsrobocert configuration:
Configuration file is empty.\
"""
        LOGGER.error(message)
        return None

    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        message = """\
Error while validating dnsrobocert configuration for node path {0}:
{1}.
-----
{2}\
""".format(
            "/" + "/".join([str(item) for item in e.path]), e.message, raw_config,
        )
        LOGGER.error(message)
        return None

    try:
        _values_conversion(config)
        _business_check(config)
    except ValueError as e:
        message = """\
Error while validating dnsrobocert configuration:
{0}
-----
{1}\
""".format(
            str(e), raw_config,
        )
        LOGGER.error(message)
        return None

    return config


def get_profile(config: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    profiles = [
        profile
        for profile in config.get("profiles", {})
        if profile["name"] == profile_name
    ]
    return profiles[0] if profiles else None


def get_certificate(config: Dict[str, Any], lineage: str) -> Optional[Dict[str, Any]]:
    certificates = [
        certificate
        for certificate in config.get("certificates", [])
        if get_lineage(certificate) == lineage
    ]
    return certificates[0] if certificates else None


def get_lineage(certificate_config: Dict[str, Any]) -> str:
    lineage = (
        certificate_config.get("name")
        if certificate_config.get("name")
        else utils.normalize_lineage(certificate_config.get("domains", [None])[0])
    )
    if not lineage:
        raise ValueError(
            "Could not find the certificate name for certificate config: {0}".format(
                certificate_config
            )
        )

    return lineage


def get_acme_url(config: Dict[str, Any]) -> str:
    acme = config.get("acme", {})

    directory_url = acme.get("directory_url")
    if directory_url:
        return directory_url

    api_version = acme.get("api_version", 2)
    staging = acme.get("staging", False)

    if api_version < 2:
        domain = "acme-staging" if staging else "acme-v01"
    else:
        domain = "acme-staging-v02" if staging else "acme-v02"

    return "https://{0}.api.letsencrypt.org/directory".format(domain)


def find_profile_for_lineage(config: Dict[str, Any], lineage: str) -> Dict[str, Any]:
    certificate = get_certificate(config, lineage)
    if not certificate:
        raise RuntimeError(
            "Error, certificate named `{0}` could not be found in configuration.".format(
                lineage
            )
        )
    profile_name = certificate.get("profile")
    if not profile_name:
        raise RuntimeError(
            "Error, profile named `{0}` could not be found in configuration.".format(
                lineage
            )
        )

    return get_profile(config, profile_name)


def _values_conversion(config: Dict[str, Any]):
    certs_permissions = config.get("acme", {}).get("certs_permissions", {})
    files_mode = certs_permissions.get("files_mode")
    if isinstance(files_mode, str):
        certs_permissions["files_mode"] = int(files_mode, 8)
    dirs_mode = certs_permissions.get("dirs_mode")
    if isinstance(dirs_mode, str):
        certs_permissions["dirs_mode"] = int(dirs_mode, 8)


def _business_check(config: Dict[str, Any]):
    profiles = [profile["name"] for profile in config.get("profiles", [])]
    lineages: Set[str] = set()
    for certificate_config in config.get("certificates", []):
        # Check that every certificate is associated to an existing profile
        profile = certificate_config.get("profile")
        lineage = get_lineage(certificate_config)
        if lineage:
            if profile not in profiles:
                raise ValueError(
                    "Profile `{0}` used by certificate `{1}` does not exist.".format(
                        profile, lineage
                    )
                )

            if lineage in lineages:
                raise ValueError(
                    "Certificate with name `{0}` is duplicated.".format(lineage)
                )
            lineages.add(lineage)

    # Check that each files_mode and dirs_mode is a valid POSIX mode
    files_mode = config.get("acme", {}).get("certs_permissions", {}).get("files_mode")
    if files_mode and files_mode > 511:
        raise ValueError("Invalid files_mode `{0}` provided.".format(oct(files_mode)))
    dirs_mode = config.get("acme", {}).get("certs_permissions", {}).get("dirs_mode")
    if dirs_mode and dirs_mode > 511:
        raise ValueError("Invalid dirs_mode `{0}` provided.".format(oct(files_mode)))
