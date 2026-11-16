from __future__ import annotations

import threading
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
import schedule

from dnsrobocert.core import background


@pytest.fixture(autouse=True)
def clean_scheduler() -> Iterator[None]:
    schedule.clear()
    yield
    schedule.clear()


def test_renew_job_renews_after_delay() -> None:
    stop_thread = threading.Event()
    lock = threading.Lock()

    with (
        patch("dnsrobocert.core.background.random", return_value=0.0),
        patch("dnsrobocert.core.background.certbot.renew") as renew,
    ):
        background._renew_job("config.yml", "/dir", lock, stop_thread)

    renew.assert_called_once_with("config.yml", "/dir", lock)


def test_renew_job_delay_is_bounded() -> None:
    stop_thread = MagicMock()
    stop_thread.wait.return_value = False

    with (
        patch("dnsrobocert.core.background.random", return_value=0.999999),
        patch("dnsrobocert.core.background.certbot.renew"),
    ):
        background._renew_job("config.yml", "/dir", threading.Lock(), stop_thread)

    assert 0 <= stop_thread.wait.call_args[0][0] < 21600


def test_renew_job_skipped_when_interrupted() -> None:
    stop_thread = threading.Event()
    stop_thread.set()

    with patch("dnsrobocert.core.background.certbot.renew") as renew:
        background._renew_job("config.yml", "/dir", threading.Lock(), stop_thread)

    renew.assert_not_called()


def test_worker_schedules_two_daily_jobs_and_stops() -> None:
    captured: list[threading.Event] = []

    with (
        patch(
            "dnsrobocert.core.background._launch_background_jobs",
            side_effect=captured.append,
        ),
        background.worker("config.yml", "/dir", threading.Lock()),
    ):
        assert sorted(str(job.at_time) for job in schedule.get_jobs()) == [
            "00:00:00",
            "12:00:00",
        ]
        assert not captured[0].is_set()

    assert captured[0].is_set()


def test_background_thread_runs_pending_jobs_until_stopped() -> None:
    stop_thread = threading.Event()

    def run_pending() -> None:
        stop_thread.set()

    with patch("schedule.run_pending", side_effect=run_pending) as run:
        background._launch_background_jobs(stop_thread, interval=0)
        for thread in threading.enumerate():
            if thread is not threading.current_thread() and thread.name.startswith(
                "Thread-"
            ):
                thread.join(timeout=5)

    run.assert_called()
