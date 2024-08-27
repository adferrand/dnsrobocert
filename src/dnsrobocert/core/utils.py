from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import coloredlogs
from certbot.compat import misc

try:
    POSIX_MODE = True
    import grp
    import pwd
except ImportError:
    POSIX_MODE = False

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def execute(
    command: list[str] | str,
    check: bool = True,
    shell: bool = False,
    env: dict[str, str] | None = None,
    lock: threading.Lock | None = None,
) -> None:
    if not env:
        env = os.environ.copy()
    env = env.copy()
    env["PYTHONUNBUFFERED "] = "1"

    call = subprocess.check_call if check else subprocess.call

    LOGGER.info(
        f"Launching command: {subprocess.list2cmdline(command) if isinstance(command, list) else command}"
    )
    sys.stdout.write("----------\n")
    sys.stdout.flush()

    error = None
    try:
        if lock:
            with lock:
                call(command, shell=shell, env=env)
        else:
            call(command, shell=shell, env=env)
    except subprocess.CalledProcessError as e:
        error = e

    sys.stdout.write("----------\n")
    sys.stdout.flush()

    if error:
        raise error


def fix_permissions(certificate_permissions: dict[str, Any], target_path: str) -> None:
    files_mode = certificate_permissions.get("files_mode", 0o640)
    dirs_mode = certificate_permissions.get("dirs_mode", 0o750)

    os.chmod(target_path, dirs_mode)

    uid = -1
    gid = -1

    user = certificate_permissions.get("user")
    group = certificate_permissions.get("group")

    if (user or group) and not POSIX_MODE:
        LOGGER.warning(
            "Setting user and group for certificates/keys is not supported on Windows."
        )
    elif POSIX_MODE:
        if isinstance(user, int):
            uid = user
        elif isinstance(user, str):
            uid = pwd.getpwnam(user)[2]

        if isinstance(group, int):
            gid = group
        elif isinstance(group, str):
            gid = grp.getgrnam(group)[2]

        os.chown(target_path, uid, gid)  # type: ignore

    for root, dirs, files in os.walk(target_path):
        for path in dirs:
            os.chmod(os.path.join(root, path), dirs_mode)
        for path in files:
            os.chmod(os.path.join(root, path), files_mode)
        if POSIX_MODE:
            for path in files + dirs:
                os.chown(os.path.join(root, path), uid, gid)  # type: ignore


def configure_certbot_workspace(
    dnsrobocert_config: dict[str, Any], directory_path: str
) -> None:
    live_path = os.path.join(directory_path, "archive")
    archive_path = os.path.join(directory_path, "live")

    if not os.path.exists(live_path):
        os.makedirs(live_path)
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)

    certificate_permissions = dnsrobocert_config.get("acme", {}).get(
        "certs_permissions", {}
    )
    fix_permissions(certificate_permissions, live_path)
    fix_permissions(certificate_permissions, archive_path)


def digest(path: str) -> bytes | None:
    if not os.path.exists(path):
        return None

    with open(path, "rb") as file_h:
        config_data = file_h.read()

    md5 = hashlib.md5()
    md5.update(config_data)
    return md5.digest()


def normalize_lineage(domain: str) -> str:
    return re.sub(r"^\*\.", "", domain)


def validate_snap_environment(args: argparse.Namespace) -> None:
    """
    Verify that the provided CLI flags are compatible with an execution of
    DNSroboCert inside snap. No-op if we are not in a snap.
    """
    if not os.environ.get("SNAP"):
        return

    errors = []

    if not _is_valid_path_for_snap(args.config):
        errors.append(f"Invalid --config value: {args.config}")

    if not _is_valid_path_for_snap(args.directory):
        errors.append(f"Invalid --directory value: {args.directory}")

    for error in errors:
        LOGGER.error(error)

    if errors:
        LOGGER.error(
            "Snap DNSroboCert can only use non-hidden files and directories "
            "located in the user HOME folder by default."
        )
        LOGGER.error(
            "DNSroboCert can be granted to use the /etc directory with this command: "
            "snap connect dnsrobocert:etc"
        )

        sys.exit(1)


def get_default_args() -> dict[str, str]:
    """
    Retrieve the default values of CLI flags depending on the execution context.
    """
    if os.environ.get("SNAP"):
        user_home = os.environ.get("SNAP_REAL_HOME", str(Path.home()))
        return {
            "config": os.path.join(user_home, "dnsrobocert/dnsrobocert.yml"),
            "configDesc": os.path.join(user_home, "dnsrobocert/dnsrobocert.yml"),
            "directory": os.path.join(user_home, "dnsrobocert/letsencrypt"),
            "directoryDesc": os.path.join(user_home, "dnsrobocert/letsencrypt"),
        }

    return {
        "config": os.path.join(os.getcwd(), "dnsrobocert.yml"),
        "configDesc": "$(pwd)/dnsrobocert.yml",
        "directory": misc.get_default_folder("config"),
        "directoryDesc": misc.get_default_folder("config"),
    }


def _is_valid_path_for_snap(path: str) -> bool:
    """
    Check that the given path:
    * is relative to home_path and it is not composed of hidden parts (folder/files starting with "."),
    * or is located inside /etc if the snap is authorized to use /etc (connected to system_file interface).
    """
    home_path = os.environ.get("SNAP_REAL_HOME", str(Path.home()))

    # Check if the snap is authorized to use the /etc directory
    try:
        os.listdir("/etc")
        system_files_interface = True
    except PermissionError:
        system_files_interface = False

    return (
        os.path.abspath(path).startswith(home_path)
        and not any(part for part in _split_path(path) if part.startswith("."))
    ) or (system_files_interface and os.path.abspath(path).startswith("/etc/"))


def _split_path(path: str) -> list[str]:
    """
    Split the given path into an array containing each part composing the path.
    For instance: /etc/to/my/config.yml => ["/", "etc", "to", "my", "config.yml"].
    """
    all_parts: list[str] = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            all_parts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            all_parts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            all_parts.insert(0, parts[1])

    return all_parts
