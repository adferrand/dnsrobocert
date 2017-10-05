#!/bin/sh

hooks=""

if [ "$EXPORT_TO_PFX" = "true"]; then
    hooks="$hooks --deploy-hook /scripts/pfx-export-hook.sh"
fi

certbot renew -n $hooks