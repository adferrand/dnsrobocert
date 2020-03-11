#!/bin/sh
set -e

cd /etc/letsencrypt

delegated_per_domain=""
if [ -f /etc/letsencrypt/domains.conf ]; then
	delegated=`cat domains.conf | grep "^$CERTBOT_DOMAIN" | grep -E -o 'delegated=.*' | sed -E 's/delegated=([^[:space:]]+)[[:space:]].*/\1/'`
	delegated_per_domain="--delegated=$delegated"
fi

lexicon $LEXICON_OPTIONS $delegated_per_domain $LEXICON_PROVIDER $LEXICON_PROVIDER_OPTIONS delete $CERTBOT_DOMAIN TXT --name="_acme-challenge.$CERTBOT_DOMAIN." --content="$CERTBOT_VALIDATION" --output=QUIET
