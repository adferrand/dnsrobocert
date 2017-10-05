#!/bin/sh

openssl pkcs12 -export -out "$RENEWED_LINEAGE/cert.pfx" -inkey "$RENEWED_LINEAGE/privkey.pem" -in "$RENEWED_LINEAGE/cert.pem" -certfile "$RENEWED_LINEAGE/chain.pem"