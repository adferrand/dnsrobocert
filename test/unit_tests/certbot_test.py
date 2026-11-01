from unittest import mock

from dnsrobocert.core import certbot


def test_certonly_with_acme_profile(tmp_path):
    """Test that acme_profile is passed to certbot as --preferred-profile."""
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
"""
    )

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
    config_path.write_text(
        """\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
"""
    )

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
    """Test that _issue reads acme_profile from the certificate config and forwards it."""
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """\
draft: true
profiles:
- name: test
  provider: test
certificates:
- domains: [test.example.com]
  profile: test
  acme_profile: shortlived
"""
    )
    (tmp_path / "live").mkdir()

    with mock.patch("dnsrobocert.core.certbot.certonly") as mock_certonly:
        certbot._issue(str(config_path), str(tmp_path), mock.MagicMock())

        mock_certonly.assert_called_once()
        assert mock_certonly.call_args.kwargs["acme_profile"] == "shortlived"
