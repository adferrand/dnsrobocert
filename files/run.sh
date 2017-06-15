#!/bin/sh

# Ensure domain.txt exists
touch /etc/letsencrypt/domains.txt

# Load crontab and incrontab
crontab /etc/crontab

# Start supervisord
/usr/bin/supervisord -c /etc/supervisord.conf