#!/bin/sh
set -e

cd /etc/letsencrypt
lexicon $LEXICON_OPTIONS $LEXICON_PROVIDER $LEXICON_PROVIDER_OPTIONS create $CERTBOT_DOMAIN TXT --name="_acme-challenge.$CERTBOT_DOMAIN." --content="$CERTBOT_VALIDATION"

if [ -z "$LEXICON_NAMESERVER" ]; then
	NS=$(dig +short NS $CERTBOT_DOMAIN)
else
	NS=$(dig +short NS $CERTBOT_DOMAIN @$LEXICON_NAMESERVER)
fi

while : ; do
  for ns in $NS
  do
    result=$(dig +short TXT $CERTBOT_DOMAIN @$ns)
	set +e
    dig +short TXT _acme-challenge.$CERTBOT_DOMAIN @$ns | grep -w "\"$CERTBOT_VALIDATION\"" > /dev/null 2>&1
    hasEntry=$?
	set -e

    if [ $hasEntry -ne 0 ]; then
      echo "NS $ns did not have expected value, trying again in $LEXICON_SLEEP_TIME seconds"
      sleep $LEXICON_SLEEP_TIME
      continue 2
    fi
  done
  break
done
