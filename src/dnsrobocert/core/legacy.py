import logging
import os
import re
from typing import Any, Dict
import shlex

import coloredlogs
import yaml
from lexicon import config, parser

LEGACY_CONFIGURATION_PATH = "/etc/letsencrypt/domains.conf"
LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)

LEXICON_ARGPARSER = parser.generate_cli_main_parser()


def migrate(config_path):
    if os.path.exists(config_path):
        return

    if not os.path.exists(LEGACY_CONFIGURATION_PATH):
        return

    provider = os.environ.get("LEXICON_PROVIDER")
    if not provider:
        LOGGER.error("Error, LEXICON_PROVIDER environment variable is not set!")

    envs, configs, args = _gather_parameters(provider)

    provider_config = {"provider": provider}
    migrated_config = {
        "profiles": {provider: provider_config},
        "certificates": _extract_certificates(envs, provider),
    }

    for key, value in configs.get(provider, {}).items():
        provider_config.setdefault("provider_options", {})[  # type: ignore
            key
        ] = value

    env_key_prefix = "LEXICON_{0}_".format(provider.upper())
    for key, value in envs.items():
        if key.startswith(env_key_prefix):
            provider_config.setdefault(  # type: ignore
                "provider_options", {}
            )[
                key.replace(env_key_prefix, "").lower()
            ] = value

    _handle_specific_envs_variables(envs, migrated_config, provider)

    for key, value in args.get(provider, {}).items():
        provider_config.setdefault("provider_options", {})[  # type: ignore
            key
        ] = value
    if args.get('delegated'):
        provider_config['delegated_subdomain'] = args.get('delegated')

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
        LOGGER.warning("Please visit https://example.com for more details. ")
        LOGGER.warning(
            "New configuration file is available at `{0}`".format(example_config_path)
        )
        LOGGER.warning(
            "Quick fix (if directory `{0}` is persisted): rename this file to `{1}`".format(
                os.path.dirname(config_path), os.path.basename(config_path)
            )
        )

        os.makedirs(os.path.dirname(example_config_path), exist_ok=True)
        with open(example_config_path, "w") as f:
            f.write(new_config_data)

    return example_config_path


def _handle_specific_envs_variables(
    envs: Dict[str, str], migrated_config: Dict[str, Any], profile: str
):
    if envs.get("LETSENCRYPT_USER_MAIL"):
        migrated_config.setdefault("acme", {})["email_account"] = envs.get(
            "LETSENCRYPT_USER_MAIL"
        )

    if envs.get("LETSENCRYPT_STAGING") == "true":
        migrated_config.setdefault("acme", {})["staging"] = True

    if envs.get("LETSENCRYPT_ACME_V1 ") == "true":
        migrated_config.setdefault("acme", {})["api_version"] = 1

    if envs.get("CRON_TIME_STRING"):
        migrated_config.setdefault("acme", {})["crontime_renew"] = envs.get(
            "CRON_TIME_STRING"
        )

    if envs.get("CERTS_FILES_MODE"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "files_mode"
        ] = int(envs["CERTS_FILES_MODE"])

    if envs.get("CERTS_DIRS_MODE"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "dirs_mode"
        ] = int(envs["CERTS_DIRS_MODE"])

    if envs.get("CERTS_USER_OWNER"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "users"
        ] = int(envs["CERTS_USER_OWNER"])

    if envs.get("CERTS_GROUP_OWNER"):
        migrated_config.setdefault("acme", {}).setdefault("certs_permissions", {})[
            "group"
        ] = int(envs["CERTS_GROUP_OWNER"])

    if envs.get("LEXICON_SLEEP_TIME"):
        migrated_config["profiles"][profile]["sleep_time"] = int(
            envs["LEXICON_SLEEP_TIME"]
        )

    if envs.get("LEXICON_MAX_CHECKS"):
        migrated_config["profiles"][profile]["max_checks"] = int(
            envs["LEXICON_MAX_CHECKS"]
        )

    if envs.get("DEPLOY_HOOK"):
        migrated_config["profiles"][profile]["deploy_hook"] = int(envs["DEPLOY_HOOK"])

    if envs.get("PFX_EXPORT") == "true":
        for value in migrated_config.get("certificates", {}).values():
            value.setdefault("pfx", {})["export"] = True
            if envs.get("PFX_EXPORT_PASSPHRASE"):
                value["pfx"]["passphrase"] = envs["PFX_EXPORT_PASSPHRASE"]


