#!/bin/sh

if [ -n "$TIMEZONE" ]
then
  echo "Waiting for DNS"
  ping -c1 -W60 google.com || ping -c1 -W60 www.google.com
  apk add --no-cache tzdata
  if [ -f /usr/share/zoneinfo/"$TIMEZONE" ]
  then
    echo "Setting timezone to $TIMEZONE"
    cp /usr/share/zoneinfo/"$TIMEZONE" /etc/localtime
    echo "$TIMEZONE" > /etc/timezone
  else
    echo "$TIMEZONE does not exist"
  fi
  apk del tzdata
fi

# Inhibit config.yml creation if legacy config is detected
# to avoid skipping this legacy config processing.
if [ ! -f "/etc/letsencrypt/domains.conf" ]; then
  if [ ! -f "${CONFIG_PATH}" ]; then
      echo "draft: true" >> "${CONFIG_PATH}"
  fi
fi

export PATH="${HOME}/.local/bin:${PATH}"
exec dnsrobocert -c "${CONFIG_PATH}" -d "${CERTS_PATH}"
