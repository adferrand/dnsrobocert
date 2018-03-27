FROM python:alpine3.7
LABEL maintainer="Adrien Ferrand <ferrand.ad@gmail.com>"

# Scripts in /scripts are required to be in the PATH to run properly as certbot's hooks
ENV PATH /scripts:$PATH

# Versioning
ENV LEXICON_VERSION 2.2.1
ENV CERTBOT_VERSION 0.22.2

# Let's Encrypt configuration
ENV LETSENCRYPT_STAGING false
ENV LETSENCRYPT_USER_MAIL noreply@example.com

# Lexicon configuration
ENV LEXICON_PROVIDER cloudflare

# Container specific configuration
ENV PFX_EXPORT false
ENV PFX_EXPORT_PASSPHRASE ""
ENV CERTS_DIRS_MODE 0750
ENV CERTS_FILES_MODE 0640
ENV CERTS_USER_OWNER root
ENV CERTS_GROUP_OWNER root

# Install dependencies, certbot, lexicon, prepare for first start and clean
RUN apk --no-cache --update add rsyslog git openssl libffi supervisor docker \
&& apk --no-cache --update --virtual build-dependencies add libffi-dev openssl-dev python-dev build-base \
&& pip install "certbot==$CERTBOT_VERSION" \
&& pip install "dns-lexicon==$LEXICON_VERSION" \
&& pip install "dns-lexicon[namecheap]==$LEXICON_VERSION" \
&& pip install "dns-lexicon[route53]==$LEXICON_VERSION" \
&& pip install "dns-lexicon[softlayer]==$LEXICON_VERSION" \
&& pip install "dns-lexicon[transip]==$LEXICON_VERSION" \
&& mkdir -p /var/lib/letsencrypt/hooks \
&& mkdir -p /etc/supervisord.d \
&& apk del build-dependencies

# Copy configuration files
COPY files/run.sh /scripts/run.sh
COPY files/watch-domains.sh /scripts/watch-domains.sh
COPY files/autorestart-containers.sh /scripts/autorestart-containers.sh
COPY files/autocmd-containers.sh /scripts/autocmd-containers.sh
COPY files/crontab /etc/crontab
COPY files/supervisord.conf /etc/supervisord.conf
COPY files/authenticator.sh /var/lib/letsencrypt/hooks/authenticator.sh
COPY files/cleanup.sh /var/lib/letsencrypt/hooks/cleanup.sh
COPY files/deploy-hook.sh /scripts/deploy-hook.sh
COPY files/renew.sh /scripts/renew.sh

RUN chmod +x /scripts/*

VOLUME ["/etc/letsencrypt"]

CMD ["/scripts/run.sh"]
