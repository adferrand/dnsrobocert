from dnsrobocert.core import config


def test_good_config_minimal(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
"""
        )

    parsed = config.load(str(config_path))
    assert parsed


def test_bad_config_wrong_schema(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
wrong_property: bad
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_non_existent_profile(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
profiles:
- name: one
  provider: one
certificates:
- domains: [test.example.com]
  profile: two
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_wrong_posix_mode(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
acme:
  certs_permissions:
    files_mode: 9999
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_bad_config_duplicated_cert_name(tmp_path):
    config_path = tmp_path / "config.yml"
    with open(str(config_path), "w") as f:
        f.write(
            """\
draft: true
profiles:
- name: one
  provider: one
certificates:
- domains: [test.example.com]
  profile: one
- name: test.example.com
  domains: [test1.example.com, test2.example.com]
  profile: one
"""
        )

    parsed = config.load(str(config_path))
    assert not parsed


def test_wildcard_lineage():
    certificate = {"domains": ["*.example.com", "example.com"], "profile": "dummy"}

    assert config.get_lineage(certificate) == "example.com"
