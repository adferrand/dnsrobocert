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
test1.sub.example.com test2.sub.example.com
"""
        )

    monkeypatch.setenv("LEXICON_PROVIDER", "ovh")
    monkeypatch.setenv("LEXICON_OVH_AUTH_APPLICATION_KEY", "KEY")
    monkeypatch.setenv("LEXICON_OPTIONS", "--delegated=sub.example.com")
    monkeypatch.setenv(
        "LEXICON_PROVIDER_OPTIONS",
        "--auth-entrypoint ovh-eu --auth-application-secret=SECRET",
    )
    monkeypatch.setenv("LETSENCRYPT_USER_MAIL", "john.doe@example.com")
    monkeypatch.setenv("LETSENCRYPT_STAGING", "true")

    with mock.patch(
        "dnsrobocert.core.legacy.LEGACY_CONFIGURATION_PATH",
        new=legacy_config_domain_file,
    ):
        legacy.migrate(config_path)

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
- domains:
  - test1.sub.example.com
  - test2.sub.example.com
  name: test1.sub.example.com
  profile: ovh
profiles:
- delegated_subdomain: sub.example.com
  name: ovh
  provider: ovh
  provider_options:
    auth_application_key: KEY
    auth_application_secret: SECRET
    auth_entrypoint: ovh-eu
"""
    )
