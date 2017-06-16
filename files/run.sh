#!/bin/sh

# Ensure domain.conf exists
touch /etc/letsencrypt/domains.conf

# Load crontab and incrontab
crontab /etc/crontab

# Start supervisord
/usr/bin/supervisord -c /etc/supervisord.conf