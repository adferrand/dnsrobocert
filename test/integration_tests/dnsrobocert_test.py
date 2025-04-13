from __future__ import annotations

import contextlib
import json
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from unittest import skipIf
from unittest.mock import patch

import requests
import urllib3

from dnsrobocert.core import main

_PEBBLE_VERSION = "v2.6.0"
_ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_CHALLTESTSRV_PORT = 8000

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _fetch(workspace: str) -> tuple[str, str, str]:
    arch = "amd64"
    os_kind = platform.system().lower()
    if os_kind == "windows":
        suffix = ".exe"
    elif os_kind == "linux":
        suffix = ""
    else:
        raise RuntimeError("Unsupported platform: {0}".format(platform.system()))

    pebble_path = _fetch_asset("pebble", os_kind, arch, suffix)
    challtestsrv_path = _fetch_asset("pebble-challtestsrv", os_kind, arch, suffix)
    pebble_config_path = _build_pebble_config(workspace)
    return pebble_path, challtestsrv_path, pebble_config_path


def _fetch_asset(asset: str, os_kind: str, arch: str, suffix: str) -> str:
    asset_path = os.path.join(
        _ASSETS_PATH, f"{asset}-{_PEBBLE_VERSION}-{os_kind}-{arch}{suffix}"
    )
    if not os.path.exists(asset_path):
        with tempfile.TemporaryDirectory() as workdir:
            archive_path = os.path.join(workdir, "archive.tar.gz")
            asset_url = f"https://github.com/letsencrypt/pebble/releases/download/{_PEBBLE_VERSION}/{asset}-{os_kind}-{arch}.tar.gz"
            response = requests.get(asset_url)
            response.raise_for_status()
            with open(archive_path, "wb") as file_h:
                file_h.write(response.content)

            with tarfile.open(archive_path) as archive:
                archive.extractall(workdir)
                shutil.copyfile(
                    os.path.join(
                        workdir,
                        f"{asset}-{os_kind}-{arch}",
                        os_kind,
                        arch,
                        f"{asset}{suffix}",
                    ),
                    asset_path,
                )

    os.chmod(asset_path, os.stat(asset_path).st_mode | stat.S_IEXEC)

    return asset_path


def _build_pebble_config(workspace: str) -> str:
    config_path = os.path.join(workspace, "pebble-config.json")
    with open(config_path, "w") as file_h:
        file_h.write(
            json.dumps(
                {
                    "pebble": {
                        "listenAddress": "0.0.0.0:14000",
                        "managementListenAddress": "0.0.0.0:15000",
                        "certificate": os.path.join(_ASSETS_PATH, "cert.pem"),
                        "privateKey": os.path.join(_ASSETS_PATH, "key.pem"),
                        "httpPort": 80,
                        "tlsPort": 443,
                    },
                }
            )
        )

    return config_path


def _check_until_timeout(url: str, attempts: int = 30) -> None:
    for _ in range(attempts):
        time.sleep(1)
        try:
            if requests.get(url, verify=False).status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass

    raise ValueError(f"Error, url did not respond after {attempts} attempts: {url}")


@contextlib.contextmanager
def _start_pebble(tmp_path: Path) -> Iterator[None]:
    workspace = tmp_path / "workspace"
    os.mkdir(str(workspace))

    pebble_path, challtestsrv_path, pebble_config_path = _fetch(str(workspace))

    environ = os.environ.copy()
    environ["PEBBLE_VA_NOSLEEP"] = "1"
    environ["PEBBLE_WFE_NONCEREJECT"] = "0"
    environ["PEBBLE_AUTHZREUSE"] = "100"
    environ["PEBBLE_VA_ALWAYS_VALID"] = "1"

    pebble_process: subprocess.Popen | None = None
    challtestsrv_process: subprocess.Popen | None = None

    try:
        pebble_process = subprocess.Popen(
            [
                pebble_path,
                "-config",
                pebble_config_path,
                "-dnsserver",
                "127.0.0.1:8053",
            ],
            env=environ,
        )
        challtestsrv_process = subprocess.Popen(
            [
                challtestsrv_path,
                "-management",
                ":{0}".format(_CHALLTESTSRV_PORT),
                "-defaultIPv6",
                '""',
                "-defaultIPv4",
                "127.0.0.1",
                "-http01",
                '""',
                "-tlsalpn01",
                '""',
                "-https01",
                '""',
            ],
            env=environ,
        )

        _check_until_timeout("https://127.0.0.1:14000/dir")

        yield
    finally:
        if pebble_process:
            pebble_process.terminate()
        if challtestsrv_process:
            challtestsrv_process.terminate()


@skipIf(
    platform.system() == "Darwin",
    reason="Integration tests are not supported on Mac OS X.",
)
def test_it(tmp_path: Path) -> None:
    with _start_pebble(tmp_path):
        directory_path = tmp_path / "letsencrypt"
        os.mkdir(directory_path)

        config_path = tmp_path / "config.yml"
        with open(str(config_path), "w") as f:
            f.write(
                """\
draft: false
acme:
  email_account: john.doe@example.net
  directory_url: https://127.0.0.1:14000/dir
profiles:
- name: dummy
  provider: dummy
  provider_options:
    auth_token: TOKEN
certificates:
- domains:
  - test1.example.net
  - test2.example.net
  profile: dummy
  follow_cnames: true
  reuse_key: true
  key_type: ecdsa
  pfx:
    export: true
    passphrase: test
"""
            )

        with patch.object(main._Daemon, "do_shutdown") as shutdown:
            shutdown.side_effect = [False, True]
            with patch(
                "dnsrobocert.core.certbot._DEFAULT_FLAGS", ["-n", "--no-verify-ssl"]
            ):
                main.main(["-c", str(config_path), "-d", str(directory_path)])

        assert set(os.listdir(directory_path / "live" / "test1.example.net")) == {
            "privkey.pem",
            "cert.pfx",
            "fullchain.pem",
            "README",
            "cert.pem",
            "chain.pem",
        }
