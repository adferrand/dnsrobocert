ARG BUILDER_ARCH=amd64
FROM docker.io/${BUILDER_ARCH}/python:3-slim AS constraints

COPY src poetry.lock poetry.toml pyproject.toml README.rst /tmp/dnsrobocert/

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       curl \
       gcc \
       python3-dev \
       libffi-dev \
 && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - \
 && rm -rf /var/lib/apt/lists/*

RUN cd /tmp/dnsrobocert \
 && /root/.local/bin/poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/constraints.txt \
 && /root/.local/bin/poetry build -f wheel

FROM docker.io/python:3.9.10-slim

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

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
