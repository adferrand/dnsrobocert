import hashlib
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List

import coloredlogs

try:
    POSIX_MODE = True
    import pwd
    import grp
except ImportError:
    POSIX_MODE = False

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def execute(args: List[str], check: bool = True, env: Dict[str, str] = None):
    if not env:
        env = os.environ.copy()
    env = env.copy()
    env["PYTHONUNBUFFERED "] = "1"

    LOGGER.debug("Launching command: {0}".format(subprocess.list2cmdline(args)))
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        universal_newlines=True,
    )

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            sys.stdout.write(" | " + output)

    errcode = process.poll()

    if errcode != 0 and check:
        raise RuntimeError(
            "Following command with non-zero errorcode ({0}):\n{1}".format(
                errcode, subprocess.list2cmdline(args)
            )
        )


def fix_permissions(certificate_permissions: Dict[str, Any], target_path: str):
    files_mode = certificate_permissions.get("files_mode", 0o640)
    dirs_mode = certificate_permissions.get("dirs_mode", 0o750)

    os.chmod(target_path, dirs_mode)

    uid = None
    gid = None
    user = certificate_permissions.get("user")
    group = certificate_permissions.get("group")

    if (user or group) and not POSIX_MODE:
        LOGGER.warning(
            "Setting user and group for certificates/keys is not supported on Windows."
        )
    elif POSIX_MODE:
        uid = pwd.getpwnam(user)[2] if user else -1
        gid = grp.getgrnam(group)[2] if group else -1
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


def digest(path):
    if not os.path.exists(path):
        return None

    with open(path, "rb") as file_h:
        config_data = file_h.read()

    md5 = hashlib.md5()
    md5.update(config_data)
    return md5.digest()
