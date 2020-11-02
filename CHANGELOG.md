# Changelog

## master - CURRENT
### Added
* Add Python 3.9 official support

### Modified
* Upgrade Lexicon to 3.4.5 (various fixes on providers)

## 3.7.1 - 25/10/2020
### Modified
* Upgrade Lexicon to 3.4.4 (fix Gandi provider)
* Upgrade Certbot to 1.9.0

## 3.7.0 - 11/09/2020
## Modified
* Upgrade Lexicon to 3.4.3 (add Njalla provider)
* Upgrade Certbot to 1.8.0

## 3.6.0 - 17/08/2020
## Modified
* Upgrade Lexicon to 3.3.28
* Upgrade Certbot to 1.7.0
* Upgrade Docker base image to Alpine 3.12

## 3.5.1 - 25/07/2020
## Modified
* Modify dependencies versions pinning to fix the docker images builds

## 3.5.0 - 23/07/2020
## Added
* `autocmd.command` now accepts list of string. If a list of string is provided, the command will
  be executed outside of a shell. If a string is provided, it will be executed inside a shell.
  The list of string form should be used if you do not need the features of a shell since it allows
  a better control of the arguments passed to the command and avoid potential injections attacks.

## Modified
* Upgrade Lexicon to 3.3.27 (support for Dynu.com provider)
* Upgrade Docker base image to Alpine 3.12

## 3.4.0 - 14/06/2020
### Added
* DNS challenges are now all run before any wait or check happens. This is useful for certificates that
  contains  lot of domains, because DNSroboCert will wait only once the provided `sleep_time`, instead
  of waiting after each challenge. This optimizations is also valid for `max_checks`.
  
### Modified
* Improve log output from the auth and cleanup hooks.
* Improve documentation.

## 3.3.4 - 14/06/2020
### Modified
* Upgrade Lexicon to 3.3.26 (fix errors with Godaddy provider)

## 3.3.3 - 03/06/2020
### Modified
* Upgrade Lexicon to 3.3.24
* Upgrade Certbot to 1.5.0

## 3.3.2 - 31/05/2020
### Added
* Allow environment variable injection in the configuration file

## 3.3.1 - 30/05/2020
### Added
* Validate the directory URL with a regex

### Changed
* Improve the regex check to email account for better compatibility

## 3.3.0 - 15/05/2020
### Added
* Set the User-Agent comment for Let'sEncrypt statistics

### Changed
* Update Lexicon to 3.3.22
* Search for `dnsrobocert.yml` config file in current directory when `--config` flag is not set.

## 3.2.0 - 06/05/2020
### Changed
* Update Lexicon to 3.3.21 (API tokens for Cloudflare)
* Update Certbot to 1.4.0

