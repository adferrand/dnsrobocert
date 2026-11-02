#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
WHEELS_DIR = os.path.join(ROOT_DIR, "wheels")
BUILD_JSON = os.path.join(WHEELS_DIR, "build.json")

TARGETS = ["cryptography", "cffi", "lxml"]
ARCHS = [
    "linux/amd64",
    "linux/arm64",
    "linux/arm/v7",
    "linux/ppc64le",
]
PYTHON_VERSION = "3.9"
ALPINE_VERSION = "3.13"

# We need to set CRYPTOGRAPHY_DONT_BUILD_RUST for now because Rust is not working properly
# for emulated 32 bits architecture with QEMU (eg. armv7) on 64 bits architecture (eg. amd64).
# See https://github.com/docker/buildx/issues/395
DOCKERFILE = f"""
FROM docker.io/python:{PYTHON_VERSION}-alpine{ALPINE_VERSION}

RUN apk --no-cache add \
        build-base \
        openssl-dev \
        libxml2-dev \
        libxslt-dev \
        libffi-dev \
        zlib-dev \
        cargo

COPY requirements.txt .

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN python -m pip wheel --no-binary :all: --no-deps -r requirements.txt -w /precompiled-wheels

CMD ["cp", "-ra", "/precompiled-wheels", "/wheels"]
"""


def _need_rebuild(requirements):
    if not os.path.exists(BUILD_JSON):
        return True

    with open(BUILD_JSON) as file_h:
        descriptor = json.loads(file_h.read())

    if descriptor.get("python_version") != PYTHON_VERSION:
        return True

    if descriptor.get("alpine_version") != ALPINE_VERSION:
        return True

    if descriptor.get("architectures") != ARCHS:
        return True

    for requirement in requirements:
        package, version = _extract_req(requirement)
        if descriptor.get("packages").get(package) != version:
            return True

    return False


def _extract_req(requirement):
    match = re.match(r"^(.*)==(.*?)(?:$|;\w*.*$)", requirement)
    return match.group(1), match.group(2)


def main():
    with tempfile.TemporaryDirectory() as workspace:
        output = subprocess.check_output(
            ["poetry", "export", "--format", "requirements.txt", "--without-hashes"],
            universal_newlines=True,
        )
        requirements = []
        for entry in output.split("\n"):
            if re.match(rf"^({'|'.join(TARGETS)}).*$", entry):
                requirements.append(entry)

        if _need_rebuild(requirements):
            print("Wheels are out-of-date and need to be rebuilt.")
        else:
            print("Wheels are up-to-date, no rebuild is needed.")
            return

        requirements_path = os.path.join(workspace, "requirements.txt")
        with open(requirements_path, "w+") as file_h:
            for requirement in requirements:
                print(requirement, file=file_h)

        with open(os.path.join(workspace, "Dockerfile"), "w") as file_h:
            file_h.write(DOCKERFILE)

        subprocess.check_call(
            [
                "docker",
                "run",
                "--rm",
                "--privileged",
                "docker.io/multiarch/qemu-user-static",
                "--reset",
                "-p",
                "yes",
            ]
        )

        subprocess.check_call(["docker", "buildx", "create", "--use"])

        subprocess.check_call(
            [
                "docker",
                "buildx",
                "build",
                "--platform",
                ",".join(ARCHS),
                f"--output=type=local,dest={workspace}",
                "--tag",
                "dnsrobocert-wheels",
                workspace,
            ]
        )

        if os.path.exists(WHEELS_DIR):
            shutil.rmtree(WHEELS_DIR)
        os.makedirs(WHEELS_DIR, exist_ok=True)

        for arch in ARCHS:
            arch = arch.replace("/", "_")
            shutil.copytree(
                os.path.join(workspace, arch, "precompiled-wheels"),
                WHEELS_DIR,
                dirs_exist_ok=True,
            )

        extracted_requirements = [
            _extract_req(requirement) for requirement in requirements
        ]
        build_data = {
            "python_version": PYTHON_VERSION,
            "alpine_version": ALPINE_VERSION,
            "architectures": ARCHS,
            "packages": {
                package: version for package, version in extracted_requirements
            },
        }

        with open(BUILD_JSON, "w") as file_h:
            file_h.write(json.dumps(build_data))


if __name__ == "__main__":
    main()
