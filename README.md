# patrickpissurno/rpi-docker-letsencrypt-dns
Automated daily multiarch builds for [docker-letsencrypt-dns](https://github.com/adferrand/docker-letsencrypt-dns), supporting:
- amd64
- arm64
- armhf (armv7)

An up-to-date version of the upstream source code is fetched, built and released in my Docker Hub daily (automated via Travis CI).

### Does it work with the Raspberry Pi?
**Yes!** In fact the 'rpi' in this repo's name stands for 'Raspberry Pi'. This image is multiarch and **should support** both Pi 2, Pi 3 and Pi 4 (both armv7 and arm64). However, I have only tested it on my Pi 4 running Ubuntu (arm64). Give it a try!

### Usage
Take a look at the [upstream repo](https://github.com/adferrand/docker-letsencrypt-dns) for usage instructions, it works exactly the same way. You just have to replace every `adferrand/letsencrypt-dns` occurrence with `patrickpissurno/rpi-docker-letsencrypt-dns`.

### TL;DR
`docker pull patrickpissurno/rpi-docker-letsencrypt-dns`

### Special Thanks
I'd like to thank Travis CI for providing their service for free. The building proccess for this image takes an excruciating amount of time. This wouldn't be possible if it weren't for them.
