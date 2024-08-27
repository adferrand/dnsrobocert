#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import tempfile
import threading
import time
import traceback
from typing import Any

import coloredlogs
import yaml

from dnsrobocert.core import background, certbot, config, legacy, utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def _process_config(
    config_path: str,
    directory_path: str,
    runtime_config_path: str,
    lock: threading.Lock,
) -> None:
    dnsrobocert_config = config.load(config_path)

    if not dnsrobocert_config:
        return

    if dnsrobocert_config.get("draft"):
        LOGGER.info("Configuration file is in draft mode: no action will be done.")
        return

    with open(runtime_config_path, "w") as f:
        f.write(yaml.dump(dnsrobocert_config))

    utils.configure_certbot_workspace(dnsrobocert_config, directory_path)

    LOGGER.info("Registering ACME account if needed.")
    certbot.account(runtime_config_path, directory_path, lock)

    LOGGER.info("Creating missing certificates if needed (~1min for each)")
    certbot._issue(runtime_config_path, directory_path, lock)


class _Daemon:
    _do_shutdown = False

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, _signum: Any, _frame: Any) -> None:
        self._do_shutdown = True

    def do_shutdown(self) -> bool:
        return self._do_shutdown


def _watch_config(config_path: str, directory_path: str) -> None:
    LOGGER.info("Starting DNSroboCert.")

    with tempfile.TemporaryDirectory() as workspace:
        runtime_config_path = os.path.join(workspace, "dnsrobocert-runtime.yml")
        certbot_lock = threading.Lock()

        with background.worker(runtime_config_path, directory_path, certbot_lock):
            daemon = _Daemon()
            previous_digest = ""
            while not daemon.do_shutdown():
                try:
                    generated_config_path = legacy.migrate(config_path)
                    effective_config_path = (
                        generated_config_path if generated_config_path else config_path
                    )
                    digest = utils.digest(effective_config_path)

                    if digest != previous_digest:
                        previous_digest = digest
                        _process_config(
                            effective_config_path,
                            directory_path,
                            runtime_config_path,
                            certbot_lock,
                        )
                except BaseException as error:
                    LOGGER.error("An error occurred during DNSroboCert watch:")
                    LOGGER.error(error)
                    traceback.print_exc(file=sys.stderr)

                time.sleep(1)

    LOGGER.info("Exiting DNSroboCert.")


def _run_config(config_path: str, directory_path: str) -> None:
    LOGGER.info("Running DNSroboCert...")

    with tempfile.TemporaryDirectory() as workspace:
        runtime_config_path = os.path.join(workspace, "dnsrobocert-runtime.yml")
        certbot_lock = threading.Lock()

        generated_config_path = legacy.migrate(config_path)
        effective_config_path = (
            generated_config_path if generated_config_path else config_path
        )

        _process_config(
            effective_config_path,
            directory_path,
            runtime_config_path,
            certbot_lock,
        )


def main(args: list[str] | None = None) -> None:
    if not args:
        args = sys.argv[1:]

    defaults = utils.get_default_args()

    parser = argparse.ArgumentParser(description="Start dnsrobocert.")
    parser.add_argument(
        "--config",
        "-c",
        default=defaults["config"],
        help=f"set the dnsrobocert config to use (default {defaults['configDesc']})",
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=defaults["directory"],
        help=f"set the directory path where certificates are stored (default: {defaults['directoryDesc']})",
    )
    parser.add_argument(
        "--one-shot",
        "-o",
        action="store_true",
        help="if set, DNSroboCert will process only once certificates (creation, renewal, deletion) then return immediately",
    )

    parsed_args = parser.parse_args(args)

    utils.validate_snap_environment(parsed_args)

    if parsed_args.one_shot:
        _run_config(
            os.path.abspath(parsed_args.config), os.path.abspath(parsed_args.directory)
        )
    else:
        _watch_config(
            os.path.abspath(parsed_args.config), os.path.abspath(parsed_args.directory)
        )


if __name__ == "__main__":
    main()