def _gather_parameters(provider):
    env_variables_of_interest = {
        name: value
        for name, value in os.environ.items()
        if name.startswith("LETSENCRYPT_")
        or name.startswith("PFX_")
        or name.startswith("CERTS_")
        or name in ["CRON_TIME_STRING", "DOCKER_CLUSTER_PROVIDER", "DEPLOY_HOOK"]
    }

    command_line_params = {}
    command = [provider, 'create', 'example.net', 'TXT',
               *shlex.split(os.environ.get('LEXICON_PROVIDER_OPTIONS', '')),
               *shlex.split(os.environ.get('LEXICON_OPTIONS', ''))]
    try:
        args, _ = LEXICON_ARGPARSER.parse_known_args(command)
    except SystemExit:
        args = None

    resolver = config.ConfigResolver()
    if args:
        resolver.with_args(args)
    resolver.with_env()
    resolver.with_config_dir(os.path.dirname(LEGACY_CONFIGURATION_PATH))

    lexicon_files_config: Dict[str, Any] = {}
    for source in resolver._config_sources:
        if isinstance(source, config.ProviderFileConfigSource):
            provider = list(source._parameters.keys())[0]
            lexicon_files_config.setdefault(provider, {}).update(
                source._parameters[provider]
            )
        elif isinstance(source, config.FileConfigSource) and not isinstance(
            source, config.ProviderFileConfigSource
        ):
            lexicon_files_config.update(source._parameters)
        elif isinstance(source, config.EnvironmentConfigSource):
            env_variables_of_interest.update(source._parameters)
        elif isinstance(source, config.ArgsConfigSource):
            command_line_params = {
                provider: {
                    key: value for key, value in source._parameters.items()
                    if key not in ('delegated', 'config_dir', 'provider_name', 'action', 'domain',
                                   'type', 'name', 'content', 'ttl', 'priority', 'identifier',
                                   'log_level', 'output') and value is not None
                }
            }
            if source._parameters['delegated']:
                command_line_params['delegated'] = source._parameters['delegated']
            print(command_line_params)

    return env_variables_of_interest, lexicon_files_config, command_line_params


def _extract_certificates(envs: Dict[str, str], profile: str) -> Dict[str, Any]:
    certificates: Dict[str, Any] = {}

    with open(os.path.join(LEGACY_CONFIGURATION_PATH)) as f:
        lines = f.read().splitlines()

    for line in lines:
        if line.strip():
            lineage = None
            additional_certs = []
            autorestart = []
            autocmd = []

            items = re.split("\\s+", line)
            for index, item in enumerate(items):
                if index == 0:
                    lineage = item
                    continue

                if item.startswith("autorestart-containers="):
                    containers = item.replace("autorestart-containers=", "").split(",")
                    containers = [container.strip() for container in containers]
                    autorestart.append(
                        {
                            "swarm_services"
                            if envs.get("DOCKER_CLUSTER_PROVIDER") == "swarm"
                            else "containers": containers,
                        }
                    )
                    continue

                if item.startswith("autocmd-containers="):
                    item = " ".join(items[index:])
                    directives = item.replace("autocmd-containers=", "").split(",")
                    for directive in directives:
                        [container, command] = directive.split(":")
                        autocmd.append({"containers": container, "cmd": command})
                    break

                additional_certs.append(item)

            if lineage:
                certificates[lineage] = {}
                certificates[lineage]["profile"] = profile
                if additional_certs:
                    certificates[lineage]["san"] = additional_certs
                if autorestart:
                    certificates[lineage]["autorestart"] = autorestart
                if autocmd:
                    certificates[lineage]["autocmd"] = autocmd

    return certificates
