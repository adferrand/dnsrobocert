import logging
import os
from typing import Dict

import jsonschema
import pkg_resources
import yaml
import coloredlogs

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def load(config_path: str) -> Dict:
    if not os.path.exists(config_path):
        LOGGER.warning("Configuration file {0} does not exist.".format(config_path))
        return {}

    with open(config_path) as file_h:
        config = yaml.load(file_h.read(), yaml.FullLoader)

    schema_path = pkg_resources.resource_filename("dnsrobocert", "schema.yml")
    with open(schema_path) as file_h:
        schema = yaml.load(file_h.read(), yaml.FullLoader)

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
        raise ValueError(message) from None


def _business_check(config: Dict):
    profiles = config.get("profiles", {}).keys()
    for lineage, cert_config in config.get("certificates", {}).items():
        # Check that every certificate is associated to an existing profile
        profile = cert_config.get("profile")
        if profile not in profiles:
            raise ValueError(
                "Profile `{0}` used by certificate `{1}` does not exist.".format(
                    profile, lineage
                )
            )

        # Check that each files_mode and dirs_mode is a valid POSIX mode
        files_mode = cert_config.get("files_mode")
        if files_mode and files_mode > 511:
            raise ValueError(
                "Invalid files_mode `{0}` provided for certificate {1}".format(
                    oct(files_mode), lineage
                )
            )
