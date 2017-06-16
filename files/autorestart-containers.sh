#!/bin/sh

domain=$1
containers=$2
IFS=' ,'

if [ ! -S /var/run/docker.sock ]; then
    echo "ERROR: /var/run/docker.sock is missing."
    exit 1
fi

if [ ! -f /etc/letsencrypt/live/$domain/cert.pem ]; then
    echo "ERROR: /etc/letsencrypt/live/$domain/cert.pem is missing."
    exit 1
fi

while true; do
    inotifywait -e modify /etc/letsencrypt/live/$domain/cert.pem

    echo ">>> Restarting dockers $containers because certificate for $domain has been modified."
    for container in $containers; do
        docker restart $container
    done
done