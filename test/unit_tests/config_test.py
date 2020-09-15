import os

import pytest

from dnsrobocert.core import config


def test_good_config_minimal(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
"""
        )

    parsed = config.load(str(config_path))
    assert parsed


def test_bad_config_wrong_schema(tmp_path):
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


def test_bad_config_non_existent_profile(tmp_path):
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


def test_bad_config_wrong_posix_mode(tmp_path):
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


def test_bad_config_duplicated_cert_name(tmp_path):
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


def test_wildcard_lineage():
    certificate = {"domains": ["*.example.com", "example.com"], "profile": "dummy"}

    assert config.get_lineage(certificate) == "example.com"


def test_environment_variable_injection(tmp_path):
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


def test_extract_config_from_drc_env(monkeypatch, caplog):
    # Valid values
    monkeypatch.setenv("DRC__ACME__EMAIL_ACCOUNT", "my.email@example.net")
    monkeypatch.setenv("DRC__ACME__DIRECTORY_URL", "http://example.net/directory")
    monkeypatch.setenv("DRC__PROFILES__0__NAME", "my_profile1")
    monkeypatch.setenv("DRC__PROFILES__0__PROVIDER", "digitalocean")
    monkeypatch.setenv("DRC__PROFILES__0__PROVIDER_OPTIONS__AUTH_TOKEN", "TOKEN")

    # Invalid values
    monkeypatch.setenv("DRC__UNKNOWN", "dummy")
    monkeypatch.setenv("DRC__ACME__API_VERSION", "notanumber")
    monkeypatch.setenv("DRC__PROFILES__NOTANUMBER__NAME", "dummy")
    monkeypatch.setenv("DRC__PROFILES__0__NAME__ISALEAF", "dummy")

    extracted_config = config.extract_config_from_drc_env()
    assert extracted_config["acme"]["email_account"] == "my.email@example.net"
    assert extracted_config["acme"]["directory_url"] == "http://example.net/directory"
    assert extracted_config["profiles"][0]["name"] == "my_profile1"
    assert extracted_config["profiles"][0]["provider"] == "digitalocean"
    assert extracted_config["profiles"][0]["provider_options"]["auth_token"] == "TOKEN"

    warnings = [record.message for record in caplog.records]
    assert "Environment variable DRC__ACME__API_VERSION is invalid: invalid literal for int() with base 10: 'notanumber'." in warnings
    assert "Environment variable DRC__PROFILES__0__NAME__ISALEAF is invalid: variable name should finish with __NAME." in warnings
    assert "Environment variable DRC__PROFILES__NOTANUMBER__NAME is invalid: expected a number instead of __NOTANUMBER." in warnings
    assert "Environment variable DRC__UNKNOWN is invalid: variable name should not contain __UNKNOWN." in warnings


def test_merge_config_with_drc_envs(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yml"

    # With config only
    with open(str(config_path), "w") as f:
        f.write(
            """\
    draft: true
    acme:
      api_version: 2
    """
        )

    parsed = config.load(str(config_path), merge_drc_envs=True)
    assert parsed["draft"] is True
    assert parsed["acme"]["api_version"] == 2
    assert "email_account" not in parsed["acme"]

    # With config + drc env
    monkeypatch.setenv("DRC__ACME__EMAIL_ACCOUNT", "my.email@example.net")

    parsed = config.load(str(config_path), merge_drc_envs=True)
    assert parsed["draft"] is True
    assert parsed["acme"]["api_version"] == 2
    assert parsed["acme"]["email_account"] == "my.email@example.net"

    # With drc env only
    os.remove(config_path)

    parsed = config.load(str(config_path), merge_drc_envs=True)
    assert "draft" not in parsed
    assert parsed["acme"]["email_account"] == "my.email@example.net"

    # Check field priority order (config file takes precedence)
    with open(str(config_path), "w") as f:
        f.write(
            """\
    acme:
      email_account: another.email@example.net
    """
        )

    parsed = config.load(str(config_path), merge_drc_envs=True)
    assert parsed["acme"]["email_account"] == "another.email@example.net"
