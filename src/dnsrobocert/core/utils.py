import hashlib
import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Union

import coloredlogs

try:
    POSIX_MODE = True
    import grp
    import pwd
except ImportError:
    POSIX_MODE = False

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def execute(
    command: Union[List[str], str],
    check: bool = True,
    shell: bool = False,
    env: Dict[str, str] = None,
):
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
        call(command, shell=shell, env=env)
    except subprocess.CalledProcessError as e:
        error = e

    sys.stdout.write("----------\n")
    sys.stdout.flush()

    if error:
        raise error


def fix_permissions(certificate_permissions: Dict[str, Any], target_path: str):
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
    dnsrobocert_config: Dict[str, Any], directory_path: str
):
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


def digest(path: str):
    if not os.path.exists(path):
        return None

    with open(path, "rb") as file_h:
        config_data = file_h.read()

    md5 = hashlib.md5()
    md5.update(config_data)
    return md5.digest()


def normalize_lineage(domain: str):
    return re.sub(r"^\*\.", "", domain)
