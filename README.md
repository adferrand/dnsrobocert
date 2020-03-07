# patrickpissurno/rpi-docker-letsencrypt-dns
[![build status](https://travis-ci.org/patrickpissurno/rpi-docker-letsencrypt-dns.svg?branch=master)](https://travis-ci.org/patrickpissurno/rpi-docker-letsencrypt-dns)
[![](https://img.shields.io/docker/pulls/patrickpissurno/rpi-docker-letsencrypt-dns.svg)](https://hub.docker.com/r/patrickpissurno/rpi-docker-letsencrypt-dns "Click to view the image on Docker Hub")
[![license](https://img.shields.io/github/license/patrickpissurno/rpi-docker-letsencrypt-dns?maxAge=1800)](https://github.com/patrickpissurno/rpi-docker-letsencrypt-dns/blob/master/LICENSE)

Automated daily multiarch builds for [docker-letsencrypt-dns](https://github.com/adferrand/docker-letsencrypt-dns), supporting:
- amd64
- arm64
- armhf (armv7)

An up-to-date version of the [upstream source code](https://github.com/adferrand/docker-letsencrypt-dns) is fetched, built and released to my [Docker Hub](https://hub.docker.com/r/patrickpissurno/rpi-docker-letsencrypt-dns) daily (automated via [Travis CI](https://travis-ci.org/patrickpissurno/rpi-docker-letsencrypt-dns/)).

### Does it work with the Raspberry Pi?
**Yes!** In fact the 'rpi' in this repo's name stands for 'Raspberry Pi'. This image is multiarch and **should support** both Pi 2, Pi 3 and Pi 4 (both armv7 and arm64). However, I have only tested it on my Pi 4 running Ubuntu (arm64). Give it a try!

### Usage
Take a look at the [upstream repo](https://github.com/adferrand/docker-letsencrypt-dns) for usage instructions, it works exactly the same way. You just have to replace every `adferrand/letsencrypt-dns` occurrence with `patrickpissurno/rpi-docker-letsencrypt-dns`.

### TL;DR
`docker pull patrickpissurno/rpi-docker-letsencrypt-dns`

### Special Thanks
I'd like to thank [Travis CI](https://travis-ci.org/patrickpissurno/rpi-docker-letsencrypt-dns/) for providing their service for free. The building proccess for this image takes an excruciating long amount of time (around 2h). This wouldn't be possible if it weren't for them.
