# Architectural TODO

Items that need design work before implementation. Each one came out of the
project review and was deliberately left out of the bug-fix pass.

## 1. Retry policy after a failed issuance
- **Problem:** in `main._watch_config`, `previous_digest` is updated before
  processing, so a failed issuance is only retried when the config changes or at
  the next scheduled renewal. The loop polls every second, so a naive "retry
  while failing" would hit Let's Encrypt rate limits.
- **To decide:** backoff schedule (per certificate, not global), a cap on
  attempts, and whether failures are surfaced (logs only, or notifications).
- **Touches:** `main.py`, `certbot._issue` (already returns success as a bool).

## 2. Configurable ACME CA and preferred chain
- **Problem:** `certbot._DEFAULT_FLAGS` hardcodes `--preferred-chain "ISRG Root X1"`
  and applies it to `register` and `certonly` for every ACME server, which is
  wrong for other CAs.
- **To decide:** config location (global `acme` vs per certificate), schema
  change, default behaviour for existing users, and EAB support for CAs that need
  it (ZeroSSL, Google).
- **Touches:** `schema.yml`, `certbot.py`, `docs/configuration_reference.rst`.

## 3. `crontab_renew` and `certs_root_path`
- **Problem:** both options are in `schema.yml` and the docs, but nothing reads
  them. Renewal is hardcoded to 00:00 and 12:00 in `background.py`, so user
  values are silently ignored. The docs (around line 350) even rely on
  `crontab_renew`.
- **To decide:** implement them (the `schedule` library has no cron syntax, so
  this means a cron parser or a different scheduler) or deprecate and remove them
  with a migration warning.
- **Touches:** `schema.yml`, `background.py`, `utils.py`, docs.

## 4. Renewal job blocks the scheduler thread
- **Problem:** `background._renew_job` sleeps for up to 6 hours inside the
  scheduler thread. Other jobs are delayed, and the 00:00 and 12:00 runs can
  overlap or stall. `schedule` is also module-global state, so jobs accumulate if
  `worker()` is called more than once, and the thread is neither a daemon nor
  joined.
- **To decide:** apply the jitter when scheduling instead of sleeping in the job,
  or move to a worker with an owned scheduler instance. Define shutdown
  semantics for an in-progress certbot run.
- **Touches:** `background.py`, `main.py`. This depends on item 3.

## 5. Auto-revoke safety
- **Problem:** `certbot._issue` revokes and deletes every lineage in `live/`
  that is not in the config, so an empty `certificates` list revokes everything.
  `os.listdir` on `live/` is also unguarded.
- **To decide:** opt-in or opt-out flag, a guard against an empty list, or a
  dry-run and confirmation step.
- **Touches:** `certbot.py`, `schema.yml`, docs.

## Security follow-ups

Items left over from the security review that were not fixed, either because
they need a decision or because they could not be verified locally.

### 6. Image vulnerability scanning
- **Problem:** the Docker image is not scanned for known vulnerabilities in CI or
  at release time. A local scan was not possible during the review.
- **To decide:** scanner (Trivy or Grype), report-only or blocking, and which
  severities fail the build. Run it once locally first to see the baseline, since
  a blocking gate may fail immediately on unfixed base-image CVEs.
- **Touches:** `.github/workflows/main.yml` (docker job), `release.yml`.

### 7. Container runs as root, no healthcheck
- **Problem:** the image has no `USER` and no `HEALTHCHECK`. Root is partly
  needed for the docker socket and for `chown` of certificates.
- **To decide:** a non-root mode (needs socket group handling and a way to
  chown), and a healthcheck approach (`pgrep` is absent from the slim image, so
  it needs an extra package or a small script).
- **Touches:** `Dockerfile`, `docker/run.sh`, docs.

### 8. Hash-pinned Python dependencies in the image
- **Problem:** `constraints.txt` is exported with `--no-hashes`, so installs are
  not hash-verified. pip does not enforce hashes from a constraints file, and the
  armv7 `sed` pins in the Dockerfile would invalidate them.
- **To decide:** install from a hashed requirements file (`--require-hashes`)
  instead of constraints, and handle armv7 separately (for example its own lock).
- **Touches:** `Dockerfile`.

### 9. Docker client compatibility
- **Problem:** the image now ships Debian's `docker-cli` (26.1.5) instead of the
  latest client. It works with current daemons, but a future daemon that raises
  its minimum API version would break `autorestart` and `autocmd`.
  `autorestart`/`autocmd` were not tested end to end against a real socket.
- **To decide:** add an integration test with a real socket (Docker or Podman),
  and decide how to react if Debian's client lags behind.
- **Touches:** `hooks.py`, `test/`, `Dockerfile`.

### 10. Other secret exposure in output
- **Problem:** config validation errors no longer dump the config, but
  `jsonschema` messages can still embed the offending value (for example a secret
  placed in a field of the wrong type). Lexicon provider errors may include
  request URLs or tokens, and `hooks.main` prints full tracebacks.
- **To decide:** a redaction layer for known secret fields (`provider_options`,
  `pfx.passphrase`), applied to validation messages and hook errors.
- **Touches:** `config.py`, `hooks.py`, `challenge.py`.

### 11. Certificate permission handling
- **Problem:** `utils.fix_permissions` walks with `os.walk` and `chmod`/`chown`
  follow symlinks. This is relied on for `live/` links into `archive/`, but a
  symlink pointing elsewhere would change permissions outside the certificate
  directory. An unknown user raises `KeyError`, while an unknown group is
  silently ignored.
- **To decide:** restrict changes to targets inside the certificate directory,
  and make user and group errors consistent.
- **Touches:** `utils.py`, tests (none exist for `fix_permissions`).

### 12. Windows hook command quoting
- **Problem:** `certbot._hook_cmd` uses `subprocess.list2cmdline` on Windows,
  which is only covered by a POSIX test. It was not run on Windows.
- **To decide:** add a Windows-specific test in the existing CI matrix.
- **Touches:** `test/unit_tests/certbot_test.py`.

### 13. Release and repository settings (manual, outside the code)
- Register a PyPI trusted publisher (repository `adferrand/dnsrobocert`,
  workflow `release.yml`, environment `pypi`), then delete the `PYPI_USERNAME`
  and `PYPI_PASSWORD` secrets.
- Review the open GitHub Dependabot security alerts on the repository.
- Update or archive the `adferrand/letsencrypt-dns` Docker Hub repository now that
  it is no longer published, and consider a final release with a stronger
  deprecation notice.
- `snapcraft.yaml` is still on `base: core20` (end of life) and needs a snap
  build and store check.
