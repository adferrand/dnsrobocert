import os
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        f.write(
            """\
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
"""
        )

    shutdown.side_effect = [False, True]
    main.main(["-c", str(config_path), "-d", str(directory_path)])

    assert shutdown.called
    assert account.called
    assert certonly.called
    assert not revoke.called
    assert background.worker.called