## 3.1.7 - 04/05/2020
### Added 
* DNSroboCert can now display logs in your current timezone if the `TIMEZONE` environment variable
  is set (@a16bitsysop #104)

### Changed
* Update Lexicon to 3.3.20 (rebranded Hetzner provider, support pagination on CloudFlare)

## 3.1.6 - 08/04/2020
## Changed
* Update runtime dependencies (including cryptography 2.9)
* Fix the `delegated_subdomain` parameter in providers configuration that was not taken into account
  (@davidyuk #96)
* Fix providers configuration link in the documentation (@davidyuk #95)

## 3.1.5 - 01/04/2020
### Changed
* Ensure a certificate name does not have wildcard characters when migrating from legacy config
  (eg. `example.com` for domains `[*.example.com`, `example.com]` instead of `*.example.com`).

## 3.1.4 - 30/03/2020
### Changed
* Protect the auth hook from NXDOMAIN failures when checking if the TXT entry of a challenge
  has been propagated in the DNS zone.
* Improve logs during sub-command execution (flush the output)

## 3.1.3 - 30/03/2020
### Added
* `acme.certs_permissions.user` and `acme.certs_permissions.group` can know be defined as integer
  to set the uid or gid instead of the user name and group name owner of the certificates.

## 3.1.2 - 29/03/2020
### Changed
* More consistent output for sub-commands launched by DNSroboCert

## 3.1.1 - 28/03/2020
### Added
* Add the `ttl` parameter in the providers definition. It allows to control the TTL value in TXT entries
  inserted during the DNS-01 challenges. This value for environment variable `LEXICON_TTL` from legacy
  configuration is properly migrated.

## 3.1.0 - 26/03/2020
### Added
* Build multi-arch Docker image (`amd64`, `i386`, `arm64`, `armv7`, `armv6`, `ppc64le` and `s390x`),
  with the help of @patrickpissurno and @a16bitsysop.

### Changed
* Use Alpine as base image again (3.11)
* Update Lexicon to 3.3.19 (improvments for SafeDNS and DigitalOcean providers)

## 3.0.2 - 24/03/2020
### Added
* Allow to define octal values of `acme.dirs_mode` and `acme.files_mode` as strings
  (eg `"0755"`) in the YAML configuration file
  
### Changed
* Improve the User Guide (@Neejoh with #84)

## 3.0.1 - 19/03/2020
### Added
* Add Docker CLI

### Changed
* Update Lexicon to 3.3.18 (fix Hetzner provider)

## 3.0.0 - 18/03/2020
### Added
* Complete refactoring of former `adferrand/letsencrypt-dns` into DNSroboCert. Docker image is now
  `adferrand/dnsrobocer` and is available in DockerHub. Standalone tool is installable through PyPI at
  https://pypi.org/project/dnsrobocert/.
* DNSroboCert does not use environment variables + `domains.conf` anymore. If you come from the
  `adferrand/letsencrypt-dns` Docker image, the corresponding YAML configuration file is dynamically
  generated at `/etc/dnsrobocert/config.yml`. Please see
  https://dnsrobocert.readthedocs.io/en/latest/miscellaneous.html#migration-from-docker-letsencrypt-dns
  for more details.
* Complete CI/CD flow, with unit/integration tests, code quality, type checking and automated deployment.
* New features (configurable with `config.yml`, not legacy configuration):
    * you can now define multiple DNS providers in one single instance of DNSroboCert
    * the custom deploy scripts and PFX exports are defined per certificate
    * force renew can be set for specific certificates
  
## Changed
* Along with migration to DNSroboCert, all bash files are rewritten into Python.
* Certificate renewal is not handled automatically anymore by an external cron task, but by DNSroboCert directly.

## Removed
* Configuration of certificate renewal frequency has been removed.

## 2.23.0 - 04/03/2020
### Changed
* Update Certbot to 1.3.0: automated handling for https://community.letsencrypt.org/t/revoking-certain-certificates-on-march-4/114864

## 2.22.0 - 07/02/2020
### Changed
* Update Lexicon to 3.3.17: support private domains and add Gransy provider, that generalize and replace Subreg.
* Update Certbot to 1.2.0: remove POST-as-GET fallback

## 2.21.0 - 10/01/2020
### Changed
* Update Lexicon to 3.3.14 (add EUServ)
* Update base image to Alpine 3.11 and Python 3.8

## 2.20.0 - 07/12/2019
### Changed
* Update Lexicon to 3.3.11 (add HostingDE, RcodeZero)
* Update Certbot to 1.0.0

## 2.19.0 - 04/11/2019
### Changed
* Update Lexicon to 3.3.8 (add HostingDE, RcodeZero)
* Update Certbot to 0.39.0

## 2.18.0 - 25/09/2019
### Changed
* Update Lexicon to 3.3.3 (add DirectAdmin provider)
* Update Certbot to 0.38.0 (forward support to Python 3.8)

## 2.17.0 - 25/08/2019
### Added
* Create a docker-compose.yml template, that can be configured by environment variables (@mgh87 #41)
* Pre-generation of a `domain.conf` to avoid the creation of a directory when `domain.conf` is
  host mounted from a non existent path (@Akkarine #60)

### Changed
* Update Lexicon to 3.3.2 that fixes Yandex provider
* Update Certbot to 0.37.2 (various fixes)
* Various corrections in `README.md` (@Akkarine #60)

## 2.16.0 - 17/07/2019
### Changed
* Update Lexicon to 3.3.1 (add SafeDNS, Dreamhost, Dinahosting)
* Update Certbot to 0.36.0 (various fixes)
* Update base image to Alpine 3.10

## 2.15.0 - 19/06/2019
### Changed
* Update Lexicon to 3.2.7 (add Aliyun, Azure DNS and GratisDNS providers)
* Update Certbot to 0.35.1 (various fixes)

## 2.14.1 - 27/05/2019
### Changed
* Certbot's work dir and logs dir are now set to be in the config dir `/etc/letsencrypt` (respectively under
  `work` and `logs`). This allows to persist both certbot backups and logs.

## 2.14.0 - 14/05/2019
### Added
* First implementation of autorestart feature in a Docker cluster:
  using environment variable `DOCKER_CLUSTER_PROVIDER (default: none)`, the container will use appropriate
  service restart command to restart the service name specified in `autorestart-containers=...` directive.
  For now, only Swarm is supported: support is triggered using `DOCKER_CLUSTER_PROVIDER=swarm`.

### Changed
* Python libraries uses now the pip option --no-cache-dir to reduce container footprints.
* The autorestart and autocmd directives are now triggered upon certificate renewal as before, but also
  upon first certificate issuance now.

## 2.13.0 - 14/05/2019
### Added
* Environment variables `CRON_TIME_STRING (default: "12 01,13 * * *")` and `TZ (default: UTC)` allow to control
  at which frequency, and on which timezone the renewal cron job will be executed. By default it is twice a day,
  at midday and midnight UTC.

### Changed
* Update Lexicon to 3.2.5
* Update Certbot to 0.34.2

## 2.12.0 - 28/04/2019
### Added
* Environment variable `DEPLOY_HOOK` (default: _empty_) can be set to execute a shell command when a certificate
  is created or renewed. This deploy command can be used for instance to do some post-process formatting on the
  certificates before their deployment on a service requiring a specific certificate format.

## Changed
* Update Lexicon to 3.2.4 (new providers: Netcup)

## 2.11.0 - 10/04/2019
### Added
* Environment variable `LETSENCRYPT_SKIP_REGISTER` (default: `false`) can be set to `true` and avoid the container
  to try to register a new account against Let'sEncrypt servers: useful for instance if the container is already
  attached to a letsencrypt configuration folder with an existing account.
* By modifying the `run.sh` script, the container now responds to interruption signals and proceed to shutdown by
  itself, without the need from the Docker daemon to kill it.

### Changed
* Update Lexicon to 3.2.1 (various fixes)
* Update Certbot to 0.33.1 (various fixes)

## 2.10.1 - 10/03/2019
### Changed
* Use `full` extra of Lexicon PyPI package to ensure all providers have their optional dependencies fulfilled.

## 2.10.0 - 09/03/2019
### Changed
* Update base image to Alpine 3.9
* Update Lexicon to 3.1.6 (new providers: Hover, Zilore)
* Update Certbot to 0.32.0

## 2.9.0 - 20/01/2019
### Added
* Ignore README file in /etc/letsencrypt/live

### Changed
* Update Lexicon to 3.0.8
* Update Certbot to 0.30.0

## 2.8.0 - 27/12/2018
### Added
* Support new providers thanks to Lexicon update: Internet.bs, Hetzner

### Changed
* Update Lexicon to 3.0.7
* Update Certbot to 0.29.1

## 2.7.0 - 26/11/2018
### Added
* Support new providers thanks to Lexicon update: Auto (dns provider auto-resolution), ConoHa, NFSN, Easyname, LocalZone (bind9)
* Allow to configure the DNS API connection using YAML files, thanks to the new configuration system of Lexicon 3

### Changed
* Update Lexicon to 3.0.2
* Update Certbot to 0.28.0
* README.md updated to refer to YAML files, update environment variable parsing

## 2.6.1 - 27/09/2018
### Added
* Support new providers thanks to Lexicon update: Plesk, Inwx, Hurricane Electric

### Changed
* Update Lexicon to 2.7.9

## 2.6.0 - 17/09/2018
### Added
* Continuous integration/deployment is now handled by CircleCI to allow more advanced strategies and faster builds
* Add and configure Circus, an alternative to Supervisor, compatible with Python 3, with better control over environment variables propagation, and network sockets supervision (not used yet here)

### Changed
* Update base image to Alpine 3.8
* Update Lexicon to 2.7.3
* Update Certbot to 0.27.1

### Removed
* Docker Hub "Automated build" is disabled in favor of CircleCI
* Remove Supervisor and its configuration (in favor of Circus)

## 2.5.3 - 01/09/2018
### Added
* `LEXICON_OPTIONS` was added to the cleanup script #29

## 2.5.2 - 08/08/2018
### Changed
* Avoid to mark `domains.conf` as edited on each watch loop

## 2.5.1 - 08/08/2018
### Changed
* Correct `domains.conf` parsing for particular cases (wildcard domains on the last line of the file)

## 2.5.0 - 19/07/2018
### Changed
* Upgrade Certbot to 0.26.1
* Upgrade Lexicon to 2.7.0, with extended security support for Subreg
* Correct certificate revocation for some formatting for `domains.conf`

## 2.4.0 - 15/07/2018
### Changed
* Upgrade Certbot to 0.26.0
* Upgrade Lexicon to 2.6.0, including new DNS providers: ExoScale, Zeit, and Google Cloud DNS

## 2.3.1 - 25/06/2018
### Changed
* Upgrade Lexicon to 2.4.4, with support of Online.net provider

## 2.3.0 - 17/06/2018
### Added
* Add Lexicon dependencies for Subreg provider

### Changed
* Upgrade Certbot to 0.25.1
* Upgrade Lexicon to 2.4.3, with a lot of bugfixes for some providers (OVH, GoDaddy, Gandi), and support to the Gandi LiveDNS API

## 2.2.0 - 05/06/2018
### Added
Add `LEXICON_OPTIONS` environment variable for specific lexicon options

### Changed
* Upgrade Certbot to version 0.24.0
* Upgrade Lexicon to version 2.3.0: a lot of stability improvments, in particular for Namecheap provider, and added providers Constellix, Linode V4 and Subreg
* Correct `domains.conf` parsing when there is no newline on the end of the file
* Improved documentation

### Removed
* Removed unsused code

## 2.1.0 - 22/04/2018
### Added
* Add `LEXICON_PROVIDER_OPTIONS` environment variable to pass DNS provider authentication parameters directly to lexicon executable

### Changed
* Update Certbot to 0.23.0

## 2.0.1 - 14/04/2018
### Changed
* Correct autocmd/autorestart behavior with wildcard certificates
* Correct wrongly revokation of wilcard certificates after their creation

## 2.0.0 - 27/03/2018
### Added
* Connect to the ACME v2 servers, which allow wildcard certificates generation (eg. *.example.com)
* Allow use of old ACME v1 servers through `LEXICON_ACME_V1` environment variable
* Clean autocmd/autorestart jobs on the live container when needed

### Changed
* Update Certbot to 0.22.2 to supports the ACME v2 servers
* Update Lexicon to 0.22.1 adding support for following DNS providers: AuroraDNS, Gehirn Infrastructure Service, OnApp and Sakura Cloud
* Correct deploy hook about files/directory permission fixation
