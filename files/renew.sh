#!/bin/sh

echo "Launch renew test"
certbot renew \
    -n \
    --config-dir /etc/letsencrypt --logs-dir /etc/letsencrypt/logs --work-dir /etc/letsencrypt/work \
    --deploy-hook deploy-hook.sh
