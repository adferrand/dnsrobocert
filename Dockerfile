FROM docker.io/python:3.15.0-slim AS constraints

COPY src uv.lock pyproject.toml README.rst /tmp/dnsrobocert/

RUN pip install --no-cache-dir uv==0.13.6 \
 && cd /tmp/dnsrobocert \
 && uv export --no-emit-project --no-hashes > /tmp/dnsrobocert/constraints.txt \
 # Pin some packages on armv7l arch to latest available and compatible versions from piwheels.
 && [ "$(uname -m)" != "armv7l" ] || sed -i 's/cryptography==.*/cryptography==49.0.0/' /tmp/dnsrobocert/constraints.txt \
 && [ "$(uname -m)" != "armv7l" ] || sed -i 's/lxml==.*/lxml==6.1.1/' /tmp/dnsrobocert/constraints.txt \
 && uv build

FROM docker.io/python:3.15.0-slim

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/

ENV CONFIG_PATH=/etc/dnsrobocert/config.yml
ENV CERTS_PATH=/etc/letsencrypt

RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       bash \
       libxslt1.1 \
       podman \
       docker-cli \
 && if [ "$(uname -m)" = "armv7l" ]; then export PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple; fi \
 && python3 -m pip install --no-cache-dir -c /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert /var/lib/apt/lists/*

# For retro-compatibility purpose
RUN mkdir -p /opt/dnsrobocert/bin \
 && ln -s /usr/local/bin/python /opt/dnsrobocert/bin/python

COPY docker/run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
