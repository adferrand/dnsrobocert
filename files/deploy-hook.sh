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

# Synchronize mode for new certificate files
chmod $CERTS_FILES_MODE $RENEWED_LINEAGE/*