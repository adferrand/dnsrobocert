from __future__ import annotations

import logging
import os
import re
import shlex
from copy import deepcopy
from functools import reduce
from typing import Any

import coloredlogs
import yaml
from lexicon._private.parser import generate_cli_main_parser
from lexicon.config import (
    ArgsConfigSource,
    ConfigResolver,
    EnvironmentConfigSource,
    FileConfigSource,
)

from dnsrobocert.core import utils

LEGACY_CONFIGURATION_PATH = "/etc/letsencrypt/domains.conf"
LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)

LEXICON_ARGPARSER = generate_cli_main_parser()


def migrate(config_path: str) -> str | None:
    if os.path.exists(config_path):  # pragma: nocover
        return None

    if not os.path.exists(LEGACY_CONFIGURATION_PATH):  # pragma: nocover
        return None

    provider = os.environ.get("LEXICON_PROVIDER")
    if not provider:  # pragma: nocover
        LOGGER.error("Error, LEXICON_PROVIDER environment variable is not set!")
        return None

    envs, configs, args = _gather_parameters(provider)

    provider_config = {"name": provider, "provider": provider}
    migrated_config = {
        "profiles": [provider_config],
        "certificates": _extract_certificates(envs, provider),
    }

    for key, value in configs.get(provider, {}).items():
        provider_config.setdefault("provider_options", {})[key] = value  # type: ignore

    env_key_prefix = "LEXICON_{0}_".format(provider.upper())
    for key, value in envs.items():
        if key.startswith(env_key_prefix):
            provider_config.setdefault("provider_options", {})[  # type: ignore
                key.replace(env_key_prefix, "").lower()
            ] = value

    _handle_specific_envs_variables(envs, migrated_config)

    for key, value in args.get(provider, {}).items():
        provider_config.setdefault("provider_options", {})[key] = value  # type: ignore

    example_config_path = os.path.join(
        os.path.dirname(config_path), "config-generated.yml"
    )

    current_config_data = None
    if os.path.exists(example_config_path):
        with open(example_config_path) as f:
            current_config_data = f.read()
    new_config_data = yaml.dump(migrated_config)

    if current_config_data != new_config_data:
        LOGGER.warning(
            "Legacy configuration detected. Support for legacy configurations will be dropped soon."
        )
        LOGGER.warning(
            "Please visit https://adferrand.github.io/dnsrobocert/miscellaneous.html#migration-from-docker-letsencrypt-dns "
            "for more details. "
        )
        LOGGER.warning(f"New configuration file is available at {example_config_path}")
        LOGGER.warning(
            f"Quick fix (if directory {os.path.dirname(config_path)} is persisted): "
            f"rename this file to {os.path.basename(config_path)}"
        )

        os.makedirs(os.path.dirname(example_config_path), exist_ok=True)
        with open(example_config_path, "w") as f:
            f.write(new_config_data)

    return example_config_path


def _handle_specific_envs_variables(
    envs: dict[str, str], migrated_config: dict[str, Any]
) -> None:
    if envs.get("LETSENCRYPT_USER_MAIL"):
        migrated_config.setdefault("acme", {})["email_account"] = envs.get(
            "LETSENCRYPT_USER_MAIL"
        )

    if envs.get("LETSENCRYPT_STAGING") == "true":
        migrated_config.setdefault("acme", {})["staging"] = True

    if envs.get("LETSENCRYPT_ACME_V1") == "true":
        migrated_config.setdefault("acme", {})["api_version"] = 1

    if envs.get("CRON_TIME_STRING"):
        migrated_config.setdefault("acme", {})["crontime_renew"] = envs.get(
            "CRON_TIME_STRING"
        )

    if envs.get("CERTS_FILES_MODE"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "files_mode"
        ] = int(envs["CERTS_FILES_MODE"], 8)

    if envs.get("CERTS_DIRS_MODE"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "dirs_mode"
        ] = int(envs["CERTS_DIRS_MODE"], 8)

    if envs.get("CERTS_USER_OWNER"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "user"
        ] = str(envs["CERTS_USER_OWNER"])

    if envs.get("CERTS_GROUP_OWNER"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "group"
        ] = str(envs["CERTS_GROUP_OWNER"])

    if envs.get("LEXICON_SLEEP_TIME"):
        migrated_config["profiles"][0]["sleep_time"] = int(envs["LEXICON_SLEEP_TIME"])

    if envs.get("LEXICON_MAX_CHECKS"):
        migrated_config["profiles"][0]["max_checks"] = int(envs["LEXICON_MAX_CHECKS"])

    if envs.get("LEXICON_TTL"):
        migrated_config["profiles"][0]["ttl"] = int(envs["LEXICON_TTL"])

    if envs.get("DEPLOY_HOOK"):
        for value in migrated_config.get("certificates", []):
            value["deploy_hook"] = envs["DEPLOY_HOOK"]

    if envs.get("PFX_EXPORT") == "true":
        for value in migrated_config.get("certificates", []):
            value.setdefault("pfx", {})["export"] = True
            if envs.get("PFX_EXPORT_PASSPHRASE"):
                value["pfx"]["passphrase"] = envs["PFX_EXPORT_PASSPHRASE"]


