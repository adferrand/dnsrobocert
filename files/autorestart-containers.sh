#!/bin/sh

domain=$1
containers=$2
is_new_certificate=$3
cluster_provider=$4

if [ ! -S /var/run/docker.sock ]; then
    echo "ERROR: /var/run/docker.sock socket is missing."
    exit 1
fi

if [ ! -d /etc/letsencrypt/archive/$domain ]; then
    echo "ERROR: /etc/letsencrypt/archive/$domain directory is missing."
    exit 1
fi

restart() {
    IFS=','; for container in $containers; do
        if [ "$cluster_provider" == "swarm" ]; then
            docker service update --detach=false --force $container
        else
            docker restart $container
        fi
    done; unset IFS
}

# Load hash of the certificate
current_hash=`md5sum /etc/letsencrypt/live/$domain/cert.pem | awk '{ print $1 }'`
while true; do
    new_hash=`md5sum /etc/letsencrypt/live/$domain/cert.pem | awk '{ print $1 }'`

    if [ "$is_new_certificate" = true ]; then
        echo ">>> Restarting dockers $containers because certificate for $domain has been created."
        restart
        is_new_certificate=false
    elif [ "$current_hash" != "$new_hash" ]; then
        echo ">>> Restarting dockers $containers because certificate for $domain has been modified."
        restart
        # Keep new hash version
        current_hash="$new_hash"
    fi

    # Wait 1s for next iteration
    sleep 1
done
