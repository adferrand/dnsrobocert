from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from random import random

import coloredlogs
import schedule

from dnsrobocert.core import certbot

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


@contextmanager
def worker(
    config_path: str, directory_path: str, lock: threading.Lock
) -> Iterator[None]:
    stop_thread = threading.Event()

    schedule.every().day.at("12:00").do(
        _renew_job,
        config_path=config_path,
        directory_path=directory_path,
        lock=lock,
        stop_thread=stop_thread,
    )
    schedule.every().day.at("00:00").do(
        _renew_job,
        config_path=config_path,
        directory_path=directory_path,
        lock=lock,
        stop_thread=stop_thread,
    )

    _launch_background_jobs(stop_thread)

    try:
        yield
    finally:
        stop_thread.set()


def _launch_background_jobs(stop_thread: threading.Event, interval: int = 1) -> None:
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls) -> None:
            while not stop_thread.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()


def _renew_job(
    config_path: str,
    directory_path: str,
    lock: threading.Lock,
    stop_thread: threading.Event,
) -> None:
    random_delay_seconds = 21600  # Random delay up to 12 hours
    wait_time = int(random() * random_delay_seconds)

    LOGGER.info("Automated execution: renew certificates if needed.")
    LOGGER.info(f"Random wait for this execution: {wait_time} seconds")

    interrupted = stop_thread.wait(wait_time)

    if not interrupted:
        certbot.renew(config_path, directory_path, lock)
