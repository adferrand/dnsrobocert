FROM docker.io/ubuntu:24.04 AS constraints

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY src uv.lock pyproject.toml README.rst /tmp/dnsrobocert/

RUN cd /tmp/dnsrobocert \
 && uv python install \
 && uv export --no-emit-project --no-hashes > /tmp/dnsrobocert/constraints.txt \
 && uv build

FROM docker.io/python:3.13.3-slim

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

# Pin cryptography on armv7l arch to latest available and compatible version from pipwheels: 41.0.5
RUN [ "$(uname -m)" = "armv7l" ] && sed -i 's/cryptography==.*/cryptography==41.0.5/' /tmp/dnsrobocert/constraints.txt || true

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       curl \
       bash \
       libxslt1.1 \
       podman \
 && curl -fsSL get.docker.com | sh \
 && PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple python3 -m pip install -c /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert /var/lib/apt/lists/*

# For retro-compatibility purpose
RUN mkdir -p /opt/dnsrobocert/bin \
 && ln -s /usr/local/bin/python /opt/dnsrobocert/bin/python

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
