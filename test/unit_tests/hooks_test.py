from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from dnsrobocert.core import config, hooks

try:
    POSIX_MODE = True
    import grp
    import pwd
except ImportError:
    POSIX_MODE = False


LINEAGE = "test.example.com"


@pytest.fixture(autouse=True)
def fake_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[dict[str, Path]]:
    live_path = tmp_path / "live" / LINEAGE
    archive_path = tmp_path / "archive" / LINEAGE
    os.makedirs(str(tmp_path / "live"))
    os.makedirs(str(archive_path))
    os.symlink(str(archive_path), str(live_path), target_is_directory=True)

    monkeypatch.setenv("CERTBOT_VALIDATION", "VALIDATION")
    monkeypatch.setenv("CERTBOT_DOMAIN", LINEAGE)
    monkeypatch.setenv("RENEWED_LINEAGE", str(live_path))

    yield {
        "live": live_path,
        "archive": archive_path,
    }


@pytest.fixture
def fake_config(tmp_path: Path) -> Iterator[Path]:
    config_path = tmp_path / "config.yml"
    config_data = f"""\
acme:
  certs_permissions:
    files_mode: "0666"
    dirs_mode: 0777
    user: nobody
    group: nogroup
profiles:
- name: dummy-profile
  provider: dummy
  provider_options:
    auth_token: TOKEN
  sleep_time: 0.1
  ttl: 42
certificates:
- name: {LINEAGE}
  domains:
  - {LINEAGE}
  profile: dummy-profile
  pfx:
    export: true
  autocmd:
  - cmd: [echo, "Hello World!"]
    containers: [foo, bar]
  - cmd: echo test
    containers: [dummy]
  autorestart:
  - containers: [container1, container2]
  - swarm_services: [service1, service2]
"""
    config_path.write_text(config_data)
    yield config_path


@patch("dnsrobocert.core.challenge.Client")
def test_auth_cli(client: MagicMock, fake_config: Path) -> None:
    operations = MagicMock()
    client.return_value.__enter__.return_value = operations

    hooks.main(["-t", "auth", "-c", str(fake_config), "-l", LINEAGE])

    assert len(client.call_args[0]) == 1
    resolver = client.call_args[0][0]

    assert resolver.resolve("lexicon:domain") == LINEAGE
    assert resolver.resolve("lexicon:provider_name") == "dummy"
    assert resolver.resolve("lexicon:ttl") == 42
    assert resolver.resolve("lexicon:dummy:auth_token") == "TOKEN"

    operations.create_record.assert_called_with(
        rtype="TXT", name=f"_acme-challenge.{LINEAGE}.", content="VALIDATION"
    )


@patch("dnsrobocert.core.challenge.Client")
def test_cleanup_cli(client: MagicMock, fake_config: Path) -> None:
    operations = MagicMock()
    client.return_value.__enter__.return_value = operations

    hooks.main(["-t", "cleanup", "-c", str(fake_config), "-l", LINEAGE])

    assert len(client.call_args[0]) == 1
    resolver = client.call_args[0][0]

    assert resolver.resolve("lexicon:domain") == LINEAGE
    assert resolver.resolve("lexicon:provider_name") == "dummy"
    assert resolver.resolve("lexicon:dummy:auth_token") == "TOKEN"

    operations.delete_record.assert_called_with(
        rtype="TXT", name=f"_acme-challenge.{LINEAGE}.", content="VALIDATION"
    )


@patch("dnsrobocert.core.hooks.deploy")
def test_deploy_cli(deploy: MagicMock, fake_config: Path) -> None:
    hooks.main(["-t", "deploy", "-c", str(fake_config), "-l", LINEAGE])
    deploy.assert_called_with(config.load(fake_config), LINEAGE)


