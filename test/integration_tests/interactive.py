"""Interactive mode of the integration tests.

Starts Pebble and pebble-challtestsrv, then runs dnsrobocert against any
configuration. Set `acme.directory_url` to https://127.0.0.1:14000/dir.

    python test/integration_tests/interactive.py [-c CONFIG] [-d DIRECTORY] [--watch]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from dnsrobocert_test import _CHALLTESTSRV_PORT, _start_pebble

from dnsrobocert.core import main

_WORKSPACE_PATH = Path(__file__).parent / "interactive-workspace"

_SAMPLE_CONFIG = """\
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


def _list_certs(directory_path: Path) -> None:
    live_path = directory_path / "live"
    if not live_path.is_dir():
        print("No certificates yet.")
        return
    for name in sorted(os.listdir(live_path)):
        if not (live_path / name).is_dir():
            continue
        print(f"{name}: {sorted(os.listdir(live_path / name))}")


def _run(config_path: Path, directory_path: Path, watch: bool) -> None:
    args = ["-c", str(config_path), "-d", str(directory_path)]
    if not watch:
        args.append("--one-shot")
    try:
        main.main(args)
    except SystemExit as e:
        print(f"dnsrobocert exited: {e.code}")
    except Exception as e:  # noqa: BLE001
        print(f"dnsrobocert failed: {e!r}")


def _interact(config_path: Path, directory_path: Path, watch: bool) -> None:
    if watch:
        print("Watch mode: press Ctrl+C to stop.")
        _run(config_path, directory_path, True)
        return

    while True:
        _run(config_path, directory_path, False)
        while True:
            choice = input("[r]erun / [l]ist certs / [q]uit: ").strip().lower()
            if choice == "l":
                _list_certs(directory_path)
            elif choice == "r":
                break
            elif choice == "q":
                return


def cli(argv: list[str] | None = None) -> None:
    assert __doc__ is not None
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "-c",
        "--config",
        help="dnsrobocert config (default: interactive-workspace/config.yml, created from a sample if missing)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="certificates directory (default: interactive-workspace/letsencrypt)",
    )
    parser.add_argument("--watch", action="store_true", help="run in daemon mode")
    options = parser.parse_args(argv)

    _WORKSPACE_PATH.mkdir(exist_ok=True)

    # Pebble needs a fresh directory, hence a temp one distinct from the workspace.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        if options.config:
            config_path = Path(options.config).resolve()
        else:
            config_path = _WORKSPACE_PATH / "config.yml"
            if not config_path.exists():
                config_path.write_text(_SAMPLE_CONFIG)

        directory_path = (
            Path(options.directory).resolve()
            if options.directory
            else _WORKSPACE_PATH / "letsencrypt"
        )
        directory_path.mkdir(parents=True, exist_ok=True)

        with _start_pebble(tmp_path):
            print("ACME directory:   https://127.0.0.1:14000/dir")
            print(f"challtestsrv API: http://127.0.0.1:{_CHALLTESTSRV_PORT}")
            print(f"Config:           {config_path}")
            print(f"Certificates:     {directory_path}")
            with patch(
                "dnsrobocert.core.certbot._DEFAULT_FLAGS", ["-n", "--no-verify-ssl"]
            ):
                try:
                    _interact(config_path, directory_path, options.watch)
                except (KeyboardInterrupt, EOFError):
                    print()


if __name__ == "__main__":
    cli(sys.argv[1:])
