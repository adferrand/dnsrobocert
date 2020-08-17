ARG BUILDER_ARCH=amd64
FROM docker.io/${BUILDER_ARCH}/python:3-slim-buster AS constraints

COPY . /tmp/dnsrobocert

RUN python3 -m pip install --user poetry --no-warn-script-location \
 && python3 -m pip install --user poetry --no-warn-script-location \
 && cd /tmp/dnsrobocert \
 && python3 -m poetry export --format requirements.txt --without-hashes > /tmp/dnsrobocert/requirements.txt \
 && python3 -m poetry build -f wheel

FROM docker.io/alpine:3.11 AS wheels

COPY --from=constraints /tmp/dnsrobocert/requirements.txt /tmp/dnsrobocert/
COPY --from=constraints /tmp/dnsrobocert/dist/*.whl /tmp/dnsrobocert/wheels/

RUN apk add --no-cache gcc python3-dev musl-dev libffi-dev libxml2-dev libxslt-dev openssl-dev \
 && python3 -m pip install wheel \
 && python3 -m pip wheel -r /tmp/dnsrobocert/requirements.txt -w /tmp/dnsrobocert/wheels

FROM docker.io/alpine:3.11

COPY --from=wheels /tmp/dnsrobocert/wheels /tmp/dnsrobocert/wheels

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN apk add --no-cache \
        py3-pip \
        # Hooks dependencies
        docker-cli \
        bash \
 && python3 -m pip install /tmp/dnsrobocert/wheels/*.whl \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
