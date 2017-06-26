FROM python:alpine3.6
MAINTAINER Adrien Ferrand <ferrand.ad@gmail.com>

ENV LEXICON_VERSION 2.1.8
ENV CERTBOT_VERSION 0.15.0

ENV LETSENCRYPT_STAGING false
ENV LETSENCRYPT_USER_MAIL noreply@example.com
ENV LEXICON_PROVIDER cloudflare

# Install dependencies
RUN apk --no-cache --update add rsyslog git openssl libffi inotify-tools supervisor docker \
&& apk --no-cache --update --virtual build-dependencies add libffi-dev openssl-dev python-dev build-base \
# Install certbot
&& pip install certbot \
# Install lexicon
&& pip install requests[security] "dns-lexicon==$LEXICON_VERSION" \
# Prepare for first start, and clean
&& mkdir -p /var/lib/letsencrypt/hooks \
&& mkdir -p /etc/supervisord.d \
&& apk del build-dependencies

# Copy configuration files
COPY files/run.sh /scripts/run.sh
COPY files/watch-domains.sh /scripts/watch-domains.sh
COPY files/autorestart-containers.sh /scripts/autorestart-containers.sh
COPY files/crontab /etc/crontab
COPY files/supervisord.conf /etc/supervisord.conf
COPY files/authenticator.sh /var/lib/letsencrypt/hooks/authenticator.sh
COPY files/cleanup.sh /var/lib/letsencrypt/hooks/cleanup.sh

VOLUME ["/etc/letsencrypt"]

CMD ["/scripts/run.sh"]
