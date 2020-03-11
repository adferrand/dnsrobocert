import logging
import os
from typing import Any, Dict, Optional
import re

import coloredlogs
import jsonschema
import pkg_resources
import yaml

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def load(config_path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(config_path):
        LOGGER.error("Configuration file {0} does not exist.".format(config_path))
        return None

    with open(config_path) as file_h:
        config = yaml.load(file_h.read(), yaml.FullLoader)

    schema_path = pkg_resources.resource_filename("dnsrobocert", "schema.yml")
    with open(schema_path) as file_h:
        schema = yaml.load(file_h.read(), yaml.FullLoader)

    if not config:
        LOGGER.error("DNSroboCert configuration is empty.")
        return None

    try:
        jsonschema.validate(instance=config, schema=schema)
        _business_check(config)
        return config
    except jsonschema.ValidationError as e:
        message = """\
Error while validating dnsrobocert configuration for node path {0}:
{1}
-----
{2}\
""".format(
            "/" + "/".join([str(item) for item in e.path]),
            e.message,
            yaml.dump(e.instance)
            if isinstance(e.instance, (dict, list))
            else str(e.instance),
        )
        LOGGER.error(message)
        return None


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


def get_lineage(certificate_config: Dict[str, Any]) -> Optional[str]:
    return (
        certificate_config.get("name")
        if certificate_config.get("name")
        else re.sub(r"^\*\.", "", certificate_config.get("domains", [None])[0])
    )


def get_acme_url(config: Dict[str, Any]) -> str:
    acme = config.get("acme", {})

    directory_url = config.get("directory_url")
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


def _business_check(config: Dict[str, Any]):
    profiles = [profile["name"] for profile in config.get("profiles", [])]
    for certificate_config in config.get("certificates", []):
        # Check that every certificate is associated to an existing profile
        profile = certificate_config.get("profile")
        lineage = get_lineage(certificate_config)
        if profile not in profiles:
            raise ValueError(
                "Profile `{0}` used by certificate `{1}` does not exist.".format(
                    profile, lineage
                )
            )

        # Check that each files_mode and dirs_mode is a valid POSIX mode
        files_mode = certificate_config.get("files_mode")
        if files_mode and files_mode > 511:
            raise ValueError(
                "Invalid files_mode `{0}` provided for certificate {1}".format(
                    oct(files_mode), lineage
                )
            )
