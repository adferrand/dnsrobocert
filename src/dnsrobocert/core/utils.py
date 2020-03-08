import logging
import os
import subprocess
from typing import Any, Dict, List
import hashlib
import multiprocessing
import sys

import coloredlogs

try:
    POSIX_MODE = True
    import pwd
    import grp
except ImportError:
    POSIX_MODE = False

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


def _flush_subprocess_stream(process: subprocess.Popen, stdtype: str ='stdout'):
    if stdtype == 'stdout':
        std = process.stdout
    else:
        std = process.stderr
    
    while True:
        output = std.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            sys.stdout.write(' | ' + output)
    process.poll()


def execute(args: List[str], check: bool = True, env: Dict[str, str] = None):
    if not env:
        env = os.environ.copy()
    env = env.copy()
    env['PYTHONUNBUFFERED '] = '1'

    LOGGER.debug("Launching command: {0}".format(subprocess.list2cmdline(args)))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, universal_newlines=True)
    process_stdout = multiprocessing.Process(target=_flush_subprocess_stream, args=(process, 'stdout'))
    process_stderr = multiprocessing.Process(target=_flush_subprocess_stream, args=(process, 'stderr'))

    process_stdout.start()
    process_stderr.start()

    process_stdout.join()
    process_stderr.join()
    errcode = process.poll()

    if errcode != 0 and check:
        raise RuntimeError('Following command with non-zero errorcode ({0}):\n{1}'.format(errcode, subprocess.list2cmdline(args)))


def fix_permissions(certs_perms_config: Dict[str, Any], target_path: str):
    files_mode = certs_perms_config.get("files_mode", 0o640)
    dirs_mode = certs_perms_config.get("dirs_mode", 0o750)

    os.chmod(target_path, dirs_mode)

    uid = None
    gid = None
    user = certs_perms_config.get("user")
    group = certs_perms_config.get("group")
    if (user or group) and not POSIX_MODE:
        LOGGER.warning(
            "Setting user and group for certificates/keys is not supported on Windows."
        )
    else:
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


def configure_certbot_workspace(config: Dict[str, Any], directory_path: str):
    live_path = os.path.join(directory_path, "archive")
    archive_path = os.path.join(directory_path, "live")

    if not os.path.exists(live_path):
        os.makedirs(live_path)
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)

    certs_permissions_config = config.get("acme", {}).get("certs_permissions", {})
    fix_permissions(certs_permissions_config, live_path)
    fix_permissions(certs_permissions_config, archive_path)


def digest(path):
    if not os.path.exists(path):
        LOGGER.error(
            "Configuration file %s does not exist.", os.path.abspath(path),
        )

        return None

    with open(path, "rb") as file_h:
        config_data = file_h.read()

    md5 = hashlib.md5()
    md5.update(config_data)
    return md5.digest()
