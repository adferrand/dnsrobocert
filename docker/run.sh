#!/bin/bash

# Inhibit config.yml creation if legacy config is detected
# to avoid skipping this legacy config processing.
if [ ! -f "/etc/letsencrypt/domains.conf" ]; then
  if [ ! -f "${CONFIG_PATH}" ]; then
      echo "draft: true" >> "${CONFIG_PATH}"
  fi
fi

export PATH="${HOME}/.local/bin:${PATH}"
exec dnsrobocert -c "${CONFIG_PATH}" -d "${CERTS_PATH}"
