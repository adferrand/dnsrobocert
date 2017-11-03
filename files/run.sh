#!/bin/sh

# Ensure domain.conf exists
touch /etc/letsencrypt/domains.conf

# Ensure certs folders exist, and with correct permissions
mkdir -p /etc/letsencrypt/live /etc/letsencrypt/archive
if [ "$CERTS_DIR_WORLD_READABLE" = "true" ]; then
    chmod 0755 /etc/letsencrypt/live /etc/letsencrypt/archive
elif [ "$CERTS_DIR_GROUP_READABLE" = "true" ]; then
    chmod 0750 /etc/letsencrypt/live /etc/letsencrypt/archive
else
    chmod 0700 /etc/letsencrypt/live /etc/letsencrypt/archive
fi

# Synchronize certs files mode and user/group permissions
chmod $CERTS_DIRS_MODE $(find /etc/letsencrypt/live /etc/letsencrypt/archive -type d)
chmod $CERTS_FILES_MODE $(find /etc/letsencrypt/live /etc/letsencrypt/archive -type f)
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
