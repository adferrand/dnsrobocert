#!/bin/sh

echo "Launch renew test"
certbot renew -n --deploy-hook deploy-hook.sh