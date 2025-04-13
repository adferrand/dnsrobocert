#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import traceback
from typing import Any, cast

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    CertificateIssuerPrivateKeyTypes,
)
from cryptography.hazmat.primitives.serialization import pkcs12

from dnsrobocert.core import config, utils
from dnsrobocert.core.challenge import check_one_challenge, txt_challenge


def main(args: list[str] | None = None) -> int:
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
            f"Error occured while loading the configuration file, aborting the {parsed_args.type} hook.",
            file=sys.stderr,
        )
        return 1

    try:
        globals()[parsed_args.type](dnsrobocert_config, parsed_args.lineage)
    except BaseException as e:
        print(
            f"Error while executing the {parsed_args.type} hook:",
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

    return 0


def auth(dnsrobocert_config: dict[str, Any], lineage: str) -> None:
    certificate = config.get_certificate(dnsrobocert_config, lineage)
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    if certificate is None:
        raise RuntimeError(
            f"Error while executing the auth hook: certificate config for lineage {lineage} coud not be found."
        )

    if profile is None:
        raise RuntimeError(
            f"Error while executing the auth hook: profile for lineage {lineage} coud not be found."
        )

    print(f"Executing auth hook for domain {domain}, lineage {lineage}.")

    txt_challenge(certificate, profile, token, domain, action="create")

    remaining_challenges = int(os.environ.get("CERTBOT_REMAINING_CHALLENGES", "0"))
    if remaining_challenges != 0:
        print(
            f"Still {remaining_challenges} challenges to handle, skip checks until last challenge."
        )
        return

    all_domains_str = os.environ.get("CERTBOT_ALL_DOMAINS", "")
    all_domains = all_domains_str.split(",")
    challenges_to_check = [f"_acme-challenge.{domain}" for domain in all_domains]

    sleep_time = profile.get("sleep_time", 30)
    max_checks = profile.get("max_checks", 0)
    if max_checks:
        print(f"Challenges to check: {challenges_to_check}")
        checks = 0
        while True:
            checks = checks + 1
            if checks > max_checks:
                print(
                    f"All challenges were not propagated after the maximum tries of {max_checks}",
                    file=sys.stderr,
                )
                raise RuntimeError("Auth hook failed.")

            print(
                f"Wait {sleep_time} seconds before checking that all challenges have the expected value "
                f"(try {checks}/{max_checks})"
            )
            time.sleep(sleep_time)

            challenges_to_check = [
                challenge
                for challenge in challenges_to_check
                if not check_one_challenge(
                    challenge,
                    token if challenge == "_acme-challenge.{domain}" else None,
                )
            ]

            if not challenges_to_check:
                print(
                    f"All challenges have been propagated (try {checks}/{max_checks})."
                )
                break
    else:
        print(
            f"Wait {sleep_time} seconds to let all challenges be propagated: {challenges_to_check}"
        )
        time.sleep(sleep_time)


def cleanup(dnsrobocert_config: dict[str, str], lineage: str) -> None:
    certificate = config.get_certificate(dnsrobocert_config, lineage)
    profile = config.find_profile_for_lineage(dnsrobocert_config, lineage)
    domain = os.environ["CERTBOT_DOMAIN"]
    token = os.environ["CERTBOT_VALIDATION"]

    print(f"Executing cleanup hook for domain {domain}, lineage {lineage}.")

    txt_challenge(certificate, profile, token, domain, action="delete")


def deploy(dnsrobocert_config: dict[str, Any], _no_lineage: Any) -> None:
    lineage_path = os.environ["RENEWED_LINEAGE"]
    lineage = os.path.basename(lineage_path)
    certificate = config.get_certificate(dnsrobocert_config, lineage)

    _pfx_export(certificate, lineage_path, lineage)
    _fix_permissions(
        dnsrobocert_config.get("acme", {}).get("certs_permissions", {}), lineage_path
    )
    _autorestart(certificate)
    _autocmd(certificate)
    _deploy_hook(certificate)


def _pfx_export(certificate: dict[str, Any], lineage_path: str, lineage: str) -> None:
    pfx = certificate.get("pfx", {})
    if pfx.get("export"):
        with open(os.path.join(lineage_path, "privkey.pem"), "rb") as f:
            key = serialization.load_pem_private_key(f.read(), None)
        with open(os.path.join(lineage_path, "cert.pem"), "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        with open(os.path.join(lineage_path, "chain.pem"), "rb") as f:
            ca_certs = x509.load_pem_x509_certificates(f.read())

        passphrase: str = pfx.get("passphrase")
        p12 = pkcs12.serialize_key_and_certificates(
            lineage.encode("utf-8"),
            cast(
                CertificateIssuerPrivateKeyTypes, key
            ),  # By construction, Certbot will generate only RSA/ECDSA private keys.
            cert,
            ca_certs,
            (
                serialization.BestAvailableEncryption(passphrase.encode("utf-8"))
                if passphrase
                else serialization.NoEncryption()
            ),
        )

        with open(os.path.join(lineage_path, "cert.pfx"), "wb") as f:
            f.write(p12)


def _fix_permissions(
    certificate_permissions: dict[str, str], lineage_path: str
) -> None:
    archive_path = lineage_path.replace(os.path.sep + "live", os.path.sep + "archive")
    utils.fix_permissions(certificate_permissions, archive_path)
    utils.fix_permissions(certificate_permissions, lineage_path)


def _autorestart(certificate: dict[str, Any]) -> None:
    autorestart = certificate.get("autorestart")
    if autorestart:
        if not os.path.exists("/var/run/docker.sock") and not os.path.exists(
            "/run/podman/podman.sock"
        ):
            raise RuntimeError(
                "Error, /var/run/docker.sock and /run/podman/podman.sock sockets are missing."
            )

        if os.path.exists("/var/run/docker.sock"):
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

        if os.path.exists("/run/podman/podman.sock"):
            for onerestart in autorestart:
                containers = onerestart.get("podman_containers", [])
                for container in containers:
                    utils.execute(["podman", "--remote", "restart", container])


def _autocmd(certificate: dict[str, Any]) -> None:
    autocmd = certificate.get("autocmd")
    if autocmd:
        if not os.path.exists("/var/run/docker.sock"):
            raise RuntimeError("Error, /var/run/docker.sock socket is missing.")

        for onecmd in autocmd:
            command = onecmd.get("cmd")

            containers = onecmd.get("containers", [])
            for container in containers:
                if isinstance(command, list):
                    utils.execute(["docker", "exec", container, *command])
                else:
                    utils.execute(f"docker exec {container} {command}", shell=True)


def _deploy_hook(certificate: dict[str, Any]) -> None:
    deploy_hook = certificate.get("deploy_hook")
    env = os.environ.copy()
    env.update(
        {
            "DNSROBOCERT_CERTIFICATE_NAME": certificate.get("name", ""),
            "DNSROBOCERT_CERTIFICATE_PROFILE": certificate.get("profile", ""),
            "DNSROBOCERT_CERTIFICATE_DOMAINS": ",".join(certificate.get("domains", [])),
        }
    )
    if deploy_hook:
        if os.name == "nt":
            subprocess.check_call(["powershell.exe", "-Command", deploy_hook], env=env)
        else:
            subprocess.check_call(deploy_hook, shell=True, env=env)


if __name__ == "__main__":
    sys.exit(main())
