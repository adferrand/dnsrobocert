#!/bin/sh

echo "Launch renew test"

hooks=""
if [ "$PFX_EXPORT" = "true" ]; then
    hooks="$hooks --deploy-hook pfx-export-hook.sh"
fi

certbot renew -n $hooks