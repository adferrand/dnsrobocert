FROM python:3.7-alpine3.10
LABEL maintainer="Adrien Ferrand <ferrand.ad@gmail.com>"

# Scripts in /scripts are required to be in the PATH to run properly as certbot's hooks
ENV PATH /scripts:$PATH

# Versioning
ENV LEXICON_VERSION 3.3.8
ENV CERTBOT_VERSION 0.39.0

# Install dependencies, certbot, lexicon, prepare for first start and clean
RUN apk --no-cache --update add rsyslog git libffi libxml2 libxslt libstdc++ openssl docker ethtool tzdata bash bind-tools \
 && apk --no-cache --update --virtual build-dependencies add libffi-dev libxml2-dev libxslt-dev openssl-dev build-base linux-headers \
 && pip install --no-cache-dir "certbot==$CERTBOT_VERSION" \
 && pip install --no-cache-dir "dns-lexicon[full]==$LEXICON_VERSION" \
 && pip install --no-cache-dir circus \
 && mkdir -p /var/letsencrypt \
 && touch /var/letsencrypt/domains.conf \
 && mkdir -p /var/lib/letsencrypt/hooks \
 && mkdir -p /etc/circus.d \
 && apk del build-dependencies

# Let's Encrypt configuration
ENV LETSENCRYPT_STAGING=false \
    LETSENCRYPT_USER_MAIL=noreply@example.com \
    LETSENCRYPT_ACME_V1=false \
    LETSENCRYPT_SKIP_REGISTER=false

# Lexicon configuration
ENV LEXICON_OPTIONS="" \
    LEXICON_PROVIDER=cloudflare \
    LEXICON_PROVIDER_OPTIONS="" \
    LEXICON_SLEEP_TIME=30 \
    LEXICON_MAX_CHECKS=3

# Container specific configuration
ENV TZ=UTC \
    CRON_TIME_STRING="12 01,13 * * *" \
    PFX_EXPORT=false \
    PFX_EXPORT_PASSPHRASE="" \
    CERTS_DIRS_MODE=0750 \
    CERTS_FILES_MODE=0640 \
    CERTS_USER_OWNER=root \
    CERTS_GROUP_OWNER=root \
    DEPLOY_HOOK=""

# Container in cluster configuration (Swarm, Kubernetes ...)
ENV DOCKER_CLUSTER_PROVIDER none

# Copy scripts
COPY files/run.sh \
     files/watch-domains.sh \
     files/autorestart-containers.sh \
     files/autocmd-containers.sh \
     files/deploy-hook.sh \
     files/renew.sh /scripts/

COPY files/authenticator.sh \
     files/cleanup.sh /var/lib/letsencrypt/hooks/

# Copy configuration files
COPY files/circus.ini /etc/circus.ini
COPY files/letsencrypt-dns.ini /etc/circus.d/letsencrypt-dns.ini

RUN chmod +x /scripts/*

VOLUME ["/etc/letsencrypt"]

CMD ["/scripts/run.sh"]
