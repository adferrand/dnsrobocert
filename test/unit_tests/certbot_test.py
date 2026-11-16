from unittest import mock

from dnsrobocert.core import certbot


def test_certonly_with_acme_profile(tmp_path):
    """Test that acme_profile is passed to certbot as --preferred-profile."""
    config_path = tmp_path / "config.yml"
    config_path.write_text("""\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
""")

    with mock.patch("dnsrobocert.core.utils.execute") as mock_execute:
        lock = mock.MagicMock()
        certbot.certonly(
            config_path=str(config_path),
            directory_path=str(tmp_path),
            lineage="test.example.com",
            lock=lock,
            domains=["test.example.com"],
            acme_profile="shortlived",
        )

        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0][0]
        assert "--preferred-profile" in call_args
        assert "shortlived" in call_args
        profile_idx = call_args.index("--preferred-profile")
        assert call_args[profile_idx + 1] == "shortlived"


def test_certonly_without_acme_profile(tmp_path):
    """Test that --preferred-profile is not passed when acme_profile is not set."""
    config_path = tmp_path / "config.yml"
    config_path.write_text("""\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
""")

    with mock.patch("dnsrobocert.core.utils.execute") as mock_execute:
        lock = mock.MagicMock()
        certbot.certonly(
            config_path=str(config_path),
            directory_path=str(tmp_path),
            lineage="test.example.com",
            lock=lock,
            domains=["test.example.com"],
        )

        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0][0]
        assert "--preferred-profile" not in call_args


def test_issue_forwards_acme_profile(tmp_path):
    """Test that issue reads acme_profile from the certificate config and forwards it."""
    config_path = tmp_path / "config.yml"
    config_path.write_text("""\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
  acme_profile: shortlived
""")
    (tmp_path / "live").mkdir()

    with mock.patch("dnsrobocert.core.certbot.certonly") as mock_certonly:
        certbot.issue(str(config_path), str(tmp_path), mock.MagicMock())

        mock_certonly.assert_called_once()
        assert mock_certonly.call_args.kwargs["acme_profile"] == "shortlived"


def test_hook_cmd_quotes_arguments() -> None:
    import shlex

    command = certbot._hook_cmd("auth", '/tmp/a b/"$(evil)".yml', "x; rm -rf /")

    args = shlex.split(command)
    assert args[-4:] == ["-c", '/tmp/a b/"$(evil)".yml', "-l", "x; rm -rf /"]


_ISSUE_CONFIG = """\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [keep.example.com]
  profile: test
"""


def _issue_workspace(tmp_path, live_dirs):
    config_path = tmp_path / "config.yml"
    config_path.write_text(_ISSUE_CONFIG)
    for name in live_dirs:
        (tmp_path / "live" / name).mkdir(parents=True)
    return config_path


def test_issue_revokes_certificates_removed_from_config(tmp_path):
    config_path = _issue_workspace(
        tmp_path, ["keep.example.com", "old.example.com", "README"]
    )

    with (
        mock.patch("dnsrobocert.core.certbot.certonly"),
        mock.patch("dnsrobocert.core.certbot.revoke") as revoke,
    ):
        assert certbot.issue(str(config_path), str(tmp_path), mock.MagicMock())

    revoke.assert_called_once()
    assert revoke.call_args.args[2] == "old.example.com"


def test_issue_returns_false_when_a_certificate_fails(tmp_path):
    config_path = _issue_workspace(tmp_path, ["keep.example.com"])

    with mock.patch("dnsrobocert.core.certbot.certonly", side_effect=RuntimeError):
        assert not certbot.issue(str(config_path), str(tmp_path), mock.MagicMock())


def test_issue_returns_false_on_invalid_config(tmp_path):
    assert not certbot.issue(
        str(tmp_path / "missing.yml"), str(tmp_path), mock.MagicMock()
    )


def test_revoke_targets_certificate_of_lineage(tmp_path):
    config_path = _issue_workspace(tmp_path, [])

    with mock.patch("dnsrobocert.core.utils.execute") as execute:
        certbot.revoke(
            str(config_path), str(tmp_path), "old.example.com", mock.MagicMock()
        )

    command = execute.call_args[0][0]
    assert command[command.index("--cert-path") + 1] == str(
        tmp_path / "live" / "old.example.com" / "cert.pem"
    )


def test_account_skipped_without_email(tmp_path):
    config_path = _issue_workspace(tmp_path, [])

    with mock.patch("dnsrobocert.core.utils.execute") as execute:
        certbot.account(str(config_path), str(tmp_path), mock.MagicMock())

    execute.assert_not_called()


def test_account_registers_with_email(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("acme:\n  email_account: me@example.com\n" + _ISSUE_CONFIG)

    with mock.patch("dnsrobocert.core.utils.execute") as execute:
        certbot.account(str(config_path), str(tmp_path), mock.MagicMock())

    command = execute.call_args[0][0]
    assert "register" in command
    certbot_args = command[command.index("register") :]
    assert certbot_args[certbot_args.index("-m") + 1] == "me@example.com"
