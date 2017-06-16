#!/bin/sh

# Ensure domain.conf exists
touch /etc/letsencrypt/domains.conf

# Load crontab and incrontab
crontab /etc/crontab

# Update TLDs
tldextract --update

# Start supervisord
/usr/bin/supervisord -c /etc/supervisord.conf