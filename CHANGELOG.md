# Changelog

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
