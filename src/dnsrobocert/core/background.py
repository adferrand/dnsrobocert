import logging
import threading
import time
from contextlib import contextmanager
from random import random

import coloredlogs
import schedule
from dnsrobocert.core import certbot

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


@contextmanager
def worker(config_path: str, directory_path: str):
    schedule.every().day.at("12:00").do(
        _renew_job, config_path=config_path, directory_path=directory_path
    )
    schedule.every().day.at("00:00").do(
        _renew_job, config_path=config_path, directory_path=directory_path
    )

    stop_thread = _launch_background_jobs()

    try:
        yield
    finally:
        stop_thread.set()


def _launch_background_jobs(interval: int = 1) -> threading.Event:
    stop_thread = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not stop_thread.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()

    return stop_thread


def _renew_job(config_path: str, directory_path: str):
    random_delay_seconds = 21600  # Random delay up to 12 hours
    wait_time = int(random() * random_delay_seconds)
    LOGGER.info("Automated execution: renew certificates if needed.")
    LOGGER.info(f"Random wait for this execution: {wait_time} seconds")
    time.sleep(wait_time)
    certbot.renew(config_path, directory_path)
