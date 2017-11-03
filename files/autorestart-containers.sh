#!/bin/sh

domain=$1
containers=$2

if [ ! -S /var/run/docker.sock ]; then
    echo "ERROR: /var/run/docker.sock socket is missing."
    exit 1
fi

if [ ! -d /etc/letsencrypt/archive/$domain ]; then
    echo "ERROR: /etc/letsencrypt/archive/$domain directory is missing."
    exit 1
fi

# Load hash of the certificate
current_hash=`md5sum /etc/letsencrypt/live/$domain/cert.pem | awk '{ print $1 }'`
while true; do
    new_hash=`md5sum /etc/letsencrypt/live/$domain/cert.pem | awk '{ print $1 }'`

    if [ "$current_hash" != "$new_hash" ]; then
        echo ">>> Restarting dockers $containers because certificate for $domain has been modified."
        IFS=','; for container in $containers; do
            docker restart $container
        done; unset IFS

        # Keep new hash version
        current_hash="$new_hash"
    fi

    # Wait 1s for next iteration
    sleep 1
done
