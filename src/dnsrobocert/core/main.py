#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import logging
import os
import re
import signal
import sys
import tempfile
import time
import traceback
from random import random
from typing import List, Optional

import coloredlogs
import schedule
import yaml
from certbot.compat import misc

from dnsrobocert.core import certbot, config, legacy, utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def _process_config(config_path: str, directory_path: str, runtime_config_path: str):
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
    certbot.account(runtime_config_path, directory_path)

    LOGGER.info("Creating missing certificates if needed (~1min for each)")
    certificates = dnsrobocert_config.get("certificates", {})
    for certificate in certificates:
        try:
            lineage = config.get_lineage(certificate)
            domains = certificate["domains"]
            force_renew = certificate.get("force_renew", False)
            LOGGER.info(f"Handling the certificate for domain(s): {', '.join(domains)}")
            certbot.certonly(
                runtime_config_path,
                directory_path,
                lineage,
                domains,
                force_renew=force_renew,
            )
        except BaseException as error:
            LOGGER.error(
                f"An error occurred while processing certificate config `{certificate}`:\n{error}"
            )

    LOGGER.info("Revoke and delete certificates if needed")
    lineages = {config.get_lineage(certificate) for certificate in certificates}
    for domain in os.listdir(os.path.join(directory_path, "live")):
        if domain != "README":
            domain = re.sub(r"^\*\.", "", domain)
            if domain not in lineages:
                LOGGER.info(f"Removing the certificate {domain}")
                certbot.revoke(runtime_config_path, directory_path, domain)


class _Daemon:
    _do_shutdown = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, _signum, _frame):
        self._do_shutdown = True

    def do_shutdown(self):
        return self._do_shutdown


def _renew_job(config_path: str, directory_path: str):
    random_delay_seconds = 21600  # Random delay up to 12 hours
    wait_time = int(random() * random_delay_seconds)
    LOGGER.info("Automated execution: renew certificates if needed.")
    LOGGER.info(f"Random wait for this execution: {wait_time} seconds")
    time.sleep(wait_time)
    certbot.renew(config_path, directory_path)


def _watch_config(config_path: str, directory_path: str):
    LOGGER.info("Starting DNSroboCert.")

    with tempfile.TemporaryDirectory() as workspace:
        runtime_config_path = os.path.join(workspace, "dnsrobocert-runtime.yml")

        schedule.every().day.at("12:00").do(
            _renew_job, config_path=runtime_config_path, directory_path=directory_path
        )
        schedule.every().day.at("00:00").do(
            _renew_job, config_path=runtime_config_path, directory_path=directory_path
        )

        daemon = _Daemon()
        previous_digest = ""
        while not daemon.do_shutdown():
            schedule.run_pending()

            try:
                generated_config_path = legacy.migrate(config_path)
                effective_config_path = (
                    generated_config_path if generated_config_path else config_path
                )
                digest = utils.digest(effective_config_path)

                if digest != previous_digest:
                    previous_digest = digest
                    _process_config(
                        effective_config_path, directory_path, runtime_config_path
                    )
            except BaseException as error:
                LOGGER.error("An error occurred during DNSroboCert watch:")
                LOGGER.error(error)
                traceback.print_exc(file=sys.stderr)

            time.sleep(1)

    LOGGER.info("Exiting DNSroboCert.")


def main(args: Optional[List[str]] = None):
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Start dnsrobocert.")
    parser.add_argument(
        "--config",
        "-c",
        default=os.path.join(os.getcwd(), "dnsrobocert.yml"),
        help="Set the dnsrobocert config to use.",
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=misc.get_default_folder("config"),
        help="Set the directory path where certificates are stored.",
    )

    parsed_args = parser.parse_args(args)

    _watch_config(
        os.path.abspath(parsed_args.config), os.path.abspath(parsed_args.directory)
    )


if __name__ == "__main__":
    main()
