#!/usr/bin/env python3
import glob
import os
import re
import shutil
import subprocess
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
WHEELS_DIR = os.path.join(ROOT_DIR, "wheels")

TARGETS = ["cryptography", "cffi", "lxml"]
ARCHS = ["linux/amd64", "linux/386", "linux/arm64", "linux/arm/v7", "linux/arm/v6", "linux/ppc64le", "linux/s390x"]
PYTHON_VERSION = 3.8
ALPINE_VERSION = 3.12

DOCKERFILE = f"""
FROM docker.io/python:{PYTHON_VERSION}-alpine{ALPINE_VERSION}

RUN apk --no-cache add build-base openssl-dev libxml2-dev libxslt-dev libffi-dev zlib-dev
 
COPY requirements.txt .
RUN mkdir -p /precompiled-wheels/$(uname -m) \
 && pip wheel --no-deps -r requirements.txt -w /precompiled-wheels

CMD ["cp", "-ra", "/precompiled-wheels", "/wheels"]
"""


def main():
    with tempfile.TemporaryDirectory() as workspace:
        output = subprocess.check_output(["poetry", "export", "--format", "requirements.txt", "--without-hashes"],
                                         universal_newlines=True)
        requirements = []
        for entry in output.split("\n"):
            if re.match(rf"^({'|'.join(TARGETS)}).*$", entry):
                requirements.append(entry)

        requirements_path = os.path.join(workspace, "requirements.txt")
        with open(requirements_path, "w+") as file_h:
            for requirement in requirements:
                print(requirement, file=file_h)

        with open(os.path.join(workspace, "Dockerfile"), "w") as file_h:
            file_h.write(DOCKERFILE)

        subprocess.check_call(["docker", "run", "--rm", "--privileged",
                               "docker.io/multiarch/qemu-user-static", "--reset", "-p", "yes"])

        subprocess.check_call(["docker", "buildx", "create", "--use"])

        subprocess.check_call(["docker", "buildx", "build", "--platform", ",".join(ARCHS),
                               f"--output=type=local,dest={workspace}", "--tag", "dnsrobocert-wheels", workspace])

        if os.path.exists(WHEELS_DIR):
            shutil.rmtree(WHEELS_DIR)

        for arch in ARCHS:
            arch = arch.replace("/", "_")
            shutil.copytree(os.path.join(workspace, arch, "precompiled-wheels"), WHEELS_DIR, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
