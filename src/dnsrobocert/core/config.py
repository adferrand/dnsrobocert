import logging
import os
import re
from copy import deepcopy
from functools import reduce
from typing import Any, Dict, Optional, Set, Union

import coloredlogs
import jsonschema
import pkg_resources
import yaml

from dnsrobocert.core import utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def load(config_path: str, merge_drc_envs: bool = False) -> Optional[Dict[str, Any]]:
    if not os.path.exists(config_path) and not merge_drc_envs:
        LOGGER.error(f"Configuration file {config_path} does not exist.")
        return None

    if os.path.exists(config_path):
        with open(config_path) as file_h:
            raw_config = file_h.read()

        raw_config = _inject_env_variables(raw_config)

        try:
            config = yaml.load(raw_config, Loader=yaml.FullLoader)
        except BaseException:
            message = """
Error while validating dnsrobocert configuration:
Configuration file is not a valid YAML file.\
    """
            LOGGER.error(message)
            return None

        if not config:
            message = """
Error while validating dnsrobocert configuration:
Configuration file is empty.\
    """
            LOGGER.error(message)
            return None
    else:
        config = {}

    if merge_drc_envs:
        config = _deep_merge(extract_config_from_drc_env(), config)

    schema_path = pkg_resources.resource_filename("dnsrobocert", "schema.yml")
    with open(schema_path) as file_h:
        schema = yaml.load(file_h.read(), yaml.FullLoader)

    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        node = "/" + "/".join([str(item) for item in e.path])
        message = f"""\
Error while validating dnsrobocert configuration for node path {node}:
{e.message}.
-----
{yaml.dump(config)}\
    """
        LOGGER.error(message)
        return None

    try:
        _values_conversion(config)
        _business_check(config)
    except ValueError as e:
        message = f"""\
Error while validating dnsrobocert configuration:
{str(e)}
-----
{yaml.dump(config)}\
"""
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
            f"Could not find the certificate name for certificate config: {certificate_config}"
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

    return f"https://{domain}.api.letsencrypt.org/directory"


def find_profile_for_lineage(config: Dict[str, Any], lineage: str) -> Dict[str, Any]:
    certificate = get_certificate(config, lineage)
    if not certificate:
        raise RuntimeError(
            f"Error, certificate named `{lineage}` could not be found in configuration."
        )
    profile_name = certificate.get("profile")
    if not profile_name:
        raise RuntimeError(
            f"Error, profile named `{lineage}` could not be found in configuration."
        )

    return get_profile(config, profile_name)


def extract_config_from_drc_env() -> Dict[str, Any]:
    schema_path = pkg_resources.resource_filename("dnsrobocert", "schema.yml")
    with open(schema_path) as file_h:
        schema = yaml.load(file_h.read(), yaml.FullLoader)

    drc_vars = [(key, re.sub(r"^DRC__", "", key).split("__"), value)
                for key, value in os.environ.items()
                if key.startswith('DRC__')]
    drc_vars.sort(key=lambda item: item[0])

    config = {}

    for var_name, fragments, value in drc_vars:
        parent_element: Union[dict, list] = config
        parent_description = schema
        try:
            for index, fragment in enumerate(fragments):
                fragment = fragment.lower()
                if parent_description["type"] == "array":
                    if not fragment.isnumeric():
                        raise ValueError(f"expected a number instead of __{fragment.upper()}")
                    fragment = int(fragment)
                    current_description = parent_description["items"]
                    if current_description["type"] == "object":
                        current_element = parent_element[fragment] if fragment < len(parent_element) else {}
                    elif current_description["type"] == "array":
                        current_element = parent_element[fragment] if fragment < len(parent_element) else []
                    else:
                        if index + 1 < len(fragments):
                            raise ValueError(f"variable name should finish with __{fragment}")
                        parent_element.insert(fragment, _convert_primitive(value, current_description["type"]))
                        break
                    if fragment >= len(parent_element):
                        parent_element.insert(fragment, current_element)
                else:  # Can only be an object
                    current_description = parent_description.get("properties", {fragment: {"type": "any"}}).get(fragment)
                    if not current_description:
                        raise ValueError(f"variable name should not contain __{fragment.upper()}")
                    if current_description["type"] == "object":
                        current_element = parent_element.setdefault(fragment, {})
                    elif current_description["type"] == "array":
                        current_element = parent_element.setdefault(fragment, [])
                    else:
                        if index + 1 < len(fragments):
                            raise ValueError(f"variable name should finish with __{fragment.upper()}")
                        parent_element[fragment] = _convert_primitive(value, current_description["type"])
                        break
                parent_element = current_element
                parent_description = current_description
        except BaseException as e:
            LOGGER.warning(f"Environment variable {var_name} is invalid: {str(e)}.")

    return config


def _deep_merge(dict1: dict, dict2: dict) -> dict:
    def merge_into(d1: dict, d2: dict):
        for key in d2:
            if key not in d1 or not isinstance(d1[key], dict):
                d1[key] = deepcopy(d2[key])
            else:
                d1[key] = merge_into(d1[key], d2[key])
        return d1

    return reduce(merge_into, [dict1, dict2], {})


def _convert_primitive(value: str, field_type: str):
    if field_type == "boolean":
        return value == "true"
    if field_type == "integer":
        return int(value)
    # For anything else (string, any, multiple choices), just take the value as it
    return value


def _inject_env_variables(raw_config: str) -> str:
    def replace(match):
        entry = match.group(0)

        if "$${" in entry:
            return entry.replace("$${", "${")

        variable_name = match.group(1)
        if variable_name not in os.environ:
            raise ValueError(
                f"Error while parsing config: environment variable {variable_name} does not exist."
            )

        return os.environ[variable_name]

    return re.sub(r"\${1,2}{(\S+)}", replace, raw_config)


def _values_conversion(config: Dict[str, Any]) -> None:
    certs_permissions = config.get("acme", {}).get("certs_permissions", {})
    files_mode = certs_permissions.get("files_mode")
    if isinstance(files_mode, str):
        certs_permissions["files_mode"] = int(files_mode, 8)
    dirs_mode = certs_permissions.get("dirs_mode")
    if isinstance(dirs_mode, str):
        certs_permissions["dirs_mode"] = int(dirs_mode, 8)


def _business_check(config: Dict[str, Any]) -> None:
    print(config)
    profiles = [profile["name"] for profile in config.get("profiles", [])]
    lineages: Set[str] = set()
    for certificate_config in config.get("certificates", []):
        # Check that every certificate is associated to an existing profile
        profile = certificate_config.get("profile")
        lineage = get_lineage(certificate_config)
        if lineage:
            if profile not in profiles:
                raise ValueError(
                    f"Profile `{profile}` used by certificate `{lineage}` does not exist."
                )

            if lineage in lineages:
                raise ValueError(f"Certificate with name `{lineage}` is duplicated.")
            lineages.add(lineage)

    # Check that each files_mode and dirs_mode is a valid POSIX mode
    files_mode = config.get("acme", {}).get("certs_permissions", {}).get("files_mode")
    if files_mode and files_mode > 511:
        raise ValueError("Invalid files_mode `{0}` provided.".format(oct(files_mode)))
    dirs_mode = config.get("acme", {}).get("certs_permissions", {}).get("dirs_mode")
    if dirs_mode and dirs_mode > 511:
        raise ValueError("Invalid dirs_mode `{0}` provided.".format(oct(files_mode)))
