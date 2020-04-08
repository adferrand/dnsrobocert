ARG BUILDER_ARCH=amd64
FROM docker.io/${BUILDER_ARCH}/python:3-slim-buster AS constraints

COPY . /tmp/dnsrobocert

RUN python3 -m pip install --user poetry --no-warn-script-location \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/constraints.txt \
 && python3 -m poetry build -f wheel

FROM docker.io/alpine:3.11

COPY --from=constraints /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN sed -i -e 's/v[[:digit:]]\..*\//edge\//g' /etc/apk/repositories \
 && apk add --no-cache \
        py3-pip \
        # Core dependencies that would need a compilation
        "py3-cryptography=~$(grep cryptography /tmp/dnsrobocert/constraints.txt | sed 's/.*==//g')" \
        "py3-lxml=~$(grep lxml /tmp/dnsrobocert/constraints.txt | sed 's/.*==//g')" \
        # Hooks dependencies
        docker-cli \
        bash \
 && pip3 install -c /tmp/dnsrobocert/constraints.txt /tmp/dnsrobocert/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
