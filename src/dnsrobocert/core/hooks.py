#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import logging
import os
import subprocess
import sys
import time
import traceback
from typing import Any, Dict, List

import coloredlogs
import OpenSSL
import pem
from dns import resolver
from lexicon.client import Client
from lexicon.config import ConfigResolver

from dnsrobocert.core import config, utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def main(args: List[str] = None) -> int:
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--type", choices=["auth", "cleanup", "deploy"], required=True
    )
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("-l", "--lineage", default="None", required=False)

    parsed_args = parser.parse_args(args)
    dnsrobocert_config = config.load(parsed_args.config)

    if not dnsrobocert_config:
        LOGGER.error(
            "Error occured while loading the configuration file, aborting the `{0}` hook.".format(
                parsed_args.type
            )
        )
        return 1

    try:
        globals()[parsed_args.type](dnsrobocert_config, parsed_args.lineage)
    except BaseException as e:
        LOGGER.error("Error while executing the `{0}` hook:".format(parsed_args.type))
        LOGGER.error(e)
        traceback.print_exc(file=sys.stderr)
        return 1

    return 0


def auth(dnsrobocert_config: Dict[str, Any], lineage: str):
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    _txt_challenge(profile, token, domain, action="create")

    sleep_time = profile.get("sleep_time", 30)
    max_checks = profile.get("max_checks", 0)
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

            validation_answers = None
            try:
                answers = resolver.query("_acme-challenge.{0}.".format(domain), "TXT")
                validation_answers = [
                    rdata
                    for rdata in answers
                    for txt_string in rdata.strings
                    if txt_string.decode("utf-8") == token
                ]
            except (resolver.NXDOMAIN, resolver.NoAnswer):
                # Will be handled below.
                pass

            if validation_answers:
                LOGGER.info(
                    "TXT _acme-challenge.{0} has the expected token value (try {1}/{2})".format(
                        domain, checks, max_checks
                    )
                )
                break

            LOGGER.info(
                "TXT _acme-challenge.{0} does not exist or does not have the expected token value (try {1}/{2})".format(
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


def cleanup(dnsrobocert_config: Dict[str, str], lineage: str):
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    _txt_challenge(profile, token, domain, action="delete")


def deploy(dnsrobocert_config: Dict[str, Any], _no_lineage: Any):
    lineage_path = os.environ["RENEWED_LINEAGE"]
    lineage = os.path.basename(lineage_path)
    certificate = config.get_certificate(dnsrobocert_config, lineage)

    _pfx_export(certificate, lineage_path)
    _fix_permissions(
        dnsrobocert_config.get("acme", {}).get("certs_permissions", {}), lineage_path
    )
    _autorestart(certificate)
    _autocmd(certificate)
    _deploy_hook(certificate)


def _txt_challenge(
    profile: Dict[str, Any], token: str, domain: str, action: str = "create",
):
    profile_name = profile["name"]
    provider_name = profile["provider"]
    provider_options = profile.get("provider_options", {})

    if not provider_options:
        print(
            "No provider_options are defined for profile {0}, any call to the provider API is likely to fail.".format(
                profile_name
            )
        )

    config_dict = {
        "action": action,
        "domain": domain,
        "type": "TXT",
        "name": "_acme-challenge.{0}.".format(domain),
        "content": token,
        "delegated": profile.get("delegated_subdomain"),
        "provider_name": provider_name,
        provider_name: provider_options,
    }

    ttl = profile.get("ttl")
    if ttl:
        config_dict["ttl"] = ttl

    lexicon_config = ConfigResolver()
    lexicon_config.with_dict(config_dict)

    Client(lexicon_config).execute()


def _pfx_export(certificate: Dict[str, Any], lineage_path: str):
    pfx = certificate.get("pfx", {})
    if pfx.get("export"):
        with open(os.path.join(lineage_path, "privkey.pem"), "rb") as f:
            key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, f.read())
        with open(os.path.join(lineage_path, "cert.pem"), "rb") as f:
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, f.read()
            )
        ca_certs = [
            OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert.as_bytes()
            )
            for cert in pem.parse_file(os.path.join(lineage_path, "chain.pem"))
        ]

        p12 = OpenSSL.crypto.PKCS12()
        p12.set_privatekey(key)
        p12.set_certificate(cert)
        p12.set_ca_certificates(ca_certs)

        with open(os.path.join(lineage_path, "cert.pfx"), "wb") as f:
            f.write(p12.export(pfx.get("passphrase")))


def _fix_permissions(certificate_permissions: Dict[str, str], lineage_path: str):
    archive_path = lineage_path.replace(os.path.sep + "live", os.path.sep + "archive")
    utils.fix_permissions(certificate_permissions, archive_path)
    utils.fix_permissions(certificate_permissions, lineage_path)


def _autorestart(certificate: Dict[str, Any]):
    autorestart = certificate.get("autorestart")
    if autorestart:
        if not os.path.exists("/var/run/docker.sock"):
            raise RuntimeError("Error, /var/run/docker.sock socket is missing.")

        for onerestart in autorestart:
            containers = onerestart.get("containers", [])
            for container in containers:
                utils.execute(["docker", "restart", container])

            swarm_services = onerestart.get("swarm_services", [])
            for service in swarm_services:
                utils.execute(
                    [
                        "docker",
                        "service",
                        "update",
                        "--detach=false",
                        "--force",
                        service,
                    ]
                )


def _autocmd(certificate: Dict[str, Any]):
    autocmd = certificate.get("autocmd")
    if autocmd:
        if not os.path.exists("/var/run/docker.sock"):
            raise RuntimeError("Error, /var/run/docker.sock socket is missing.")

        for onecmd in autocmd:
            command = onecmd.get("cmd")

            containers = onecmd.get("containers", [])
            for container in containers:
                utils.execute(["docker", "exec", container, command])


def _deploy_hook(certificate: Dict[str, Any]):
    deploy_hook = certificate.get("deploy_hook")
    if deploy_hook:
        if os.name == "nt":
            subprocess.check_call(["powershell.exe", "-Command", deploy_hook])
        else:
            subprocess.check_call(deploy_hook, shell=True)


if __name__ == "__main__":
    sys.exit(main())
