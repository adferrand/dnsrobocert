#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import logging
import os
import sys
from typing import Dict, List

from certbot import main
from dnsrobocert.core import config, utils
import coloredlogs

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def account(config_path: str, directory_path: str):
    dnsrobocert_config = config.load(config_path)
    acme = dnsrobocert_config.get("acme", {})
    email = acme.get("email_account")

    if not email:
        LOGGER.warning(
            "Parameter acme.email_account is not set, skipping ACME registration."
        )
        return

    url = _acme_url(dnsrobocert_config)

    utils.execute(
        [
            sys.executable,
            "-m",
            "dnsrobocert.core.certbot",
            "register",
            "-n",
            "--config-dir",
            directory_path,
            "--work-dir",
            os.path.join(directory_path, "workdir"),
            "--logs-dir",
            os.path.join(directory_path, "logs"),
            "-m",
            email,
            "--agree-tos",
            "--server",
            url,
        ],
        check=False,
    )


def certonly(
    config_path: str,
    directory_path: str,
    primary: str,
    secondaries: List[str] = None,
    force_renew: bool = False,
):
    dnsrobocert_config = config.load(config_path)
    url = _acme_url(dnsrobocert_config)

    additional_params = []
    if force_renew:
        additional_params.append("--force-renew")
    if secondaries:
        for secondary in secondaries:
            additional_params.append("-d")
            additional_params.append(secondary)

    utils.execute(
        [
            sys.executable,
            "-m",
            "dnsrobocert.core.certbot",
            "certonly",
            "-n",
            "--config-dir",
            directory_path,
            "--work-dir",
            os.path.join(directory_path, "workdir"),
            "--logs-dir",
            os.path.join(directory_path, "logs"),
            "--manual",
            "--preferred-challenges=dns",
            "--manual-auth-hook",
            _hook_cmd("auth", config_path, primary),
            "--manual-cleanup-hook",
            _hook_cmd("cleanup", config_path, primary),
            "--manual-public-ip-logging-ok",
            "--expand",
            "--deploy-hook",
            _hook_cmd("deploy", config_path, primary),
            "--server",
            url,
            "-d",
            primary,
            *additional_params,
        ]
    )


def renew(config_path: str, directory_path: str):
    dnsrobocert_config = config.load(config_path)

    if dnsrobocert_config:
        utils.execute(
            [
                sys.executable,
                "-m",
                "dnsrobocert.core.certbot",
                "renew",
                "-n",
                "--config-dir",
                directory_path,
                "--deploy-hook",
                _hook_cmd("deploy", config_path),
                "--work-dir",
                os.path.join(directory_path, "workdir"),
                "--logs-dir",
                os.path.join(directory_path, "logs"),
            ]
        )


def revoke(config_path: str, directory_path: str, lineage: str):
    dnsrobocert_config = config.load(config_path)
    url = _acme_url(dnsrobocert_config)

    utils.execute(
        [
            sys.executable,
            "-m",
            "dnsrobocert.core.certbot",
            "revoke",
            "-n",
            "--config-dir",
            directory_path,
            "--work-dir",
            os.path.join(directory_path, "workdir"),
            "--logs-dir",
            os.path.join(directory_path, "logs"),
            "--server",
            url,
            "--cert-path",
            os.path.join(directory_path, "live", lineage, "cert.pem"),
        ]
    )


def _hook_cmd(hook_type: str, config_path: str, lineage: str = None) -> str:
    command = '{0} -m dnsrobocert.core.hooks -t {1} -c "{2}"'.format(
        sys.executable, hook_type, config_path
    )
    if lineage:
        command = '{0} -l "{1}"'.format(command, lineage)
    return command


def _acme_url(dnsrobocore_config: Dict) -> str:
    acme = dnsrobocore_config.get("acme", {})

    directory_url = dnsrobocore_config.get("directory_url")
    if directory_url:
        return directory_url

    api_version = acme.get("api_version", 2)
    staging = acme.get("staging", False)

    if api_version < 2:
        domain = "acme-staging" if staging else "acme-v01"
    else:
        domain = "acme-staging-v02" if staging else "acme-v02"

    return "https://{0}.api.letsencrypt.org/directory".format(domain)


if __name__ == "__main__":
    sys.exit(main.main())
