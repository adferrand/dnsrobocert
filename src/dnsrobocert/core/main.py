#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import multiprocessing
import os
import re
import sys
import time
import traceback
import logging
from random import random
import tempfile

import schedule
import coloredlogs
import yaml

from certbot.compat import misc
from dnsrobocert.core import certbot, config, legacy, utils

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def process_config(config_path: str, directory_path: str, runtime_config_path: str):
    dnsrobocert_config = config.load(config_path)

    if not dnsrobocert_config:
        return

    if dnsrobocert_config.get("draft"):
        LOGGER.info("Configuration file is in draft mode: no action will be done.")
        return

    with open(runtime_config_path, 'w') as f:
        f.write(yaml.dump(dnsrobocert_config))

    utils.configure_certbot_workspace(dnsrobocert_config, directory_path)

    LOGGER.info("Registering ACME account if needed.")
    certbot.account(runtime_config_path, directory_path)

    LOGGER.info("Creating missing certificates if needed (~1min for each)")
    certificates = dnsrobocert_config.get("certificates", {})
    for domain, cert_config in certificates.items():
        try:
            san = cert_config.get("san", [])
            force_renew = cert_config.get("force_renew", False)
            LOGGER.info(
                "Handling the certificate for domain(s): {0}".format(
                    ", ".join([domain, *san])
                )
            )
            certbot.certonly(
                runtime_config_path,
                directory_path,
                domain,
                secondaries=san,
                force_renew=force_renew,
            )
        except BaseException as error:
            LOGGER.error(
                "An error occurred while processing certificate config `{0}`:\n{1}".format(domain, error)
            )

    LOGGER.info("Revoke and delete certificates if needed")
    lineages = set(certificates.keys())
    for domain in os.listdir(os.path.join(directory_path, "live")):
        if domain != "README":
            domain = re.sub(r"^\*\.", "", domain)
            if domain not in lineages:
                LOGGER.info("Removing the certificate {0}".format(domain))
                certbot.revoke(runtime_config_path, directory_path, domain)


def watch_config(config_path: str, directory_path: str):
    with tempfile.NamedTemporaryFile() as runtime_config_file:
        runtime_config_path = runtime_config_file.name

        process = multiprocessing.Process(
            target=renew_worker, args=(runtime_config_path, directory_path)
        )

        process.start()
        previous_digest = None

        try:
            while True:
                try:
                    generated_config_path = legacy.migrate(config_path)
                    effective_config_path = generated_config_path if generated_config_path else config_path
                    digest = utils.digest(effective_config_path)

                    if digest != previous_digest:
                        previous_digest = digest
                        process_config(effective_config_path, directory_path, runtime_config_path)
                except BaseException as error:
                    LOGGER.error("An error occurred during DNSroboCert watch:")
                    LOGGER.error(error)
                    traceback.print_exc(file=sys.stdout)

                time.sleep(1)
        except KeyboardInterrupt:
            process.terminate()
            process.join()


def renew_job(config_path: str, directory_path: str):
    random_delay_seconds = 21600  # Random delay up to 12 hours
    wait_time = int(random() * random_delay_seconds)
    LOGGER.info(
        "Random wait for this renew_job execution: {0} seconds".format(wait_time)
    )
    time.sleep(wait_time)
    certbot.renew(config_path, directory_path)


def renew_worker(config_path: str, directory_path: str):
    schedule.every().day.at("12:00").do(
        renew_job, config_path=config_path, directory_path=directory_path
    )
    schedule.every().day.at("00:00").do(
        renew_job, config_path=config_path, directory_path=directory_path
    )
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Start dnsrobocert.")
    parser.add_argument(
        "--config",
        "-c",
        default=os.path.join(misc.get_default_folder("config"), "dnsrobocert.yml"),
        help="Set the dnsrobocert config to use.",
    )
    parser.add_argument(
        "--directory",
        "-d",
        default=misc.get_default_folder("config"),
        help="Set the directory path where certificates are stored.",
    )

    args = parser.parse_args()

    watch_config(os.path.abspath(args.config), os.path.abspath(args.directory))


if __name__ == "__main__":
    main()
