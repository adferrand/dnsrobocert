#!/bin/sh

# Construct PFX file for new cert if needed
if [ "$PFX_EXPORT" = "true" ]; then
    openssl pkcs12 -export \
        -out $RENEWED_LINEAGE/cert.pfx \
        -inkey $RENEWED_LINEAGE/privkey.pem \
        -in $RENEWED_LINEAGE/cert.pem \
        -certfile $RENEWED_LINEAGE/chain.pem \
        -password pass:$PFX_EXPORT_PASSPHRASE
fi

# Synchronize mode and user/group for new certificate files
find $RENEWED_LINEAGE ${RENEWED_LINEAGE/live/archive} -type d -exec chmod "$CERTS_DIRS_MODE" {} +
find $RENEWED_LINEAGE ${RENEWED_LINEAGE/live/archive} -type f -exec chmod "$CERTS_FILES_MODE" {} +
chown -R $CERTS_USER_OWNER:$CERTS_GROUP_OWNER $RENEWED_LINEAGE ${RENEWED_LINEAGE/live/archive}
