#!/bin/sh
set -e

cd /etc/letsencrypt
delegated_per_domain=""
if [ -f /etc/letsencrypt/domains.conf ]; then
	delegated=`cat domains.conf | grep "^$CERTBOT_DOMAIN" | grep -E -o 'delegated=.*' | sed -E 's/delegated=([^[:space:]]+)[[:space:]].*/\1/'`
	delegated_per_domain="--delegated=$delegated"
fi

lexicon $LEXICON_OPTIONS $delegated_per_domain $LEXICON_PROVIDER $LEXICON_PROVIDER_OPTIONS create $CERTBOT_DOMAIN TXT --name="_acme-challenge.$CERTBOT_DOMAIN." --content="$CERTBOT_VALIDATION" --ttl="$LEXICON_TTL" --output=QUIET

if [ "$LEXICON_MAX_CHECKS" -gt 0 ]; then
  tries=0
  while : ; do
    tries=$((tries + 1))
    if [ "$tries" -gt "$LEXICON_MAX_CHECKS" ]; then
      echo "The challenge was not propagated after the maximum tries of $LEXICON_MAX_CHECKS"
      exit 1
    fi

    echo "Wait $LEXICON_SLEEP_TIME seconds before checking that TXT _acme-challenge.$CERTBOT_DOMAIN has the expected value (try $tries/$LEXICON_MAX_CHECKS)"
    sleep "$LEXICON_SLEEP_TIME"

    set +e
    dig +short TXT "_acme-challenge.$CERTBOT_DOMAIN" | grep -w "\"$CERTBOT_VALIDATION\"" > /dev/null 2>&1
    hasEntry=$?
    set -e

    if [ $hasEntry -ne 0 ]; then
      echo "TXT _acme-challenge.$CERTBOT_DOMAIN did not have the expected token value (try $tries/$LEXICON_MAX_CHECKS)"
      continue 1
    fi

    echo "TXT _acme-challenge.$CERTBOT_DOMAIN has the expected token value (try $tries/$LEXICON_MAX_CHECKS)"
    break
  done
else
  echo "Wait $LEXICON_SLEEP_TIME seconds to let TXT _acme-challenge.$CERTBOT_DOMAIN entry be propagated"
  sleep "$LEXICON_SLEEP_TIME"
fi
