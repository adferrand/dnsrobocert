ARG BUILDER_ARCH=amd64
FROM docker.io/${BUILDER_ARCH}/python:3-slim AS constraints

COPY src poetry.lock poetry.toml pyproject.toml README.rst /tmp/dnsrobocert/

RUN python3 -m pip install --user poetry --no-warn-script-location \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/constraints.txt \
 && python3 -m poetry build -f wheel

FROM docker.io/python:3.9.6-slim

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        bash \
        libxslt1.1 \
 && curl -fsSL get.docker.com && sh \
 && python -m pip install --upgrade pip wheel \
 && PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple pip install -c /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert /var/lib/apt/lists/*

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
