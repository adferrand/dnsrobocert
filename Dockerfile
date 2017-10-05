FROM python:alpine3.6
LABEL maintainer="Adrien Ferrand <ferrand.ad@gmail.com>"

# Scripts in /scripts are required to be in the PATH to run properly as certbot's hooks
ENV PATH /scripts:$PATH

# Versioning
ENV LEXICON_VERSION 2.1.10
ENV CERTBOT_VERSION 0.19.0

# Let's Encrypt configuration
ENV LETSENCRYPT_STAGING false
ENV LETSENCRYPT_USER_MAIL noreply@example.com
ENV LEXICON_PROVIDER cloudflare

ENV PFX_EXPORT false
ENV PFX_EXPORT_PASSPHRASE ""

# Install dependencies, certbot, lexicon, prepare for first start and clean
RUN apk --no-cache --update add rsyslog git openssl libffi supervisor docker \
&& apk --no-cache --update --virtual build-dependencies add libffi-dev openssl-dev python-dev build-base \
&& pip install "certbot==$CERTBOT_VERSION" \
&& pip install requests[security] "dns-lexicon==$LEXICON_VERSION" \
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
COPY files/pfx-export-hook.sh /scripts/pfx-export-hook.sh
COPY files/renew.sh /scripts/renew.sh

RUN chmod +x /scripts/*

VOLUME ["/etc/letsencrypt"]

CMD ["/scripts/run.sh"]
