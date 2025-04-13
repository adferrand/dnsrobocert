from __future__ import annotations

from typing import Any

import dns.exception
import dns.resolver
import tldextract
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
        canonical_challenge_name = str(dns.resolver.canonical_name(challenge_name))
        print(
            f"Canonical challenge name found for {challenge_name}: {canonical_challenge_name}"
        )
        challenge_name = canonical_challenge_name

        extracted = tldextract.extract(challenge_name)
        domain = ".".join([extracted.domain, extracted.suffix])

    config_dict = {
        "domain": domain,
        "resolve_zone_name": profile.get("dynamic_zone_resolution", True),
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
    try:
        answers = dns.resolver.resolve(challenge, "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        print(f"TXT {challenge} does not exist.")
        return False
    except dns.exception.Timeout as e:
        print(f"Timeout while trying to check TXT {challenge}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected exception while trying to check TXT {challenge}: {e}")
        return False
    else:
        print(f"TXT {challenge} exists.")

    if token:
        validation_answers = [
            rdata
            for rdata in answers
            for txt_string in rdata.strings  # type: ignore[attr-defined]
            if txt_string.decode("utf-8") == token
        ]

        if not validation_answers:
            print(f"TXT {challenge} does not have the expected token value.")
            return False

        print(f"TXT {challenge} has the expected token value.")

    return True
