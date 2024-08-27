import os
from pathlib import Path
from unittest import mock

from pytest import MonkeyPatch

from dnsrobocert.core import config, legacy


def test_legacy_migration(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "dnsrobocert" / "config.yml"
    legacy_config_domain_file = tmp_path / "old_config" / "domains.conf"
    generated_config_path = tmp_path / "dnsrobocert" / "config-generated.yml"
    os.mkdir(os.path.dirname(legacy_config_domain_file))

    with open(
        os.path.join(os.path.dirname(legacy_config_domain_file), "lexicon.yml"), "w"
    ) as f:
        f.write(
            """\
ovh:
  auth_application_secret: SECRET
  additional_config: ADDITIONAL
"""
        )

    with open(
        os.path.join(os.path.dirname(legacy_config_domain_file), "lexicon_ovh.yml"), "w"
    ) as f:
        f.write(
            """\
auth_consumer_key: CONSUMER_KEY
"""
        )

    with open(str(legacy_config_domain_file), "w") as f:
        f.write(
            """\
test1.sub.example.com test2.sub.example.com autorestart-containers=container1,container2 autocmd-containers=container3:cmd3 arg3,container4:cmd4 arg4a arg4b
*.sub.example.com sub.example.com
"""
        )

    monkeypatch.setenv("LEXICON_PROVIDER", "ovh")
    monkeypatch.setenv("LEXICON_OVH_AUTH_APPLICATION_KEY", "KEY")
    monkeypatch.setenv(
        "LEXICON_PROVIDER_OPTIONS",
        "--auth-entrypoint ovh-eu --auth-application-secret=SECRET-OVERRIDE",
    )
    monkeypatch.setenv("LEXICON_SLEEP_TIME", "60")
    monkeypatch.setenv("LEXICON_MAX_CHECKS", "3")
    monkeypatch.setenv("LEXICON_TTL", "42")
    monkeypatch.setenv("LETSENCRYPT_USER_MAIL", "john.doe@example.com")
    monkeypatch.setenv("LETSENCRYPT_STAGING", "true")
    monkeypatch.setenv("LETSENCRYPT_ACME_V1", "true")
    monkeypatch.setenv("CERTS_DIRS_MODE", "0755")
    monkeypatch.setenv("CERTS_FILES_MODE", "0644")
    monkeypatch.setenv("CERTS_USER_OWNER", "nobody")
    monkeypatch.setenv("CERTS_GROUP_OWNER", "nogroup")
    monkeypatch.setenv("PFX_EXPORT", "true")
    monkeypatch.setenv("PFX_EXPORT_PASSPHRASE", "PASSPHRASE")
    monkeypatch.setenv("DEPLOY_HOOK", "./deploy.sh")

    with mock.patch(
        "dnsrobocert.core.legacy.LEGACY_CONFIGURATION_PATH",
        new=legacy_config_domain_file,
    ):
        legacy.migrate(config_path)

    assert config.load(generated_config_path)
    with open(generated_config_path) as f:
        generated_data = f.read()

    assert (
        generated_data
        == """\
acme:
  api_version: 1
  certs_permissions:
    dirs_mode: 493
    files_mode: 420
    group: nogroup
    user: nobody
  email_account: john.doe@example.com
  staging: true
certificates:
- autocmd:
  - cmd: cmd3 arg3
    containers:
    - container3
  - cmd: cmd4 arg4a arg4b
    containers:
    - container4
  autorestart:
  - containers:
    - container1
    - container2
  deploy_hook: ./deploy.sh
  domains:
  - test1.sub.example.com
  - test2.sub.example.com
  name: test1.sub.example.com
  pfx:
    export: true
    passphrase: PASSPHRASE
  profile: ovh
- deploy_hook: ./deploy.sh
  domains:
  - '*.sub.example.com'
  - sub.example.com
  name: sub.example.com
  pfx:
    export: true
    passphrase: PASSPHRASE
  profile: ovh
profiles:
- max_checks: 3
  name: ovh
  provider: ovh
  provider_options:
    additional_config: ADDITIONAL
    auth_application_key: KEY
    auth_application_secret: SECRET-OVERRIDE
    auth_consumer_key: CONSUMER_KEY
    auth_entrypoint: ovh-eu
  sleep_time: 60
  ttl: 42
"""
    )
