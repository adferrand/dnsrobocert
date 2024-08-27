import os
from pathlib import Path

import pytest

from dnsrobocert.core import config


def test_good_config_minimal(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
"""
        )

    parsed = config.load(str(config_path))
    assert parsed


def test_bad_config_wrong_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
wrong_property: bad
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_non_existent_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
profiles:
- name: one
  provider: one
certificates:
- domains: [test.example.com]
  profile: two
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_wrong_posix_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
acme:
  certs_permissions:
    files_mode: 9999
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_duplicated_cert_name(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
profiles:
- name: one
  provider: one
certificates:
- domains: [test.example.com]
  profile: one
- name: test.example.com
  domains: [test1.example.com, test2.example.com]
  profile: one
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_wildcard_lineage() -> None:
    certificate = {"domains": ["*.example.com", "example.com"], "profile": "dummy"}

    assert config.get_lineage(certificate) == "example.com"


def test_environment_variable_injection(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: ${DRAFT_VALUE}
acme:
  certs_root_path: $${NOT_PARSED}
profiles:
- name: one
  provider: ${PROVIDER}
certificates:
- name: test.example.com
  domains: [test1.example.com, test2.example.com, '${ADDITIONAL_CERT}']
  profile: one
"""
        )

    environ = os.environ.copy()
    try:
        os.environ.update(
            {
                "DRAFT_VALUE": "true",
                "PROVIDER": "one",
                "ADDITIONAL_CERT": "test3.example.com",
            }
        )
        parsed = config.load(str(config_path))
    finally:
        os.environ.clear()
        os.environ.update(environ)

    assert parsed["draft"] is True
    assert parsed["acme"]["certs_root_path"] == "${NOT_PARSED}"
    assert parsed["profiles"][0]["provider"] == "one"
    assert "test3.example.com" in parsed["certificates"][0]["domains"]

    with pytest.raises(ValueError) as raised:
        config.load(str(config_path))

    assert (
        str(raised.value)
        == "Error while parsing config: environment variable DRAFT_VALUE does not exist."
    )
