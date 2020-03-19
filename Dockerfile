FROM docker.io/python:3.8.2-slim-buster AS constraints

COPY pyproject.toml poetry.toml poetry.lock /tmp/dnsrobocert/

RUN python3 -m pip install --user poetry \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/constraints.txt

FROM docker.io/python:3.8.2-slim-buster

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/constraints.txt
COPY src pyproject.toml poetry.toml README.rst /tmp/dnsrobocert/

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg2 \
        software-properties-common \
 && curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
 && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
 && apt-get update \
 && apt-get -y --no-install-recommends install docker-ce-cli \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --user pipx \
 && python3 -m pipx install --verbose --pip-args "-c /tmp/dnsrobocert/constraints.txt" /tmp/dnsrobocert \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
