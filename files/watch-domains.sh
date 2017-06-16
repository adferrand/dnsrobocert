#!/bin/sh

autorestart_pattern="autorestart-containers="

staging_cmd=""
if [ "$LETSENCRYPT_STAGING" = true ]; then
    staging_cmd="--staging"
fi

while true; do
    # Clean all autorestart containers instances
    rm -f /etc/supervisord.d/*_autorestart-containers

    echo "#### Registering Let's Encrypt account if needed ####"
    certbot register -n --agree-tos -m $LETSENCRYPT_USER_MAIL $staging_cmd

    echo "#### Creating missing certificates if needed (~1min for each) ####"
    while read entry; do
        domains_cmd=""
        main_domain=""
        containers=""

        for domain in $entry; do
            if [ "${domain#*$autorestart_pattern}" != "$domain" ]; then
                containers=${domain/autorestart-containers=/}
            elif [ -z $main_domain ]; then
                main_domain=$domain
                domains_cmd="$domains_cmd -d $domain"
            else
                domains_cmd="$domains_cmd -d $domain"
            fi
        done

        echo ">>> Creating a certificate for domain(s):$domains_cmd"
        certbot certonly -n --manual --preferred-challenges=dns --manual-auth-hook /var/lib/letsencrypt/hooks/authenticator.sh --manual-cleanup-hook /var/lib/letsencrypt/hooks/cleanup.sh --manual-public-ip-logging-ok --expand $staging_cmd $domains_cmd
        
        if [ "$containers" != "" ]; then
            echo ">>> Watching certificate for main domain $domain: containers $containers autorestarted when certificate is changed."
            echo "[program:${main_domain}_autorestart-containers]" >> /etc/supervisord.d/${main_domain}_autorestart_containers
            echo "command = /scripts/autorestart-containers.sh $main_domain $containers" >> /etc/supervisord.d/${main_domain}_autorestart_containers
            echo "redirect_stderr = true" >> /etc/supervisord.d/${main_domain}_autorestart_containers
            echo "stdout_logfile = /dev/stdout" >> /etc/supervisord.d/${main_domain}_autorestart_containers
            echo "stdout_logfile_maxbytes = 0" >> /etc/supervisord.d/${main_domain}_autorestart_containers
        fi
    done < /etc/letsencrypt/domains.conf

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
        done < /etc/letsencrypt/domains.conf

        if [ "$remove_domain" = true ]; then
            echo ">>> Removing the certificate $domain"
            certbot revoke $staging_cmd --cert-path /etc/letsencrypt/live/$domain/cert.pem
            certbot delete $staging_cmd --cert-name $domain
        fi
    done

    echo "### Reloading supervisord configuration ###"
    supervisorctl update

    inotifywait -e modify /etc/letsencrypt/domains.conf
done