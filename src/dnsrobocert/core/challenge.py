from __future__ import annotations

from typing import Any

import tldextract
from dns.exception import Timeout
from dns.rdatatype import RdataType
from dns.resolver import NXDOMAIN, NoAnswer, get_default_resolver
from lexicon.client import Client
from lexicon.config import ConfigResolver


def txt_challenge(
    certificate: dict[str, Any],
    profile: dict[str, Any],
    token: str,
    domain: str,
    action: str = "create",
) -> None:
    profile_name = profile["name"]
    provider_name = profile["provider"]
    provider_options = profile.get("provider_options", {})

    if not provider_options:
        print(
            f"No provider_options are defined for profile {profile_name}, "
            "any call to the provider API is likely to fail."
        )

    challenge_name = f"_acme-challenge.{domain}."
    if certificate.get("follow_cnames"):
        print(f"Trying to resolve the canonical challenge name for {challenge_name}")
        canonical_challenge_name = resolve_canonical_challenge_name(challenge_name)
        print(
            f"Canonical challenge name found for {challenge_name}: {canonical_challenge_name}"
        )
        challenge_name = canonical_challenge_name

        extracted = tldextract.extract(challenge_name)
        domain = ".".join([extracted.domain, extracted.suffix])

    config_dict = {
        "domain": domain,
        "delegated": profile.get("delegated_subdomain"),
        "provider_name": provider_name,
        provider_name: provider_options,
    }

    ttl = profile.get("ttl")
    if ttl:
        config_dict["ttl"] = ttl

    with Client(ConfigResolver().with_dict(config_dict)) as operations:
        if action == "create":
            operations.create_record(rtype="TXT", name=challenge_name, content=token)
        elif action == "delete":
            operations.delete_record(rtype="TXT", name=challenge_name, content=token)


def check_one_challenge(challenge: str, token: str | None = None) -> bool:
    resolver = get_default_resolver()

    try:
        answers = resolver.query(challenge, "TXT")
    except (NXDOMAIN, NoAnswer):
        print(f"TXT {challenge} does not exist.")
        return False
    except Timeout as e:
        print(f"Timeout while trying to check TXT {challenge}: {e}")
        return False
    else:
        print(f"TXT {challenge} exists.")

    if token:
        validation_answers = [
            rdata
            for rdata in answers
            for txt_string in rdata.strings
            if txt_string.decode("utf-8") == token
        ]

        if not validation_answers:
            print(f"TXT {challenge} does not have the expected token value.")
            return False

        print(f"TXT {challenge} has the expected token value.")

    return True


def resolve_canonical_challenge_name(name: str) -> str:
    resolver = get_default_resolver()
    current_name = name
    visited = [current_name]

    while True:
        try:
            answer = resolver.resolve(current_name, rdtype=RdataType.CNAME)
            current_name = str(answer[0].target)
            if current_name in visited:
                resolution_map = " -> ".join([*visited, current_name])
                raise ValueError(
                    f"Error, CNAME resolution for {current_name} ended in an infinite loop!\n"
                    f"{resolution_map}"
                )
            visited.append(current_name)
        except (NXDOMAIN, NoAnswer):
            # No more CNAME in the chain, we have the final canonical_name
            return current_name
