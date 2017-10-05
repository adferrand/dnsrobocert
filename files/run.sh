#!/bin/sh

# Ensure domain.conf exists
touch /etc/letsencrypt/domains.conf

# Load crontab and incrontab
crontab /etc/crontab

# Update TLDs
tldextract --update

# Synchronize additional certificates formats
if [ "$PFX_EXPORT" = "true" ]; then
    for i in `ls /etc/letsencrypt/live`
    do
        openssl pkcs12 -export \
            -out "/etc/letsencrypt/live/$i/cert.pfx" \
            -inkey "/etc/letsencrypt/live/$i/privkey.pem" \
            -in "/etc/letsencrypt/live/$i/cert.pem" \
            -certfile "/etc/letsencrypt/live/$i/chain.pem" \
            -password pass:$PFX_EXPORT_PASSPHRASE
    done
fi

# Start supervisord
/usr/bin/supervisord -c /etc/supervisord.conf