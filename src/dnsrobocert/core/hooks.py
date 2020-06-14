#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import os
import subprocess
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

import OpenSSL
import pem
from dns import resolver
from lexicon.client import Client
from lexicon.config import ConfigResolver

from dnsrobocert.core import config, utils


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
        print(
            "Error occured while loading the configuration file, aborting the `{0}` hook.".format(
                parsed_args.type
            ),
            file=sys.stderr,
        )
        return 1

    try:
        globals()[parsed_args.type](dnsrobocert_config, parsed_args.lineage)
    except BaseException as e:
        print(
            "Error while executing the `{0}` hook:".format(parsed_args.type),
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

    return 0


def auth(dnsrobocert_config: Dict[str, Any], lineage: str):
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    print("Executing auth hook for domain {0}, lineage {1}.".format(domain, lineage))

    _txt_challenge(profile, token, domain, action="create")

    remaining_challenges = int(os.environ.get("CERTBOT_REMAINING_CHALLENGES", "0"))
    if remaining_challenges != 0:
        print(
            "Still {0} challenges to handle, skip checks until last challenge.".format(
                remaining_challenges
            )
        )
        return

    all_domains_str = os.environ.get("CERTBOT_ALL_DOMAINS", "")
    all_domains = all_domains_str.split(",")
    challenges_to_check = [
        "_acme-challenge.{0}".format(domain) for domain in all_domains
    ]

    sleep_time = profile.get("sleep_time", 30)
    max_checks = profile.get("max_checks", 0)
    if max_checks:
        print("Challenges to check: {0}".format(challenges_to_check))
        checks = 0
        while True:
            checks = checks + 1
            if checks > max_checks:
                print(
                    "All challenges were not propagated after the maximum tries of {0}".format(
                        max_checks
                    ),
                    file=sys.stderr,
                )
                raise RuntimeError("Auth hook failed.")

            print(
                "Wait {0} seconds before checking that all challenges have the expected value "
                "(try {1}/{2})".format(sleep_time, checks, max_checks)
            )
            time.sleep(sleep_time)

            challenges_to_check = [
                challenge
                for challenge in challenges_to_check
                if not _check_one_challenge(
                    challenge,
                    token
                    if challenge == "_acme-challenge.{0}".format(domain)
                    else None,
                )
            ]

            if not challenges_to_check:
                print(
                    "All challenges have been propagated (try {0}/{1}).".format(
                        checks, max_checks
                    )
                )
                break
    else:
        print(
            "Wait {0} seconds to let all challenges be propagated: {1}".format(
                sleep_time, challenges_to_check
            )
        )
        time.sleep(sleep_time)


def _check_one_challenge(challenge: str, token: Optional[str]) -> bool:
    try:
        answers = resolver.query(challenge, "TXT")
    except (resolver.NXDOMAIN, resolver.NoAnswer):
        print("TXT {0} does not exist.".format(challenge))
        return False
    else:
        print("TXT {0} exists.".format(challenge))

    if token:
        validation_answers = [
            rdata
            for rdata in answers
            for txt_string in rdata.strings
            if txt_string.decode("utf-8") == token
        ]

        if not validation_answers:
            print("TXT {0} does not have the expected token value.".format(challenge))
            return False

        print("TXT {0} has the expected token value.")

    return True


def cleanup(dnsrobocert_config: Dict[str, str], lineage: str):
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    print("Executing cleanup hook for domain {0}, lineage {1}.".format(domain, lineage))

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
