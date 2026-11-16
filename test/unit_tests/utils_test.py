from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from dnsrobocert.core import utils

posix_only = pytest.mark.skipif(not utils.POSIX_MODE, reason="POSIX only")


def test_execute_runs_command_with_unbuffered_env() -> None:
    with patch("subprocess.check_call") as check_call:
        utils.execute(["echo", "hello"], env={"A": "B"})

    env = check_call.call_args.kwargs["env"]
    assert env["A"] == "B"
    assert env["PYTHONUNBUFFERED"] == "1"
    assert check_call.call_args.args[0] == ["echo", "hello"]


def test_execute_without_check_uses_call() -> None:
    with patch("subprocess.call") as call, patch("subprocess.check_call") as check_call:
        utils.execute(["false"], check=False)

    call.assert_called_once()
    check_call.assert_not_called()


def test_execute_raises_on_failure() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        utils.execute([sys.executable, "-c", "raise SystemExit(3)"])


def test_execute_holds_lock_during_command() -> None:
    lock = threading.Lock()
    seen: list[bool] = []

    with patch(
        "subprocess.check_call", side_effect=lambda *a, **k: seen.append(lock.locked())
    ):
        utils.execute(["echo"], lock=lock)

    assert seen == [True]
    assert not lock.locked()


def test_digest(tmp_path: Path) -> None:
    path = tmp_path / "file"
    assert utils.digest(str(path)) is None

    path.write_bytes(b"content")
    assert utils.digest(str(path)) == hashlib.md5(b"content").digest()


def test_normalize_lineage() -> None:
    assert utils.normalize_lineage("*.example.com") == "example.com"
    assert utils.normalize_lineage("example.com") == "example.com"


def test_split_path() -> None:
    assert utils._split_path(os.path.join("a", "b", "c.yml")) == ["a", "b", "c.yml"]


@posix_only
def test_fix_permissions_applies_modes(tmp_path: Path) -> None:
    root = tmp_path / "live"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "key.pem").write_text("key")

    utils.fix_permissions({"files_mode": 0o600, "dirs_mode": 0o700}, str(root))

    assert stat.S_IMODE(os.stat(root).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(root / "sub").st_mode) == 0o700
    assert stat.S_IMODE(os.stat(root / "sub" / "key.pem").st_mode) == 0o600


@posix_only
def test_fix_permissions_follows_symlinks_into_archive(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    live = tmp_path / "live"
    archive.mkdir()
    live.mkdir()
    (archive / "key1.pem").write_text("key")
    os.chmod(archive / "key1.pem", 0o644)
    os.symlink(archive / "key1.pem", live / "key.pem")

    utils.fix_permissions({"files_mode": 0o600, "dirs_mode": 0o700}, str(live))

    assert stat.S_IMODE(os.stat(archive / "key1.pem").st_mode) == 0o600


@posix_only
def test_fix_permissions_unknown_group_is_ignored(tmp_path: Path) -> None:
    (tmp_path / "f").write_text("x")
    utils.fix_permissions(
        {"files_mode": 0o600, "dirs_mode": 0o700, "group": "no-such-group-xyz"},
        str(tmp_path),
    )


@posix_only
def test_fix_permissions_unknown_user_raises(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        utils.fix_permissions({"user": "no-such-user-xyz"}, str(tmp_path))


def test_configure_certbot_workspace(tmp_path: Path) -> None:
    utils.configure_certbot_workspace({}, str(tmp_path / "certs"))

    assert (tmp_path / "certs" / "live").is_dir()
    assert (tmp_path / "certs" / "archive").is_dir()


def test_validate_snap_environment_noop_outside_snap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SNAP", raising=False)
    utils.validate_snap_environment(argparse.Namespace(config="/x/.y", directory="/z"))


def test_validate_snap_environment_rejects_hidden_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SNAP", "/snap/dnsrobocert")
    monkeypatch.setenv("SNAP_REAL_HOME", str(tmp_path))

    args = argparse.Namespace(
        config=str(tmp_path / ".hidden" / "config.yml"),
        directory=str(tmp_path / "certs"),
    )
    with pytest.raises(SystemExit) as raised:
        utils.validate_snap_environment(args)
    assert raised.value.code == 1


def test_validate_snap_environment_accepts_home_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SNAP", "/snap/dnsrobocert")
    monkeypatch.setenv("SNAP_REAL_HOME", str(tmp_path))

    args = argparse.Namespace(
        config=str(tmp_path / "config.yml"), directory=str(tmp_path / "certs")
    )
    utils.validate_snap_environment(args)


def test_get_default_args(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SNAP", raising=False)
    defaults = utils.get_default_args()
    assert defaults["config"].endswith("dnsrobocert.yml")
    assert defaults["configDesc"] == "$(pwd)/dnsrobocert.yml"

    monkeypatch.setenv("SNAP", "/snap/dnsrobocert")
    monkeypatch.setenv("SNAP_REAL_HOME", str(tmp_path))
    defaults = utils.get_default_args()
    assert defaults["config"] == str(tmp_path / "dnsrobocert" / "dnsrobocert.yml")
    assert defaults["directory"] == str(tmp_path / "dnsrobocert" / "letsencrypt")
