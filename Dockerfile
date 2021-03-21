ARG BUILDER_ARCH=amd64
FROM docker.io/${BUILDER_ARCH}/python:3-slim AS constraints

COPY src poetry.lock poetry.toml pyproject.toml README.rst /tmp/dnsrobocert/

RUN python3 -m pip install --user poetry --no-warn-script-location \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/constraints.txt \
 && python3 -m poetry build -f wheel

FROM docker.io/python:3.9.2-alpine3.13

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/
COPY wheels /tmp/dnsrobocert/precompiled-wheels

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN apk add --no-cache docker-cli bash \
 && python -m pip install --upgrade pip wheel \
 # Under i686 arch emulated with QEMU, uname -m still returns x86_64. Workaround by retrying explicitly with i686 wheels.
 && (pip install --no-deps /tmp/dnsrobocert/precompiled-wheels/*_$(uname -m).whl || pip install --no-deps /tmp/dnsrobocert/precompiled-wheels/*_i686.whl) \
 && pip install -c /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
