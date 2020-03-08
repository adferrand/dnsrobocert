import json
import os

import mock

from dnsrobocert.core import legacy


def test_legacy_migration(tmp_path, monkeypatch):
    config_path = tmp_path / "dnsrobocert" / "config.yml"
    legacy_config_domain_file = tmp_path / "old_config" / "domains.conf"
    generated_config_path = tmp_path / "dnsrobocert" / "config-generated.yml"
    os.mkdir(os.path.dirname(legacy_config_domain_file))

    with open(str(legacy_config_domain_file), "w") as f:
        f.write(
            """\
test.example.com test1.example.com
"""
        )

    monkeypatch.setenv("LEXICON_PROVIDER", "dummy")
    monkeypatch.setenv("LEXICON_DUMMY_AUTH_TOKEN", "TOKEN")
    monkeypatch.setenv("LETSENCRYPT_USER_MAIL", "john.doe@example.com")
    monkeypatch.setenv("LETSENCRYPT_STAGING", "true")

    with mock.patch(
        "dnsrobocert.core.legacy.LEGACY_CONFIGURATION_PATH",
        new=legacy_config_domain_file,
    ):
        dnsrobocert_config = legacy.migrate(config_path)

    assert os.path.exists(generated_config_path)
    with open(generated_config_path) as f:
        generated_data = f.read()
    assert (
        generated_data
        == """\
acme:
  email_account: john.doe@example.com
  staging: true
certificates:
  test.example.com:
    profile: dummy
    san:
    - test1.example.com
profiles:
  dummy:
    provider: dummy
    provider_options:
      auth_token: TOKEN
"""
    )
