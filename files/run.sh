#!/bin/sh

# Ensure certs folders exist, and with correct permissions
mkdir -p /etc/letsencrypt/live /etc/letsencrypt/archive

# Synchronize certs files mode and user/group permissions
find /etc/letsencrypt/live /etc/letsencrypt/archive -type d -exec chmod "$CERTS_DIRS_MODE" {} +
find /etc/letsencrypt/live /etc/letsencrypt/archive -type f -exec chmod "$CERTS_FILES_MODE" {} +
chown -R $CERTS_USER_OWNER:$CERTS_GROUP_OWNER /etc/letsencrypt/live /etc/letsencrypt/archive

# Load crontab
crontab /etc/crontab

# Update TLDs
tldextract --update

# Synchronize additional certificates formats
if [ "$PFX_EXPORT" = "true" ]; then
    for i in `ls /etc/letsencrypt/live`
    do
        openssl pkcs12 -export \
            -out /etc/letsencrypt/live/$i/cert.pfx \
            -inkey /etc/letsencrypt/live/$i/privkey.pem \
            -in /etc/letsencrypt/live/$i/cert.pem \
            -certfile /etc/letsencrypt/live/$i/chain.pem \
            -password pass:$PFX_EXPORT_PASSPHRASE
    done
fi

# Start supervisord
/usr/bin/supervisord -c /etc/supervisord.conf
