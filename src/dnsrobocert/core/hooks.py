#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, List

import coloredlogs
import OpenSSL
import pem
from dns import resolver
from lexicon.client import Client
from lexicon.config import ConfigResolver

from dnsrobocert.core import config as dnsrobocert_config
from dnsrobocert.core import utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def main(args: List[str] = None):
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--type", choices=["auth", "cleanup", "deploy"], required=True
    )
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-l", "--lineage", default="None", required=False)

    parsed_args = parser.parse_args(args)
    config = dnsrobocert_config.load(parsed_args.config)

    globals()[parsed_args.type](config, parsed_args.lineage)


def auth(config: Dict[str, str], lineage: str):
    profile_name, profile_content = _load_profile(config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    _txt_challenge(profile_name, profile_content, token, domain, action="create")

    sleep_time = profile_content.get("sleep_time", 30)
    max_checks = profile_content.get("max_checks", 0)
    if max_checks:
        checks = 0
        while True:
            checks = checks + 1
            if checks > max_checks:
                LOGGER.error(
                    "The challenge was not propagated after the maximum tries of {0}".format(
                        max_checks
                    )
                )
                raise RuntimeError("Auth hook failed.")

            LOGGER.info(
                "Wait {0} seconds before checking that TXT _acme-challenge.{1} has the expected value "
                "(try {2}/{3})".format(sleep_time, domain, checks, max_checks)
            )
            time.sleep(sleep_time)

            answers = resolver.query("_acme-challenge.{0}.".format(domain), "TXT")
            validation_answers = [
                rdata
                for rdata in answers
                for txt_string in rdata.strings
                if txt_string.decode("utf-8") == token
            ]

            if validation_answers:
                LOGGER.info(
                    "TXT _acme-challenge.{0} has the expected token value (try {1}/{2})".format(
                        domain, checks, max_checks
                    )
                )
                break

            LOGGER.info(
                "TXT _acme-challenge.{0} did not have the expected token value (try {1}/{2})".format(
                    domain, checks, max_checks
                )
            )
    else:
        LOGGER.info(
            "Wait {0} seconds to let TXT _acme-challenge.{1} entry be propagated".format(
                sleep_time, domain
            )
        )
        time.sleep(sleep_time)


def cleanup(config: Dict[str, str], lineage: str):
    profile_name, profile_content = _load_profile(config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    _txt_challenge(profile_name, profile_content, token, domain, action="delete")


def deploy(config: Dict[str, Any], _no_lineage: Any):
    lineage_path = os.environ["RENEWED_LINEAGE"]
    lineage = os.path.basename(lineage_path)
    cert_config = config["certificates"][lineage]
    _, profile_content = _load_profile(config, lineage)

    _pfx_export(cert_config, lineage_path)
    _fix_permissions(config.get("acme", {}).get("certs_permissions", {}), lineage_path)
    _autorestart(cert_config)
    _autocmd(cert_config)
    _deploy_hook(profile_content)


def _load_profile(config: Dict[str, Any], domain: str):
    certificates = [
        value
        for key, value in config.get("certificates", {}).items()
        if key == domain or domain in value.get("san", [])
    ]

    if not certificates:
        LOGGER.error(
            "Error, no certificate configuration for domain {0} is defined.".format(
                domain
            )
        )
        raise RuntimeError("Hook execution failed.")

    # Following lines are written with the assumption that
    # the configuration file sanity has been checked before.
    certificate = certificates[0]
    profile_name = certificate["profile"]
    profiles = [
        value
        for key, value in config.get("profiles", {}).items()
        if key == profile_name
    ]

    return profile_name, profiles[0]


def _txt_challenge(
    profile_name: str,
    profile_content: Dict[str, Any],
    token: str,
    domain: str,
    action: str = "create",
):
    provider_name = profile_content["provider"]
    provider_options = profile_content.get("provider_options", {})

    if not provider_options:
        print(
            "No provider_options are defined for profile {0}, any call to the provider API is likely to fail.".format(
                profile_name
            )
        )

    lexicon_config = ConfigResolver()
    lexicon_config.with_dict(
        {
            "action": action,
            "domain": domain,
            "type": "TXT",
            "name": "_acme-challenge.{0}.".format(domain),
            "content": token,
            "provider_name": provider_name,
            provider_name: {key: value for key, value in provider_options.items()},
        }
    )

    Client(lexicon_config).execute()


def _pfx_export(cert_config: Dict[str, Any], lineage_path: str):
    pfx = cert_config.get("pfx", {})
    if pfx.get("export"):
        with open(os.path.join(lineage_path, "privkey.pem"), "rb") as f:
            key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, f.read())
        with open(os.path.join(lineage_path, "cert.pem"), "rb") as f:
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, f.read()
            )
        cacerts = [
            OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert.as_bytes()
            )
            for cert in pem.parse_file(os.path.join(lineage_path, "chain.pem"))
        ]

        p12 = OpenSSL.crypto.PKCS12()
        p12.set_privatekey(key)
        p12.set_certificate(cert)
        p12.set_ca_certificates(cacerts)

        with open(os.path.join(lineage_path, "cert.pfx"), "wb") as f:
            f.write(p12.export(pfx.get("passphrase")))


def _fix_permissions(certs_perms_config: Dict[str, str], lineage_path: str):
    archive_path = lineage_path.replace(os.path.sep + "live", os.path.sep + "archive")
    utils.fix_permissions(certs_perms_config, archive_path)
    utils.fix_permissions(certs_perms_config, lineage_path)


def _autorestart(cert_config: Dict[str, Any]):
    autorestart = cert_config.get("autorestart")
    if autorestart:
        if not os.path.exists("/var/run/docker.sock"):
            raise RuntimeError("Error, /var/run/docker.sock socket is missing.")

        containers = autorestart.get("containers", [])
        for container in containers:
            utils.execute(["docker", "restart", container])

        swarm_services = autorestart.get("swarm_services", [])
        for service in swarm_services:
            utils.execute(
                ["docker", "service", "update", "--detach=false", "--force", service]
            )


def _autocmd(cert_config: Dict[str, Any]):
    autocmd = cert_config.get("autocmd")
    if autocmd:
        if not os.path.exists("/var/run/docker.sock"):
            raise RuntimeError("Error, /var/run/docker.sock socket is missing.")

        for onecmd in autocmd:
            command = onecmd.get("cmd")

            containers = onecmd.get("containers", [])
            for container in containers:
                utils.execute(["docker", "exec", container, command])

            if onecmd.get("swarm_services"):
                print(
                    "Feature autocmd is not supported in Swarm mode and has been ignored."
                )


def _deploy_hook(profile_config: Dict[str, str]):
    deploy_hook = profile_config.get("deploy_hook")
    if deploy_hook:
        if os.name == "nt":
            subprocess.check_call(["powershell.exe", "-Command", deploy_hook])
        else:
            subprocess.check_call(deploy_hook, shell=True)


if __name__ == "__main__":
    main()