@patch("dnsrobocert.core.hooks._fix_permissions")
@patch("dnsrobocert.core.hooks._autocmd")
@patch("dnsrobocert.core.hooks._autorestart")
def test_pfx(
    _autorestart: MagicMock,
    _autocmd: MagicMock,
    _fix_permissions: MagicMock,
    fake_env: dict[str, Path],
    fake_config: Path,
) -> None:
    archive_path = fake_env["archive"]
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    with open(archive_path / "privkey.pem", "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "example.com")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=10))
        .sign(key, hashes.SHA256(), default_backend())
    )

    with open(archive_path / "cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(archive_path / "chain.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    hooks.deploy(config.load(fake_config), LINEAGE)

    assert os.path.exists(archive_path / "cert.pfx")
    assert os.stat(archive_path / "cert.pfx").st_size != 0


@patch("dnsrobocert.core.hooks._fix_permissions")
@patch("dnsrobocert.core.hooks._pfx_export")
@patch("dnsrobocert.core.hooks._autorestart")
@patch("dnsrobocert.core.hooks.os.path.exists")
@patch("dnsrobocert.core.hooks.utils.execute")
def test_autocmd(
    execute: MagicMock,
    _exists: MagicMock,
    _autorestart: MagicMock,
    _pfx_export: MagicMock,
    _fix_permissions: MagicMock,
    fake_config: Path,
) -> None:
    hooks.deploy(config.load(fake_config), LINEAGE)

    call_foo = call(["docker", "exec", "foo", "echo", "Hello World!"])
    call_bar = call(["docker", "exec", "bar", "echo", "Hello World!"])
    call_dummy = call("docker exec dummy echo test", shell=True)
    execute.assert_has_calls([call_foo, call_bar, call_dummy])


@patch("dnsrobocert.core.hooks._fix_permissions")
@patch("dnsrobocert.core.hooks._pfx_export")
@patch("dnsrobocert.core.hooks._autocmd")
@patch("dnsrobocert.core.hooks.os.path.exists")
@patch("dnsrobocert.core.hooks.utils.execute")
def test_autorestart(
    execute: MagicMock,
    _exists: MagicMock,
    _autocmd: MagicMock,
    _pfx_export: MagicMock,
    _fix_permissions: MagicMock,
    fake_config: Path,
) -> None:
    hooks.deploy(config.load(fake_config), LINEAGE)

    call_container1 = call(["docker", "restart", "container1"])
    call_container2 = call(["docker", "restart", "container2"])
    call_service1 = call(
        ["docker", "service", "update", "--detach=false", "--force", "service1"]
    )
    call_service2 = call(
        ["docker", "service", "update", "--detach=false", "--force", "service2"]
    )
    execute.assert_has_calls(
        [call_container1, call_container2, call_service1, call_service2]
    )


@patch("dnsrobocert.core.hooks._pfx_export")
@patch("dnsrobocert.core.hooks._autocmd")
@patch("dnsrobocert.core.hooks._autorestart")
def test_fix_permissions(
    _autorestart: MagicMock,
    _autocmd: MagicMock,
    _pfx_export: MagicMock,
    fake_config: dict[str, str],
    fake_env: dict[str, Path],
) -> None:
    archive_path = str(fake_env["archive"])
    live_path = str(fake_env["live"])

    probe_file = os.path.join(archive_path, "dummy.txt")
    probe_dir = os.path.join(archive_path, "dummy_dir")

    probe_live_file = os.path.join(live_path, "dummy.txt")
    probe_live_dir = os.path.join(live_path, "dummy_dir")

    open(probe_file, "w").close()
    os.mkdir(probe_dir)

    with _mock_os_chown() as chown:
        hooks.deploy(config.load(fake_config), LINEAGE)

        assert os.stat(probe_file).st_mode & 0o777 == 0o666
        assert os.stat(probe_dir).st_mode & 0o777 == 0o777
        assert os.stat(archive_path).st_mode & 0o777 == 0o777

        if POSIX_MODE:
            uid = pwd.getpwnam("nobody")[2]
            gid = grp.getgrnam("nogroup")[2]

            calls = [
                call(archive_path, uid, gid),
                call(probe_file, uid, gid),
                call(probe_dir, uid, gid),
                call(live_path, uid, gid),
                call(probe_live_file, uid, gid),
                call(probe_live_dir, uid, gid),
            ]

            if chown:
                assert chown.call_args_list == calls


@contextlib.contextmanager
def _mock_os_chown() -> Iterator[MagicMock | AsyncMock | None]:
    if POSIX_MODE:
        with patch("dnsrobocert.core.utils.os.chown") as chown:
            yield chown
    else:
        yield None
