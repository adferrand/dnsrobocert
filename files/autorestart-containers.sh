#!/bin/sh

domain=$1
containers=$2
IFS=' ,'

if [ ! -S /var/run/docker.sock ]; then
    echo "ERROR: /var/run/docker.sock socket is missing."
    exit 1
fi

if [ ! -d /etc/letsencrypt/archive/$domain ]; then
    echo "ERROR: /etc/letsencrypt/archive/$domain directory is missing."
    exit 1
fi

while true; do
    inotifywait -e modify -e create /etc/letsencrypt/archive/$domain

    sleep 1
    echo ">>> Restarting dockers $containers because certificate for $domain has been modified."
    for container in $containers; do
        docker restart $container
    done
done