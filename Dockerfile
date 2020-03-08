FROM docker.io/python:3.8.2-slim-buster

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

COPY src pyproject.toml poetry.toml poetry.lock README.md /tmp/dnsrobocert/

RUN python3 -m pip install --user pipx \
 && python3 -m pipx install --verbose /tmp/dnsrobocert \
 && mkdir -p /etc/dnsrobocert /etc/letsencrypt \
 && rm -rf /tmp/dnsrobocert

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
