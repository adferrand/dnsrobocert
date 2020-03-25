FROM alpine:3.11

ENV CONFIG_PATH /etc/dnsrobocert/config.yml
ENV CERTS_PATH /etc/letsencrypt

RUN sed -i -e 's/v[[:digit:]]\..*\//edge\//g' /etc/apk/repositories \
&& apk add --no-cache py3-pip py3-cryptography py3-lxml py3-future py3-zope-proxy \
&& pip3 install dnsrobocert==3.0.2 \
&& mkdir -p /etc/dnsrobocert /etc/letsencrypt

COPY docker/run.sh /run.sh
RUN chmod +x run.sh

CMD ["/run.sh"]
