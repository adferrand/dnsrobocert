#!/bin/sh

staging_cmd=""
if [ "$LETSENCRYPT_STAGING" = true ]; then
    staging_cmd="--staging"
fi

while true; do
    echo "#### Registering Let's Encrypt account if needed ####"
    certbot register -n --agree-tos -m $LETSENCRYPT_USER_MAIL $staging_cmd

    echo "#### Creating missing certificates if needed (~1min for each) ####"
    while read entry; do
        domains_cmd=""
        for domain in $entry; do
            domains_cmd="$domains_cmd -d $domain"
        done
        echo ">>> Creating a certificate for domain(s): $entry"
        certbot certonly -n --manual --preferred-challenges=dns --manual-auth-hook /var/lib/letsencrypt/hooks/authenticator.sh --manual-cleanup-hook /var/lib/letsencrypt/hooks/cleanup.sh --manual-public-ip-logging-ok --expand $staging_cmd $domains_cmd
    done < /etc/letsencrypt/domains.txt

    echo "### Revoke and delete certificates if needed ####"
    for domain in `ls /etc/letsencrypt/live`; do
        remove_domain=true
        while read entry; do
            for comp_domain in $entry; do
                if [ "$domain" = "$comp_domain" ]; then
                    remove_domain=false
                    break;
                fi
            done
        done < /etc/letsencrypt/domains.txt

        if [ "$remove_domain" = true ]; then
            echo ">>> Removing the certificate $domain"
            certbot revoke $staging_cmd --cert-path /etc/letsencrypt/live/$domain/cert.pem
            certbot delete $staging_cmd --cert-name $domain
        fi
    done

    inotifywait -e modify /etc/letsencrypt/domains.txt
done