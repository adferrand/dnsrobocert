# Changelog

## [2.22.0 - 07/02/2020]
### Modified
* Update Lexicon to 3.3.17: support private domains and add Gransy provider, that generalize and replace Subreg.
* Update Certbot to 1.2.0: remove POST-as-GET fallback

## [2.21.0 - 10/01/2020]
### Modified
* Update Lexicon to 3.3.14 (add EUServ)
* Update base image to Alpine 3.11 and Python 3.8

## [2.20.0 - 07/12/2019]
### Modified
* Update Lexicon to 3.3.11 (add HostingDE, RcodeZero)
* Update Certbot to 1.0.0

## [2.19.0 - 04/11/2019]
### Modified
* Update Lexicon to 3.3.8 (add HostingDE, RcodeZero)
* Update Certbot to 0.39.0

## [2.18.0 - 25/09/2019]
### Modified
* Update Lexicon to 3.3.3 (add DirectAdmin provider)
* Update Certbot to 0.38.0 (forward support to Python 3.8)

## [2.17.0] - 25/08/2019
### Added
* Create a docker-compose.yml template, that can be configured by environment variables (@mgh87 #41)
* Pre-generation of a `domain.conf` to avoid the creation of a directory when `domain.conf` is
  host mounted from a non existent path (@Akkarine #60)

### Modified
* Update Lexicon to 3.3.2 that fixes Yandex provider
* Update Certbot to 0.37.2 (various fixes)
* Various corrections in `README.md` (@Akkarine #60)

## [2.16.0] - 17/07/2019
### Modified
* Update Lexicon to 3.3.1 (add SafeDNS, Dreamhost, Dinahosting)
* Update Certbot to 0.36.0 (various fixes)
* Update base image to Alpine 3.10

## [2.15.0] - 19/06/2019
### Modified
* Update Lexicon to 3.2.7 (add Aliyun, Azure DNS and GratisDNS providers)
* Update Certbot to 0.35.1 (various fixes)

## [2.14.1] - 27/05/2019
### Modified
* Certbot's work dir and logs dir are now set to be in the config dir `/etc/letsencrypt` (respectively under
  `work` and `logs`). This allows to persist both certbot backups and logs.

## [2.14.0] - 14/05/2019
### Added
* First implementation of autorestart feature in a Docker cluster:
  using environment variable `DOCKER_CLUSTER_PROVIDER (default: none)`, the container will use appropriate
  service restart command to restart the service name specified in `autorestart-containers=...` directive.
  For now, only Swarm is supported: support is triggered using `DOCKER_CLUSTER_PROVIDER=swarm`.

### Modified
* Python libraries uses now the pip option --no-cache-dir to reduce container footprints.
* The autorestart and autocmd directives are now triggered upon certificate renewal as before, but also
  upon first certificate issuance now.

## [2.13.0] - 14/05/2019
### Added
* Environment variables `CRON_TIME_STRING (default: "12 01,13 * * *")` and `TZ (default: UTC)` allow to control
  at which frequency, and on which timezone the renewal cron job will be executed. By default it is twice a day,
  at midday and midnight UTC.

### Modified
* Update Lexicon to 3.2.5
* Update Certbot to 0.34.2

## [2.12.0] - 28/04/2019
### Added
* Environment variable `DEPLOY_HOOK` (default: _empty_) can be set to execute a shell command when a certificate
  is created or renewed. This deploy command can be used for instance to do some post-process formatting on the
  certificates before their deployment on a service requiring a specific certificate format.

## Modified
* Update Lexicon to 3.2.4 (new providers: Netcup)

## [2.11.0] - 10/04/2019
### Added
* Environment variable `LETSENCRYPT_SKIP_REGISTER` (default: `false`) can be set to `true` and avoid the container
  to try to register a new account against Let'sEncrypt servers: useful for instance if the container is already
  attached to a letsencrypt configuration folder with an existing account.
* By modifying the `run.sh` script, the container now responds to interruption signals and proceed to shutdown by
  itself, without the need from the Docker daemon to kill it.

### Modified
* Update Lexicon to 3.2.1 (various fixes)
* Update Certbot to 0.33.1 (various fixes)

## [2.10.1] - 10/03/2019
### Modified
* Use `full` extra of Lexicon PyPI package to ensure all providers have their optional dependencies fulfilled.

## [2.10.0] - 09/03/2019
### Modified
* Update base image to Alpine 3.9
* Update Lexicon to 3.1.6 (new providers: Hover, Zilore)
* Update Certbot to 0.32.0

## [2.9.0] - 20/01/2019
### Added
* Ignore README file in /etc/letsencrypt/live

### Modified
* Update Lexicon to 3.0.8
* Update Certbot to 0.30.0

## [2.8.0] - 27/12/2018
### Added
* Support new providers thanks to Lexicon update: Internet.bs, Hetzner

### Modified
* Update Lexicon to 3.0.7
* Update Certbot to 0.29.1

## [2.7.0] - 26/11/2018
### Added
* Support new providers thanks to Lexicon update: Auto (dns provider auto-resolution), ConoHa, NFSN, Easyname, LocalZone (bind9)
* Allow to configure the DNS API connection using YAML files, thanks to the new configuration system of Lexicon 3

### Modified
* Update Lexicon to 3.0.2
* Update Certbot to 0.28.0
* README.md updated to refer to YAML files, update environment variable parsing

## [2.6.1] - 27/09/2018
### Added
* Support new providers thanks to Lexicon update: Plesk, Inwx, Hurricane Electric

### Modified
* Update Lexicon to 2.7.9

## [2.6.0] - 17/09/2018
### Added
* Continuous integration/deployment is now handled by CircleCI to allow more advanced strategies and faster builds
* Add and configure Circus, an alternative to Supervisor, compatible with Python 3, with better control over environment variables propagation, and network sockets supervision (not used yet here)

### Modified
* Update base image to Alpine 3.8
* Update Lexicon to 2.7.3
* Update Certbot to 0.27.1

### Removed
* Docker Hub "Automated build" is disabled in favor of CircleCI
* Remove Supervisor and its configuration (in favor of Circus)

## [2.5.3] - 01/09/2018
### Added
* `LEXICON_OPTIONS` was added to the cleanup script #29

## [2.5.2] - 08/08/2018
### Changed
* Avoid to mark `domains.conf` as edited on each watch loop

## [2.5.1] - 08/08/2018
### Changed
* Correct `domains.conf` parsing for particular cases (wildcard domains on the last line of the file)

## [2.5.0] - 19/07/2018
### Changed
* Upgrade Certbot to 0.26.1
* Upgrade Lexicon to 2.7.0, with extended security support for Subreg
* Correct certificate revocation for some formatting for `domains.conf`

## [2.4.0] - 15/07/2018
### Changed
* Upgrade Certbot to 0.26.0
* Upgrade Lexicon to 2.6.0, including new DNS providers: ExoScale, Zeit, and Google Cloud DNS

## [2.3.1] - 25/06/2018
### Changed
* Upgrade Lexicon to 2.4.4, with support of Online.net provider

## [2.3.0] - 17/06/2018
### Added
* Add Lexicon dependencies for Subreg provider

### Changed
* Upgrade Certbot to 0.25.1
* Upgrade Lexicon to 2.4.3, with a lot of bugfixes for some providers (OVH, GoDaddy, Gandi), and support to the Gandi LiveDNS API

## [2.2.0] - 05/06/2018
### Added
Add `LEXICON_OPTIONS` environment variable for specific lexicon options

### Changed
* Upgrade Certbot to version 0.24.0
* Upgrade Lexicon to version 2.3.0: a lot of stability improvments, in particular for Namecheap provider, and added providers Constellix, Linode V4 and Subreg
* Correct `domains.conf` parsing when there is no newline on the end of the file
* Improved documentation

### Removed
* Removed unsused code

## [2.1.0] - 22/04/2018
### Added
* Add `LEXICON_PROVIDER_OPTIONS` environment variable to pass DNS provider authentication parameters directly to lexicon executable

### Modified
* Update Certbot to 0.23.0

## [2.0.1] - 14/04/2018
### Changed
* Correct autocmd/autorestart behavior with wildcard certificates
* Correct wrongly revokation of wilcard certificates after their creation

## [2.0.0] - 27/03/2018
### Added
* Connect to the ACME v2 servers, which allow wildcard certificates generation (eg. *.example.com)
* Allow use of old ACME v1 servers through `LEXICON_ACME_V1` environment variable
* Clean autocmd/autorestart jobs on the live container when needed

### Modified
* Update Certbot to 0.22.2 to supports the ACME v2 servers
* Update Lexicon to 0.22.1 adding support for following DNS providers: AuroraDNS, Gehirn Infrastructure Service, OnApp and Sakura Cloud
* Correct deploy hook about files/directory permission fixation
