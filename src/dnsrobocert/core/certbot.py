#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import annotations

import logging
import os
import re
import sys
import threading

import coloredlogs
from certbot import main

import dnsrobocert
from dnsrobocert.core import config, utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)

_DEFAULT_FLAGS = [
    "-n",
    "--user-agent-comment",
    "DNSroboCert/{0}".format(dnsrobocert.__version__),
    "--preferred-chain",
    "ISRG Root X1",
]


def account(config_path: str, directory_path: str, lock: threading.Lock) -> None:
    dnsrobocert_config = config.load(config_path)
    acme = dnsrobocert_config.get("acme", {})
    email = acme.get("email_account")

    if not email:
        LOGGER.warning(
            "Parameter acme.email_account is not set, skipping ACME registration."
        )
        return

    url = config.get_acme_url(dnsrobocert_config)

    utils.execute(
        [
            sys.executable,
            "-m",
            "dnsrobocert.core.certbot",
            "register",
            *_DEFAULT_FLAGS,
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
        lock=lock,
    )


def certonly(
    config_path: str,
    directory_path: str,
    lineage: str,
    lock: threading.Lock,
    domains: list[str] | None = None,
    force_renew: bool = False,
    reuse_key: bool = False,
    key_type: str = "rsa",
) -> None:
    if not domains:
        return

    url = config.get_acme_url(config.load(config_path))

    additional_params = []
    if force_renew:
        additional_params.append("--force-renew")
    if reuse_key:
        additional_params.append("--reuse-key")
    if key_type:
        additional_params.extend(["--key-type", key_type])

    for domain in domains:
        additional_params.append("-d")
        additional_params.append(domain)

    utils.execute(
        [
            sys.executable,
            "-m",
            "dnsrobocert.core.certbot",
            "certonly",
            *_DEFAULT_FLAGS,
            "--config-dir",
            directory_path,
            "--work-dir",
            os.path.join(directory_path, "workdir"),
            "--logs-dir",
            os.path.join(directory_path, "logs"),
            "--manual",
            "--preferred-challenges=dns",
            "--manual-auth-hook",
            _hook_cmd("auth", config_path, lineage),
            "--manual-cleanup-hook",
            _hook_cmd("cleanup", config_path, lineage),
            "--expand",
            "--deploy-hook",
            _hook_cmd("deploy", config_path, lineage),
            "--server",
            url,
            "--cert-name",
            lineage,
            *additional_params,
        ],
        lock=lock,
    )


def _issue(config_path: str, directory_path: str, lock: threading.Lock) -> None:
    dnsrobocert_config = config.load(config_path)

    if dnsrobocert_config:
        certificates = dnsrobocert_config.get("certificates", {})
        for certificate in certificates:
            try:
                lineage = config.get_lineage(certificate)
                domains = certificate["domains"]
                force_renew = certificate.get("force_renew", False)
                reuse_key = certificate.get("reuse_key", False)
                key_type = certificate.get("key_type", "rsa")
                LOGGER.info(
                    f"Handling the certificate for domain(s): {', '.join(domains)}"
                )
                certonly(
                    config_path,
                    directory_path,
                    lineage,
                    lock,
                    domains,
                    force_renew=force_renew,
                    reuse_key=reuse_key,
                    key_type=key_type,
                )
            except BaseException as error:
                LOGGER.error(
                    f"An error occurred while processing certificate config {certificate}:\n{error}"
                )

        LOGGER.info("Revoke and delete certificates if needed")
        lineages = {config.get_lineage(certificate) for certificate in certificates}
        for domain in os.listdir(os.path.join(directory_path, "live")):
            if domain != "README":
                domain = re.sub(r"^\*\.", "", domain)
                if domain not in lineages:
                    LOGGER.info(f"Removing the certificate {domain}")
                    revoke(config_path, directory_path, domain, lock)


def renew(config_path: str, directory_path: str, lock: threading.Lock) -> None:
    _issue(config_path, directory_path, lock)


def revoke(
    config_path: str, directory_path: str, lineage: str, lock: threading.Lock
) -> None:
    url = config.get_acme_url(config.load(config_path))

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
        ],
        lock=lock,
    )


def _hook_cmd(hook_type: str, config_path: str, lineage: str | None = None) -> str:
    command = (
        f'{sys.executable} -m dnsrobocert.core.hooks -t {hook_type} -c "{config_path}"'
    )
    if lineage:
        command = f'{command} -l "{lineage}"'
    return command


if __name__ == "__main__":
    sys.exit(main.main())
