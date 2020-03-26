FROM docker.io/python:3.8.2-slim-buster AS constraints

COPY pyproject.toml poetry.toml poetry.lock /tmp/dnsrobocert/

RUN python3 -m pip install --user poetry \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert-constraints.txt \
 && cat /tmp/dnsrobocert-constraints.txt

FROM alpine:3.11

COPY --from=constraints /tmp/dnsrobocert-constraints.txt /tmp/dnsrobocert-constraints.txt

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN sed -i -e 's/v[[:digit:]]\..*\//edge\//g' /etc/apk/repositories \
&& apk add --no-cache \
    # Core dependencies
    py3-pip \
    py3-cryptography \
    py3-lxml \
    py3-future \
    py3-zope-proxy \
    # Hooks dependencies
    docker-cli \
    bash \
&& pip3 install -c /tmp/dnsrobocert-constraints.txt dnsrobocert==3.0.2 \
&& mkdir -p /etc/dnsrobocert /etc/letsencrypt

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
