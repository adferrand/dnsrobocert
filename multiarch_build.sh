#!/bin/bash
# USAGE: ./multiarch_build.sh [TAG]

set -e

ARCHS="amd64 arm32v7 arm64v8"
QEMU_VERSION="v4.0.0-5"

TAG="${1:-latest}"

wget -q "https://github.com/multiarch/qemu-user-static/releases/download/${QEMU_VERSION}/qemu-arm-static" -O qemu-arm-static
chmod +x qemu-arm-static
docker run --rm --privileged multiarch/qemu-user-static:register --reset

for arch in $ARCHS; do
    cp -f Dockerfile "$arch.Dockerfile"
    if [[ "$arch" == arm* ]]; then
        sed -i "s/# ARG QEMU/ARG QEMU/g" "$arch.Dockerfile"
        sed -i "s/# COPY qemu/COPY qemu/g" "$arch.Dockerfile"
        additional_arg="--build-arg QEMU_ARCH=arm"
    fi
    docker build --build-arg "BUILD_ARCH=$arch" $additional_arg -t "adferrand/letsencrypt-dns:$TAG-$arch" -f "$arch.Dockerfile" .
done
