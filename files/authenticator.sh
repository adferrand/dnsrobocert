#!/bin/sh
set -e

lexicon $LEXICON_PROVIDER create $CERTBOT_DOMAIN TXT --name="_acme-challenge.$CERTBOT_DOMAIN." --content="$CERTBOT_VALIDATION"

sleep 30
