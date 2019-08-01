# &nbsp;![](https://raw.githubusercontent.com/adferrand/docker-letsencrypt-dns/master/images/logo_from_realies_200px.png) adferrand/letsencrypt-dns
![](https://img.shields.io/badge/tags-latest-lightgrey.svg) [![](https://images.microbadger.com/badges/version/adferrand/letsencrypt-dns:2.16.0.svg) ![](https://images.microbadger.com/badges/image/adferrand/letsencrypt-dns:2.16.0.svg)](https://microbadger.com/images/adferrand/letsencrypt-dns:2.16.0) [![CircleCI](https://circleci.com/gh/adferrand/docker-letsencrypt-dns/tree/master.svg?style=shield)](https://circleci.com/gh/adferrand/docker-letsencrypt-dns/tree/master)

* [Container functionalities](#container-functionalities)
* [Why use this Docker](#why-use-this-docker-)
* [Preparation of the container](#preparation-of-the-container)
	* [Configuring the SSL certificates](#configuring-the-ssl-certificates)
	* [Configuring DNS provider and authentication to DNS API](#configuring-dns-provider-and-authentication-to-dns-api)
		* [With environment variables](#with-environment-variables)
		* [With YAML configuration files](#with-yaml-configuration-files)
* [Run the container](#run-the-container)
* [Data persistency](#data-persistency)
	* [Share certificates with the host](#share-certificates-with-the-host)
	* [Share certificates with other containers](#share-certificates-with-other-containers)
	* [Certificates files permissions](#certificates-files-permissions)
* [Runtime operations](#runtime-operations)
	* [Certificates reconfiguration at runtime](#certificates-reconfiguration-at-runtime)
	* [Restart containers when a certificate is renewed](#restart-containers-when-a-certificate-is-renewed)
	* [Call a reload command on containers when a certificate is renewed](#call-a-reload-command-on-containers-when-a-certificate-is-renewed)
	* [Run a custom deploy hook script](#run-a-custom-deploy-hook-script)
	* [Run a service in a cluster environment](#run-a-service-in-a-cluster-environment)
* [Miscellaneous and testing](#miscellaneous-and-testing)
	* [Using ACME v1 servers](#using-acme-v1-servers)
	* [Specifying the renewal schedule](#specifying-the-renewal-schedule)
	* [Activate staging ACME servers](#activating-staging-acme-servers)
	* [Auto-export certificates in PFX format](#auto-export-certificates-in-pfx-format)
	* [Delegated authentication](#delegated-authentication)
    * [Sleep time](#sleep-time)
    * [Shell access](#shell-access)

## Container functionalities

This Docker is designed to manage [Let's Encrypt](https://letsencrypt.org) SSL certificates based on [DNS challenges](https://tools.ietf.org/html/draft-ietf-acme-acme-01#page-44).

* Let's Encrypt wildcard and regular certificates generation by [Certbot](https://github.com/certbot/certbot) using DNS challenges,
* Automated renewal of almost expired certificates using Cron Certbot task,
* Standardized API throuh [Lexicon](https://github.com/AnalogJ/lexicon) library to insert the DNS challenge with various DNS providers,
* Centralized configuration file to maintain several certificates,
* Modification of container configuration without restart,
* Automated restart of specific containers when a certificate is renewed,
* Container built on top of [Alpine Linux](https://alpinelinux.org) distribution to reduce the footprint (image size is below 200MB).

## Why use this Docker ?

If you are reading these lines, you certainly want to secure all your dockerized services using Let's Encrypt SSL certificates, which are free and accepted everywhere.

If you want to secure Web services through HTTPS, there is already plenty of great tools. In the Docker world, one can check [traefik](https://hub.docker.com/_/traefik/), or [nginx-proxy](https://hub.docker.com/r/jwilder/nginx-proxy/) + [letsencrypt-nginx-proxy-companion](https://hub.docker.com/r/jrcs/letsencrypt-nginx-proxy-companion/). Basically, theses tools will allow automated and dynamic generation/renewal of SSL certificates, based on TLS or HTTP challenges, on top of a reverse proxy to encrypt everything through HTTPS.

So far so good, but you may fall in one of the following categories:

 1. You are in a firewalled network, and your HTTP/80 and HTTPS/443 ports are not opened to the outside world.
 2. You want to secure non-Web services (like LDAP, IMAP, POP, *etc.*) were the HTTPS protocol is of no use.
 3. You want to generate a wildcard certificate, valid for any sub-domain of a given domain.

For the first case, ACME servers need to be able to access your website through HTTP (for HTTP challenges) or HTTPS (for TLS challenges) in order to validate the certificate. With a firewall these two challenges - which are widely used in HTTP proxy approaches - will not be usable: you need to ask a DNS challenge. Please note that traefik embed DNS challenges, but only for few DNS providers.

For the second case, there is no website to use TLS or HTTP challenges, and you should ask a DNS challenge. Of course you could create a "fake" website to validate the domain using a HTTP challenge, and reuse the certificate on the "real" service. But it is a workaround, and you have to implement a logic to propagate the certificate, including during its renewal. Indeed, most of the non-Web services will need to be restarted each time the certificate is renewed.

For the last case, the use of a DNS challenge is mandatory. Then the problems concerning certificates propagation that have been discussed in the second case will also occur.

The solution is a dedicated and specialized Docker service which handles the creation/renewal of Let's Encrypt certificates, and ensure their propagation in the relevant Docker services. It is the purpose of this container.

## Preparation of the container

First of all, before using this container, two steps of configuration need to be done: describing all certificates to acquire and maintain, then configuring an access to your DNS zone to publish DNS challenges.

### Configuring the SSL certificates

This container uses a file which must be put at `/etc/letsencrypt/domains.conf` in the container. It is a simple text file which follows theses rules:
- each line represents a certificate,
- one line may contain several domains separated by a space,
- the first domain is the certificate main domain,
- each following domain on a line is included in the SAN of the certificate, allowing it to be used for several domains.

Let's take an example. Our domain is `example.com`, and we want:
- a certificate for `smtp.example.com`
- a certificate for `imap.example.com` + `pop.example.com`
- a certificate for `ldap.example.com`
- a wildcard certificate for any sub-domain of `example.com` and for `example.com` itself

Then the `domains.conf` will look like this:

```
smtp.example.com
imap.example.com pop.example.com
ldap.example.com
*.example.com example.com
```

You need also to provide the mail which will be used to register your account on Let's Encrypt. Set the environment variable `LETSENCRYPT_USER_MAIL (default: noreply@example.com)` in the container for this purpose.

_NB: For a wildcard certificate, specifying a sub-domain already covered by the wildcard will raise an error during Certbot certificate generation (eg. `test.example.com` cannot be put on the same line than `*.example.com`)._

### Configuring DNS provider and authentication to DNS API

#### With environment variables

When using a DNS challenge, a TXT entry must be inserted in the DNS zone which manage the certificate domain. This TXT entry must contain a unique hash calculated by Certbot, and the ACME servers will check it before delivering the certificate.

This container will do the hard work for you, thanks to the association between [Certbot](https://certbot.eff.org/) and [Lexicon](https://github.com/AnalogJ/lexicon): DNS provider API will be called automatically to insert the TXT record when needed. All you have to do is to define for Lexicon the DNS provider to use, and the API access key.

See the list of providers supported on this link: https://github.com/AnalogJ/lexicon/blob/v3.2.7/README.md#providers

The DNS provider is choosen by setting an environment variable passed to the container: `LEXICON_PROVIDER (default: cloudflare)`.

Most of the DNS APIs requires a user and a unique access token delivered by the DNS provider. See the documentation of your provider to check how to get these (see the DNS providers list on [Lexicon documentation](https://github.com/AnalogJ/lexicon). Once done, authentication stuff can be set using one of the three following approach:
* using environment variables in the form of `LEXICON_[PROVIDER]_[OPTION]` for provider parameters in the form of `--[option]` (for instance, `LEXICON_CLOUDFLARE_AUTH_USERNAME` with the CloudFlare provider for `--auth-username` option)
* using environment variable `LEXICON_PROVIDER_OPTIONS (default empty)` which will be append directly to the lexicon binary (for instance, `LEXICON_PROVIDER_OPTIONS` could be set to `--auth-token=my-token ...`)

For instance, if the provider is CloudFlare, the username is `my_user` and the access token is `my_secret_token`, following environment variables must be passed to the container:

```bash
LEXICON_CLOUDFLARE_AUTH_USERNAME=my_cloudflare_email
LEXICON_CLOUDFLARE_AUTH_TOKEN=my_cloudflare_global_api_key
```

Or alternatively:
```bash
LEXICON_PROVIDER=cloudflare
LEXICON_PROVIDER_OPTIONS=--auth-username=my_cloudflare_email --auth-token=my_cloudflare_global_api_key
```

Some providers (like OVH) need more specific environment variables. First, run following command to get the Lexicon help for this DNS provider:

```bash
docker run -it --rm adferrand/letsencrypt-dns lexicon ovh --help
```

Once done, you will see authentication parameters of the form `--auth-somevar`. Theses parameters must be setted using environment variables of the form `LEXICON_[PROVIDER]_AUTH_SOMEVAR`.

For example with OVH, authentication parameters are `--auth-entrypoint`, `--auth-application-key`, `--auth-application-secret` and `--auth-consumer-key`. Corresponding environment variables are `LEXICON_OVH_AUTH_ENTRYPOINT`, `LEXICON_OVH_AUTH_APPLICATION_KEY`, `LEXICON_OVH_AUTH_APPLICATION_SECRET` and `LEXICON_OVH_AUTH_CONSUMER_KEY`. Or alternatively, set the `LEXICON_PROVIDER_OPTIONS` to `--auth-entrypoint=my_entrypoint --auth-application-key=my_application_key --auth-application-secret=my_application_secret --auth-consumer-key=my_consumer_key`.

Finally there is some options specific to Lexicon itself, not related to the authentication on a particular provider (like `--delegate`). You can specify this kind of options (eg. `domain` for Cloudns) via the `LEXICON_OPTIONS (default empty)` environment variable.

#### With YAML configuration files

Starting with version 2.7.0 that uses Lexicon 3.x, DNS providers and Lexicon can be configured using YAML configuration files. It means that a unique `lexicon.yml`, located on the persisted storage `/etc/letsencrypt`, can contain all parameters for Lexicon and several DNS providers. Each entry corresponds to a Lexicon option, or a provider name. Under a provider name, the relevant parameters for this provider can be set. As a convention name for the parameters, a given CLI argument `--auth-username` will be written in the YAML configuration file as `auth_username`.

To select the provider to use, the environment variable `LEXICON_PROVIDER` still need to be set.

Taking the OVH example in the previous version, with a specific configuration to provide for Lexicon itself (`--delegate`), the `lexicon.yml` will take the following form:
```yml
# Content of /etc/letsencrypt/lexicon.yml
delegate: subdomain
ovh:
  auth_entrypoint: ovh-eu
  auth_application_key: my_application_key
  auth_application_secret: my_application_secret
  auth_consumer_key: my_consumer_key
```

The YAML configuration file approach is particularly well suited for the `auto` DNS provider, that is able to resolve the actual DNS provider for a given domain. Indeed, `lexicon.yml` will be a convenient place to put the configuration of several providers.

_NB: A configuration file can be set for one particular provider. In this case, the filename must be `lexicon_[provider_name].yml` (eg. `lexicon_ovh.yml` for OVH). Theses files must be located in `/etc/letsencrypt`. There root content is directly the parameters of the relevant provider, like so:_
```yml
# Content of /etc/letsencrypt/lexicon_cloudflare.yml
auth_username: my_cloudflare_email
auth_token: my_cloudflare_global_api_key
```

## Run the container

Once preparation is done, the container can be run. As said, `domains.conf` must be mounted in the container, and API authentication variables must be passed as environment variables to the container.

For Cloudflare, with example described during preparation, run :

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	adferrand/letsencrypt-dns
```

At start, the container will look to `domains.conf` and generate the certificates if needed. Then a cron task is launched twice a day to regenerate certificates if needed. The certificates are located in the container at `/etc/letsencrypt/live/`.

## Data persistency

This container declares `/etc/letsencrypt` as a volume. Consequently generated certificates will not be destroyed if the container is destroyed. Upon re-creation, certificates will be available again.

### Share certificates with the host

If you want to share the generated certificates to the host (eg. in `/var/docker-data/letsencrypt`), you can use a host mount:

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt \
    --env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	adferrand/letsencrypt-dns
```

### Share certificates with other containers

If you want to share the generated certificates with other containers, mount the container volume `/etc/letsencrypt` into the target containers. For example:

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt \
	--env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	adferrand/letsencrypt-dns

docker run \
	--volumes-from letsencrypt-dns \
	--env 'KEY_PATH=/etc/letsencrypt/live/smtp.example.com/privkey.pem' \
	--env 'CERTIFICATE_PATH=/etc/letsencrypt/live/smtp.example.com/cert.pem' \
	namshi/smtp
```

The volume `/etc/letsencrypt` will be available for the SMTP container, which can use a generated certificate for its own concern (here, securing the SMTP protocol).

### Certificates files permissions

By default certificates files (`cert.pem`, `privkey.pem`, _etc._) are accessible only to the user/group owning `/etc/letsencrypt`, which is **root** by default. It means that generated certificates cannot be used by non-root processes (in other containers or on the host).

You can modify file mode of `/etc/letsencrypt/archive` and `/etc/letsencrypt/live` folders and their content to allow non-root processes to access the certificates. Set environment variables `CERTS_DIRS_MODE (default: 0750)` and `CERTS_FILES_MODE (default: 0640)` to modify directories and files mode respectivly. For example, a file mode of `0644` and directory mode of `0755` will open access to everyone.

Alternatively or cumulatively you may need to change the owner user/group of `/etc/letsencrypt/archive` and `/etc/letsencrypt/live` folders and their content. To do so, specify user/group name or uid/gid in the relevant environment variables: `CERTS_USER_OWNER (default: root)` and `CERTS_GROUP_OWNER (default: root)`.

_(Warning) Certificates files permissions, introduced in container version `1.4`, will modify default permissions for certificates. Previously, `/etc/letsencrypt/live` and `/etc/letsencrypt/archive` were `0750`, their sub-folders where `0755` and contained files were `0644`. Now theses folders and their sub-folders are `0750` while contained files are `0640`: this should not lead to any regression, as the parent folders have a more restrictive permission than their content, leading certs files to be unaccessible to non-root processes. However for pathological cases you will need to set environment variable `CERTS_DIRS_MODE` and `CERTS_FILES_MODE` appropriately._

## Runtime operations

### Certificates reconfiguration at runtime

If you want to add a new certificate, remove one, or extend existing one to other domains, you just need to modify the `domains.conf` file from the host. Once saved, the container will automatically mirror the modifications in `/etc/letsencrypt` volume. If new certificates need to be generated, please note that approximately 30 seconds are required for each generation before modifications are visible.

Please check the container logs to follow the operations.

### Restart containers when a certificate is renewed

As said in introduction, most of the non-Web services require a restart when the certificate is changed. And this will occur at least once each two months. To ensure correct propagation of the new certificates in your Docker services, one special entry can be added at the **end** of a line for the concerned certificate in `domains.conf`.

This entry takes the form of `autorestart-containers=container1,container2,container3` where `containerX` is the name of a container running on the same Docker instance than `letsencrypt-dns`.

You need also to mount the Docker socket of the host `/var/run/docker.sock` in the `letsencrypt-dns` container.

Once done, all specified containers will be restarted when the target certificate is renewed.

For example, we want to restart the container named `smtp` when the certificate `smtp.example.com` is renewed. Construct the following `domains.conf` file:

```
smtp.example.com imap.example.com autorestart-containers=smtp
auth.example.com
```

Then execute following commands:

```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt \
	--volume /var/run/docker.sock:/var/run/docker.sock \
	--env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	adferrand/letsencrypt-dns

docker run \
	--name smtp \
	--volumes-from letsencrypt-dns \
	--env 'KEY_PATH=/etc/letsencrypt/live/smtp.example.com/privkey.pem' \
	--env 'CERTIFICATE_PATH=/etc/letsencrypt/live/smtp.example.com/cert.pem' \
	namshi/smtp
```

If the certificate `smtp.example.com` is renewed, the container named `smtp` will be restarted. Renewal of `auth.example.com` will not restart anything.

### Call a reload command on containers when a certificate is renewed

Restarting a container when a certificate is renewed is sufficient for all cases. However one drawback is that the target processes will stop during a little time, and consequently the services provided are not continuous. This may be ok for non critical services, but problematic for things like authentication services or database servers.

If a target process allows it, the letsencrypt-dns container can call a reload configuration command on the target container when a certificate is renewed. In this case, service is not stopped and immediatly takes into account the new config, including the new certificate. Apache2 for example (example only, as an http challenge will be a better option here) can see its configuration to be hot-reloaded by invoking the command `apachectl graceful` in the target container.

To specify which command to launch on which container when a certificate is renewed, one will put at the **end** of the relevant line of `domains.conf` a special entry which takes the form of `autocmd-containers=container1:command1,container2:command2 arg2a arg2b,container3:command3 arg3a`. Comma `,` separates each container/command configuration, colon `:` separates the container name from the command to launch. Commands must be executable files, located in the $PATH of the target container, or accessed by their full path.

Similarly to the automatic containers restart functionality, you need to mount the Docker socket of the host /var/run/docker.sock in the letsencrypt-dns container (with the docker executable, using the command-line parameter `--volume /var/run/docker.sock:/var/run/docker.sock`).

In the case of an Apache2 server embedded in a container named `my-apache` to be reloaded when certificate `web.example.com` is renewed, put following entry in `domains.conf`:

```
web.example.com autocmd-containers=my-apache:apachectl graceful
```

If the certificate `web.example.com` is renewed, command `apachectl graceful` will be invoked on container `my-apache`, and the apache2 service will use the new certificate without killing any HTTP session.

_(Limitations on invokable commands) The option `autocmd-container` is intended to call a simple executable file with few potential arguments. It is not made to call some advanced bash script, and would likely fail if you do so. In fact, the command is not executed in a shell on the target, and variables will be resolved against the lets-encrypt container environment. If you want to operate advanced scripting, put an executable script in the target container, and use its path in `autocmd-container` option._

### Run a custom deploy hook script

You can specify a script or a command to execute after a certificate is created or renewed, by specifying `DEPLOY_HOOK` environment variable. This is useful if you want to copy certificates someplace else or need to reorganize file structure.

All standard environment variables will be available in your script, as well as two new variables set by certbot:
* `RENEWED_LINEAGE` - directory with certificate files (e.g. `/etc/letsencrypt/live/domain`)
* `RENEWED_DOMAINS` - list of domains for the certificate, separated by space 

Example: copying all new or renewed certificates to a single directory with `domain.crt` and `domain.key` filenames, making it easily usable with nginx:

Create deploy-hook.sh file and make it executable. 

```bash
#!/bin/sh
mkdir -p "/etc/nginx/certs"
cd "/etc/nginx/certs"
for domain in ${RENEWED_DOMAINS}; do
    cp "${RENEWED_LINEAGE}/fullchain.pem" "${domain}.crt"
    cp "${RENEWED_LINEAGE}/privkey.pem" "${domain}.key"
    chown $CERTS_USER_OWNER:$CERTS_GROUP_OWNER "${domain}.*"
    chmod $CERTS_FILES_MODE "${domain}.*"
done
```   

Execute:
```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--volume /etc/letsencrypt/deploy-hook.sh:/usr/local/bin/create-nginx-certs \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt \
	--volume /var/docker-data/nginx:/etc/nginx/certs \
	--env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	--env 'DEPLOY_HOOK=create-nginx-certs' \
	adferrand/letsencrypt-dns
```

### Run the container in a cluster environment

When this container runs in a cluster environment (eg. Swarm, Kubernetes), autoreload functionalities is likely to not be adressed to a single container, but to a service handled by several containers working together as a cluster.

Environment variable `DOCKER_CLUSTER_PROVIDER (default: none)` can be set for this purpose. Current possible values are `none` when there is no cluster (default) or `swarm`. If this variable is set to a cluster provider, names given in autorestart will be considered to be clustered services names, and appropriate commands will be used to restart the service.

_NB1: For now, only Docker Swarm is supported, and only autorestart takes the cluster into account. More complete cluster support will be added in the future._
_NB2: Since running an arbitrary command on all nodes of a service breaks the service abstraction, autocmd is not supported in Docker Swarm mode._

### Run a custom deploy hook script

You can specify a script or a command to execute after a certificate is created or renewed, by specifying `DEPLOY_HOOK` environment variable. This is useful if you want to copy certificates someplace else or need to reorganize file structure.

All standard environment variables will be available in your script, as well as two new variables set by certbot:
* `RENEWED_LINEAGE` - directory with certificate files (e.g. `/etc/letsencrypt/live/domain`)
* `RENEWED_DOMAINS` - list of domains for the certificate, separated by space 

Example: copying all new or renewed certificates to a single directory with `domain.crt` and `domain.key` filenames, making it easily usable with nginx:

Create deploy-hook.sh file and make it executable. 

```bash
#!/bin/sh
mkdir -p "/etc/nginx/certs"
cd "/etc/nginx/certs"
for domain in ${RENEWED_DOMAINS}; do
    cp "${RENEWED_LINEAGE}/fullchain.pem" "${domain}.crt"
    cp "${RENEWED_LINEAGE}/privkey.pem" "${domain}.key"
    chown $CERTS_USER_OWNER:$CERTS_GROUP_OWNER "${domain}.*"
    chmod $CERTS_FILES_MODE "${domain}.*"
done
```   

Execute:
```bash
docker run \
	--name letsencrypt-dns \
	--volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
	--volume /etc/letsencrypt/deploy-hook.sh:/usr/local/bin/create-nginx-certs \
	--volume /var/docker-data/letsencrypt:/etc/letsencrypt \
	--volume /var/docker-data/nginx:/etc/nginx/certs \
	--env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
	--env 'LEXICON_PROVIDER=cloudflare' \
	--env 'LEXICON_CLOUDFLARE_USERNAME=my_cloudflare_email' \
	--env 'LEXICON_CLOUDFLARE_TOKEN=my_cloudflare_global_api_key' \
	--env 'DEPLOY_HOOK=create-nginx-certs' \
	adferrand/letsencrypt-dns
```

## Miscellaneous and testing

### Using ACME v1 servers

Starting to version 2.0.0, this container uses the ACME v2 servers (production & staging) to allow wildcard certificates generation. If for any reason you want to continue to use old ACME v1 servers, you can set the environment variable `LETSENCRYPT_ACME_V1 (default: false)` to `true`. In this case, ACME v1 servers will be used to any certificate generation, but wildcard certificates will not be supported.

_NB: During a certificate renewal, the server (and authentication) used for the certificate generation will be reused, independently of the `LETSENCRYPT_ACME_V1` environment variable value. If you want to change the server used for a particular certificate, you will need first to revoke it by removing the relevant entry from `domains.txt` file before recreating it._

### Specifying the renewal schedule

By default the certificate regeneration process is run twice a day. This can be customized by setting the environment variable `CRON_TIME_STRING (default: "12 01,13 * * *")` to a cron time string. Be sure to also set the correct timezone using the environment variable `TZ (default: UTC)`.

### Activating staging ACME servers

During development it is not advised to generate certificates against production ACME servers, as one could reach easily the weekly limit of Let's Encrypt and could not generate certificates for a certain period of time. Staging ACME servers do not have this limit. To use them, set the environment variable `LETSENCRYPT_STAGING (default: false)` to `true`.

You will need to wipe content of `/etc/letsencrypt` volume before container re-creation when enabling or disabling staging.

### Auto-export certificates in PFX format

Some services need the SSL key and certificate stored together in PFX format (also known as PKCS#12) whose extension is .pfx (or .p12). For this purpose one can set the container environment variable `PFX_EXPORT (default: false)` to `true`: in this case, the container will ensure that every certificate handled by Certbot is exported in PFX format during certificate creation, renewal or container start/restart.

The PFX certificate for a given primary domain is located in the container on `/etc/letsencrypt/[DOMAIN]/cert.pks`: it contains the key, certificate and all intermediate certificates.

By default, the PFX certificates are not protected by a passphrase. You can define one using the environment variable `PFX_EXPORT_PASSPHRASE`.

### Delegated authentication

For domains which cannot be altered via DNS delegated authentication implemented.

Use the environment variables `DELEGATED_DOMAIN` and `DELEGATED_SUBDOMAIN` (may be the same) and create CNAME record `_acme-challenge.DOMAIN.` which points to _acme-challenge.`DELEGATED_SUBDOMAIN.`.

Example:

* Domain for SSL is `domain.com`
* Delegated domain is `delegated.com` and the special subdomain is `acme.delegated.com`
* CNAME record `_acme-challenge.domain.com.` points to `_acme-challenge.acme.delegated.com.`

### Sleep time

During a DNS challenge, a sleep must be done after TXT entry insertions in order to let DNS zone updates be propagated correctly and ensure that ACME servers will see them. Default value is 30 seconds: if this value does not suit your needs, you can modify it by setting the environment variable `LEXICON_SLEEP_TIME (default: 30)`.

### Shell access

For debugging and maintenance purpose, you may need to start a shell in your running container. With a Docker of version 1.3.0 or higher, you can do:

```bash
docker exec -it letsencrypt-dns /bin/sh
```

You will obtain a shell with the standard tools of an Alpine distribution.

## Docker-Compose configuration

Within the directory compose you can find a basic docker-compose configuration.
All used volumes and environment variables are described in detail in [Preparation of the container|#preparation-of-the-container].
The docker compose used the provider and provider options approach to be able to support different providers.
