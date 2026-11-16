import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dnsrobocert.core import main


@patch("dnsrobocert.core.main.certbot.account")
@patch("dnsrobocert.core.main.certbot.certonly")
@patch("dnsrobocert.core.main.certbot.revoke")
@patch("dnsrobocert.core.main.background")
@patch.object(main._Daemon, "do_shutdown")
def test_main_loop(
    shutdown: MagicMock,
    background: MagicMock,
    revoke: MagicMock,
    certonly: MagicMock,
    account: MagicMock,
    tmp_path: Path,
) -> None:
    directory_path = tmp_path / "letsencrypt"
    os.mkdir(directory_path)

    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write("""\
draft: false
acme:
  email_account: john.doe@example.net
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
""")

    shutdown.side_effect = [False, True]
    main.main(["-c", str(config_path), "-d", str(directory_path)])

    assert shutdown.called
    assert account.called
    assert certonly.called
    assert not revoke.called
    assert background.worker.called


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main.main(["--version"])

    assert raised.value.code == 0
    assert capsys.readouterr().out.startswith("DNSroboCert ")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(SystemExit) as raised:
        main.main(["--log-level", "LOUD"])

    assert raised.value.code == 2


@patch("dnsrobocert.core.main._watch_config")
def test_log_level_flag_configures_logging(watch: MagicMock) -> None:
    with patch("dnsrobocert.core.main.utils.configure_logging") as configure:
        main.main(["--log-level", "debug", "-c", "config.yml", "-d", "dir"])

    configure.assert_called_once_with("DEBUG")
    watch.assert_called_once()
