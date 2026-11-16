from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
import pytest

from dnsrobocert.core import challenge


def _answers(*values: str) -> list[Any]:
    return [MagicMock(strings=[value.encode("utf-8")]) for value in values]


@pytest.mark.parametrize(
    "error",
    [
        dns.resolver.NXDOMAIN(),
        dns.resolver.NoAnswer(),
        dns.exception.Timeout(),
        RuntimeError("boom"),
    ],
)
def test_check_one_challenge_resolution_errors(error: Exception) -> None:
    with patch("dns.resolver.resolve", side_effect=error):
        assert challenge.check_one_challenge("_acme-challenge.example.com") is False


def test_check_one_challenge_without_token() -> None:
    with patch("dns.resolver.resolve", return_value=_answers("anything")):
        assert challenge.check_one_challenge("_acme-challenge.example.com") is True


def test_check_one_challenge_token_found() -> None:
    answers = _answers("other", "expected")
    with patch("dns.resolver.resolve", return_value=answers):
        assert challenge.check_one_challenge("_acme-challenge.example.com", "expected")


def test_check_one_challenge_token_mismatch() -> None:
    with patch("dns.resolver.resolve", return_value=_answers("other")):
        assert not challenge.check_one_challenge(
            "_acme-challenge.example.com", "expected"
        )


def _lexicon_config(client_mock: MagicMock) -> Any:
    return client_mock.call_args[0][0]


@pytest.mark.parametrize("action", ["create", "delete"])
def test_txt_challenge_actions(action: str) -> None:
    profile = {
        "name": "p",
        "provider": "dummy",
        "provider_options": {"auth_token": "secret"},
        "ttl": 60,
    }

    with patch("dnsrobocert.core.challenge.Client") as client:
        challenge.txt_challenge({}, profile, "token", "example.com", action=action)

    operations = client.return_value.__enter__.return_value
    expected = getattr(operations, f"{action}_record")
    other = operations.delete_record if action == "create" else operations.create_record
    expected.assert_called_once_with(
        rtype="TXT", name="_acme-challenge.example.com.", content="token"
    )
    other.assert_not_called()

    config = _lexicon_config(client)
    assert config.resolve("lexicon:domain") == "example.com"
    assert config.resolve("lexicon:provider_name") == "dummy"
    assert config.resolve("lexicon:ttl") == 60
    assert config.resolve("lexicon:dummy:auth_token") == "secret"


def test_txt_challenge_follow_cnames() -> None:
    profile = {"name": "p", "provider": "dummy"}

    with (
        patch("dnsrobocert.core.challenge.Client") as client,
        patch(
            "dns.resolver.canonical_name",
            return_value="_acme-challenge.delegated.example.net.",
        ),
    ):
        challenge.txt_challenge(
            {"follow_cnames": True}, profile, "token", "example.com"
        )

    operations = client.return_value.__enter__.return_value
    operations.create_record.assert_called_once_with(
        rtype="TXT", name="_acme-challenge.delegated.example.net.", content="token"
    )
    assert _lexicon_config(client).resolve("lexicon:domain") == "example.net"
