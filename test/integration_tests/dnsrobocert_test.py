import json
import os
import stat
import subprocess
import time
from typing import Optional
from unittest import skipIf
from unittest.mock import patch
import platform

import pytest
import requests
import urllib3

from dnsrobocert.core import main

_PEBBLE_VERSION = "v2.3.0"
_ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_CHALLTESTSRV_PORT = 8000

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch(workspace):
    if platform.system() == "Windows":
        suffix = "windows-amd64.exe"
    elif platform.system() == "Linux":
        suffix = "linux-amd64"
    else:
        raise RuntimeError("Unsupported platform: {0}".format(platform.system()))

    pebble_path = _fetch_asset("pebble", suffix)
    challtestsrv_path = _fetch_asset("pebble-challtestsrv", suffix)
    pebble_config_path = _build_pebble_config(workspace)

    return pebble_path, challtestsrv_path, pebble_config_path


def _fetch_asset(asset, suffix):
    asset_path = os.path.join(
        _ASSETS_PATH, "{0}_{1}_{2}".format(asset, _PEBBLE_VERSION, suffix)
    )
    if not os.path.exists(asset_path):
        asset_url = "https://github.com/letsencrypt/pebble/releases/download/{0}/{1}_{2}".format(
            _PEBBLE_VERSION, asset, suffix
        )
        response = requests.get(asset_url)
        response.raise_for_status()
        with open(asset_path, "wb") as file_h:
            file_h.write(response.content)
    os.chmod(asset_path, os.stat(asset_path).st_mode | stat.S_IEXEC)

    return asset_path


def _build_pebble_config(workspace):
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


def _check_until_timeout(url, attempts=30):
    for _ in range(attempts):
        time.sleep(1)
        try:
            if requests.get(url, verify=False).status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass

    raise ValueError(
        "Error, url did not respond after {0} attempts: {1}".format(attempts, url)
    )


@pytest.fixture
def pebble(tmp_path):
    workspace = tmp_path / "workspace"
    os.mkdir(str(workspace))

    pebble_path, challtestsrv_path, pebble_config_path = fetch(str(workspace))

    environ = os.environ.copy()
    environ["PEBBLE_VA_NOSLEEP"] = "1"
    environ["PEBBLE_WFE_NONCEREJECT"] = "0"
    environ["PEBBLE_AUTHZREUSE"] = "100"
    environ["PEBBLE_VA_ALWAYS_VALID"] = "1"

    pebble_process: Optional[subprocess.Popen] = None
    challtestsrv_process: Optional[subprocess.Popen] = None

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


@skipIf(platform.system() == "Darwin", reason="Integration tests are not supported on Mac OS X.")
def test_it(pebble, tmp_path):
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
    """
        )

    with patch.object(main._Daemon, "do_shutdown") as shutdown:
        shutdown.side_effect = [False, True]
        with patch(
            "dnsrobocert.core.certbot._DEFAULT_FLAGS", ["-n", "--no-verify-ssl"]
        ):
            main.main(["-c", str(config_path), "-d", str(directory_path)])

    assert os.path.exists(
        os.path.join(directory_path, "live", "test1.example.net", "cert.pem")
    )
