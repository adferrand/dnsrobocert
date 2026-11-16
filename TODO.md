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