def _gather_parameters(
    provider: str,
) -> tuple[dict[str, str], dict[str, Any], dict[str, dict[str, Any]]]:
    env_variables_of_interest = {
        name: value
        for name, value in os.environ.items()
        if name.startswith("LETSENCRYPT_")
        or name.startswith("PFX_")
        or name.startswith("CERTS_")
        or name in ["CRON_TIME_STRING", "DOCKER_CLUSTER_PROVIDER", "DEPLOY_HOOK"]
    }

    command_line_params = {}
    command = [
        *shlex.split(os.environ.get("LEXICON_OPTIONS", "")),
        provider,
        "create",
        "example.net",
        "TXT",
        *shlex.split(os.environ.get("LEXICON_PROVIDER_OPTIONS", "")),
    ]
    try:
        args, _ = LEXICON_ARGPARSER.parse_known_args(command)
    except SystemExit:  # pragma: nocover
        args = None

    resolver = ConfigResolver()
    if args:
        resolver.with_args(args)
    resolver.with_env()
    resolver.with_config_dir(os.path.dirname(LEGACY_CONFIGURATION_PATH))

    lexicon_files_config: dict[str, Any] = {}
    for source in resolver._config_sources:
        if isinstance(source, FileConfigSource):
            _deep_merge(lexicon_files_config, source._parameters)
        elif isinstance(source, EnvironmentConfigSource):
            env_variables_of_interest.update(source._parameters)
        elif isinstance(source, ArgsConfigSource):
            command_line_params = {
                provider: {
                    key: value
                    for key, value in source._parameters.items()
                    if key
                    not in (
                        "delegated",
                        "resolve_zone_name",
                        "config_dir",
                        "provider_name",
                        "action",
                        "domain",
                        "type",
                        "name",
                        "content",
                        "ttl",
                        "priority",
                        "identifier",
                        "log_level",
                        "output",
                    )
                    and value is not None
                }
            }
            if source._parameters["delegated"]:
                command_line_params["delegated"] = source._parameters["delegated"]

    return env_variables_of_interest, lexicon_files_config, command_line_params


def _extract_certificates(envs: dict[str, str], profile: str) -> list[dict[str, Any]]:
    certificates: list[dict[str, Any]] = []

    with open(os.path.join(LEGACY_CONFIGURATION_PATH)) as f:
        lines = f.read().splitlines()

    for line in lines:
        if line.strip():
            domains = []
            autorestart = []
            autocmd = []

            items = re.split("\\s+", line)
            for index, item in enumerate(items):
                if item.startswith("autorestart-containers="):
                    containers = item.replace("autorestart-containers=", "").split(",")
                    containers = [container.strip() for container in containers]
                    autorestart.append(
                        {
                            (
                                "swarm_services"
                                if envs.get("DOCKER_CLUSTER_PROVIDER") == "swarm"
                                else "containers"
                            ): containers,
                        }
                    )
                    continue

                if item.startswith("autocmd-containers="):
                    item = " ".join(items[index:])
                    directives = item.replace("autocmd-containers=", "").split(",")
                    for directive in directives:
                        [container, command] = directive.split(":")
                        autocmd.append({"containers": [container], "cmd": command})
                    break

                domains.append(item)

            if domains:
                certificate: dict[str, Any] = {
                    "name": utils.normalize_lineage(domains[0]),
                    "domains": domains,
                    "profile": profile,
                }
                if autorestart:
                    certificate["autorestart"] = autorestart
                if autocmd:
                    certificate["autocmd"] = autocmd

                certificates.append(certificate)

    return certificates


def _deep_merge(*dicts: dict[str, Any]) -> dict[str, Any]:
    def merge_into(d1: dict[str, Any], d2: dict[str, Any]) -> dict[str, Any]:
        for key in d2:
            if key not in d1 or not isinstance(d1[key], dict):
                d1[key] = deepcopy(d2[key])
            else:
                d1[key] = merge_into(d1[key], d2[key])
        return d1

    return reduce(merge_into, dicts[1:], dicts[0])
