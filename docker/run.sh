#!/bin/bash

if [ ! -f "${CONFIG_PATH}" ]; then
    echo "draft: true" >> "${CONFIG_PATH}"
fi

export PATH="${HOME}/.local/bin:${PATH}"
exec dnsrobocert -c "${CONFIG_PATH}" -d "${CERTS_PATH}"
