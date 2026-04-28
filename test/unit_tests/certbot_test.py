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
