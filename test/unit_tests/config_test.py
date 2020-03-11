from dnsrobocert.core import config


def test_good_config(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
acme:
  email_account: john.doe@example.com
  staging: true
  api_version: 2
certificates: []
profiles: []
"""
        )

    parsed = config.load(str(config_path))
    assert parsed


def test_wildcard_lineage():
    certificate = {
        'domains': ['*.example.com', 'example.com'],
        'profile': 'dummy'
    }

    assert config.get_lineage(certificate) == 'example.com'
