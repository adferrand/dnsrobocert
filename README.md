# adferrand/letsencrypt-dns
![](https://img.shields.io/badge/tags-latest-lightgrey.svg) [![](https://images.microbadger.com/badges/version/adferrand/letsencrypt-dns:latest.svg) ![](https://images.microbadger.com/badges/image/adferrand/letsencrypt-dns:latest.svg)](https://microbadger.com/images/adferrand/letsencrypt-dns:latest)  

* [Container functionalities](#container-functionalities)
* [Why use this Docker](#why-use-this-docker-)
* [Preparation of the container](#preparation-of-the-container)
	* [Configuring the SSL certificates](#configuring-the-ssl-certificates)
	* [Configuring DNS provider and authentication to DNS API](#configuring-dns-provider-and-authentication-to-dns-api)
* [Run the container](#run-the-container)
	* [Advanced UI authentication/authorization](#advanced-ui-authenticationauthorization)
* [Data persistency](#data-persistency)
	* [Share certificates with the host](#share-certificates-with-the-host)
	* [Share certificates with other containers](#share-certificates-with-other-containers)
* [Reconfiguration on a running container](#reconfiguration-on-a-running-container)
* [Restarting containers when a certificate is renewed](#restarting-containers-when-a-certificate-is-renewed)
* [Miscellaneous and testing](#miscellanous-and-testing)
	* [Activating staging ACME servers](#activating-staging-acme-servers)
    * [Sleep time](#sleep-time)
    * [Shell access](#shell-access)

## Container functionalities

This Docker is designed to manage Let's Encrypt SSL certificates based on DNS challenges.

* Let's Encrypt certificates generation by Certbot using DNS challenges,
* Automated renewal of almost expired certificates using Cron Certbot task,
* Standardized API throuh Lexicon library to insert the DNS challenge with various DNS providers
* Centralized configuration file to maintain several certificates
* Modification of container configuration without restart
* Automated restart of specific containers when a certificate is renewed
* Container built on top of Alpine distribution to reduce the footprint. Image size is below 100MB.

## Why use this Docker ?

If you are reading theses lines, you certainly want to secure all your dockerized services using Let's Encrypt SSL certificates, which are free and accepted everywhere.

If you want to secure Web services through HTTPS, there is already plenty of great tools. In the Docker world, one can check traefik, or nginx-proxy + letsencrypt-nginx-proxy-companion. Basically, theses tools will allow automated and dynamic generation/renewal of SSL certificates, based on TLS or HTTP challenges, on top of a reverse proxy to encrypt everything through HTTPS.

Excellent, but you could fall in one of the following categories, were DNS challenges are useful:

 1. You are in a firewalled network, and your HTTP/80 and HTTPS/443 ports are not opened to the outside world.
 2. You want to secure non-Web services (like LDAP, IMAP, POP, *etc.*) were the HTTPS protocol is of no use.

For the first case, ACME servers need to be able to access your website through HTTP (for HTTP challenges) or HTTPS (for TLS challenges) in order to validate the certificate. With a firewall, theses two challenges, which are widely use in HTTP proxy approaches are not usable. Please note that traefik embed DNS challenges, but only for few DNS providers.

For the second case, there is no website to use TLS or HTTP challenges. So you can of course create a "fake" website to validate the domain, and reuse the certificate on the "real" service. But it is a workaround, and you have to implement a logic to propagate the certificate, including during its renewal. Indeed, most of the non-Web services will need to be restarted each time the certificate is renewed.

The solution is a dedicated and specialized Docker service which handles the creation/renewal of Let's Encrypt certificates, and ensure their propagation in the relevant Docker services. It is the purpose of this container.

## Preparation of the container

First of all, before using this container, two steps of configuration need to be done: describing the certificates to acquire and maintain, then configuring the access to your DNS zone to publish DNS challenges.

### Configuring the SSL certificates

This container uses a file which must be placed at `/etc/letsencrypt/domains.conf` in the container. It is a simple text file, following theses rules:
- each line represents a certificate,
- one line may contain several domains, seperated by a space,
- the first domain is the certificate main domain,
- each following domain on a line is included in the SAN of the certificate, allowing it to be used for several domains.

Let's take an example. Our domain is `example.com`, and we want:
- a certificate for `smtp.example.com`
- a certificate for `imap.example.com` + `pop.example.com`
- a certificate for `ldap.example.com`

Then the `domains.conf` will look like this:

```
smtp.example.com
imap.example.com pop.example.com
ldap.example.com
```

You need also to provide the mail which will be used to register your account on Let's Encrypt. Set the environment variable `LETSENCRYPT_USER_MAIL (default: noreply@example.com)` in the container for this purpose.

### Configuring DNS provider and authentication to DNS API

When using a DNS challenge, a TXT entry must be inserted in the DNS zone carying the domain of the certificate. This TXT entry must contain a unique hash calculated by Certbot, and the ACME servers will check it to deliver the certificate.

This container will do the hard work for you, thanks to the association between Certbox and Lexicon, and DNS provider API will be called automatically to  insert the TXT record when needed. All you have to do is to define for Lexicon the DNS provider to use, and the access key to the API.

Following DNS provider are supported: AWS Route53, Cloudflare, CloudXNS, DigitalOcean, DNSimple, DnsMadeEasy, DNSPark, DNSPod, EasyDNS, Gandi, Glesys, LuaDNS, Memset, Namesilo, NS1, OVH, PointHQ, PowerDNS, Rage4, Transip, Yandex, Vultr.

The DNS provider is choosen by setting an environment variable passed to the container: `LEXICON_PROVIDER (default: cloudflare)`.

Most of the DNS APIs requires a user and a unique access token delivered by the DNS provider. See the documentation of your provider to check how to get these (see the DNS providers list on [https://github.com/AnalogJ/lexicon#providers](Lexicon documentation). Once done, set the environment variables `LEXICON_[PROVIDER]_USER` and `LEXICON_[PROVIDER]_TOKEN` to this user/token. `[PROVIDER]` must be replaced by the value in capital case passed to the environment variable `LEXICON_PROVIDER`.

For instance, if the provider is DigitalOcean, the user is `my_user` and the access token is `my_secret_token`, following environment variables must be passed to the container:

```bash
LEXICON_PROVIDER=digitalocean
LEXICON_DIGITALOCEAN_USER=my_user
LEXICON_DIGITALOCEAN_TOKEN=my_secret_token
```

Some providers (like OVH) need more specific environment variables. First, run following command to get the Lexicon help for this DNS provider:

```bash
docker run -it --rm adferrand/letsencrypt-dns lexicon ovh --help
```

Once done, you will see authentication parameters of the form `--auth-somevar`. Theses parameters must be setted using environment variables of the form `LEXICON_[PROVIDER]_SOMEVAR`.

For example with OVH, authentication parameters are `--auth-entrypoint`, `--auth-application-key`, `--auth-application-secret` and `--auth-consumer-key`. Corresponding environment variables are `LEXICON_OVH_ENTRYPOINT`, `LEXICON_OVH_APPLICATION_KEY`, `LEXICON_OVH_APPLICATION_SECRET` and `LEXICON_OVH_CONSUMER_KEY`.

## Run the container

Once preparation is done, the container can be run. As said, `domains.cfg` must be mounted in the container, and API authentication variables must be passed as environment variables to the container.

For Cloudflare, with example described during preparation, run :

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.cfg:/etc/letsencrypt/domains.cfg
    --env 'LETSENCRYPT_USER_MAIL=admin@example.com'
	--env 'LEXICON_PROVIDER=cloudflare'
	--env 'LEXICON_CLOUDFLARE_USER=my_user'
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_secret_token'
```

At start, the container will look to `domains.cfg` and generate the certificates if needed. Then a cron task is launched twice a day to regenerated certificates if needed. The certificates are located in the container at `/etc/letsencrypt/live/`.

## Data persistency

This container declares `/etc/letsencrypt` as a volume. Then generated certificates will not be destroyed if the container is destroyed. At new creation, certificates will be available again.

### Share certificates with the host

If you want to share the generated certificates to the host (eg. in `/var/docker-data/letsencrypt`), you can use a host mount:

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.cfg:/etc/letsencrypt/domains.cfg
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt
    --env 'LETSENCRYPT_USER_MAIL=admin@example.com'
	--env 'LEXICON_PROVIDER=cloudflare'
	--env 'LEXICON_CLOUDFLARE_USER=my_user'
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_secret_token'
	adferrand/letsencrypt-dns
```

### Share certificates with other containers

If you want to shared the generated certificates with other containers, mount the volume `/etc/letsencrypt` of this container into the target containers. For example:

```bash
docker run \
	--name letsencrypt-dns \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt
    --env 'LETSENCRYPT_USER_MAIL=admin@example.com'
	--env 'LEXICON_PROVIDER=cloudflare'
	--env 'LEXICON_CLOUDFLARE_USER=my_user'
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_secret_token'
	adferrand/letsencrypt-dns

docker run \
	--volumes-from letsencrypt-dns
	--env 'KEY_PATH=/etc/letsencrypt/live/smtp.example.com/privkey.pem'
	--env 'CERTIFICATE_PATH=/etc/letsencrypt/live/smtp.example.com/cert.pem'
	namshi/smtp
```

The volume `/etc/letsencrypt` is then available for the SMTP container, which can use a generated certificate for its own concern (here, securing the SMTP protocol).

## Reconfiguration on a running container

If you want to add a new certificate, remove one, or extend existing one to other domains, you just need to modify the `domains.conf` file from the host. Once saved, the container will automatically mirror the modifications in the `/etc/letsencrypt` volume. If new certificates need to be generated, please note that approximately 30 seconds are required for each generation before modifications are visible.

Please check the container logs to follow the operations.

## Restarting containers when a certificate is renewed

As said in introduction, most of the non-Web services require a restart when the certificate is changed. And this will occur at least once each two months. To ensure correct propagation of the new certificates in your Docker services, one special entry can be added at the end of a line for the concerned certificate in `domains.conf`.

This entry takes the form of `autorestart-containers=container1,container2,container3` where `containerX` is the name of a container running on the same Docker instance than `letsencrypt-dns`.

You need also to mount the Docker socket of the host `/var/run/docker.sock` in the `letsencrypt-dns` container.

Once done, all specified containers will be restarted when the target certificate is renewed.

For example, we want to restart the container named `smtp` when the certificate `smtp.example.com` is renewed. Construct the following `domains.conf` file:

```
smtp.example.com imap.example.com autrestart-containers=smtp
auth.example.com
```

Then execute following commands

```bash
docker run \
	--name letsencrypt-dns \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt
    --env 'LETSENCRYPT_USER_MAIL=admin@example.com'
	--env 'LEXICON_PROVIDER=cloudflare'
	--env 'LEXICON_CLOUDFLARE_USER=my_user'
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_secret_token'
	adferrand/letsencrypt-dns

docker run \
	--name smtp
	--volumes-from letsencrypt-dns
	--env 'KEY_PATH=/etc/letsencrypt/live/smtp.example.com/privkey.pem'
	--env 'CERTIFICATE_PATH=/etc/letsencrypt/live/smtp.example.com/cert.pem'
	namshi/smtp
```

If the certificate `smtp.example.com` is renewed, the container named `smtp` will be restarted. Renewal of `auth.example.com` will not restart anything.

## Miscellaneous and testing

### Activating staging ACME servers

During development it is not advised to generate certificates againt production ACME servers, as one could reach easily the weekly limit of Let's Encrypt and could not generate certificates for a certain period of time. Staging ACME servers does not have this limit. To use them, set the environment variable `LETSENCRYPT_STAGING (default: false)` to `true`.

You will need to wipe content of `/etc/letsencrypt` volume before container re-creation when enabling or disabling staging.

### Sleep time

During a DNS challenge, a sleep must be done after the insertion of the TXT entry in order to let the entry to be propagated correctly and ensure that ACME servers will see it. The default value is 30 seconds: if this value does not suit you, you can modify it by setting the environment variable `LEXICON_SLEEP_TIME (default: 30)` in the container.

### Shell access

For debugging and maintenance purpose, you may need to start a shell in your running container. With a Docker of version 1.3.0 or higher, you can do:

```bash
docker exec -it letsencrypt-dns /bin/sh
```

You will obtain a shell with the standard tools of an Alpine distribution.