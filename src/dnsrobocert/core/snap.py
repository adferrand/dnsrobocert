import argparse
import logging
import os
import os.path
import socket
import sys

import coloredlogs
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection
from urllib3.connectionpool import HTTPConnectionPool

LOGGER = logging.getLogger(__name__)
coloredlogs.install(logger=LOGGER)


class _SnapdConnection(HTTPConnection):
    def __init__(self):
        super(_SnapdConnection, self).__init__("localhost")
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/run/snapd.socket")


class _SnapdConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super(_SnapdConnectionPool, self).__init__("localhost")

    def _new_conn(self):
        return _SnapdConnection()


class _SnapdAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return _SnapdConnectionPool()


def validate_snap_environment(args: argparse.Namespace):
    if not os.environ.get("SNAP"):
        return

    with Session() as session:
        session.mount("http://snapd/", _SnapdAdapter())

        response = session.get(
            "http://snapd/v2/connections?snap=certbot&interface=content"
        )
        response.raise_for_status()

    data = response.json()

    errors = []
    system_files_connection = [
        connection
        for connection in data.get("result", {}).get("established", [])
        if connection.get("interface") == "system-files"
    ]

    valid_paths = [os.environ.get("SNAP_REAL_HOME")]

    if system_files_connection:
        valid_paths.append("/etc")

    if not [
        path for path in valid_paths if os.path.abspath(args.config).startswith(path)
    ]:
        errors.append(f"Invalid --config value: {args.config}")

    if not [
        path for path in valid_paths if os.path.abspath(args.directory).startswith(path)
    ]:
        errors.append(f"Invalid --directory value: {args.config}")

    for error in errors:
        LOGGER.error(error)

    if errors:
        LOGGER.error(
            "The snap DNSroboCert can only use files and directories from the user HOME folder by default."
        )
        LOGGER.error(
            "You can also give to DNSroboCert an access to the /etc directory, by running the following "
            "command on a prompt with admin privileges:"
        )
        LOGGER.error("\tsnap connect dnsrobocert:etc")

        sys.exit(1)
