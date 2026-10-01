# Security policy

## Reporting

Email the maintainer at kazemiarash09@gmail.com with the affected commit, impact,
and a minimal reproduction using synthetic data. Do not open a public issue with
credentials, camera URLs, or identifying plates. Use GitHub private vulnerability
reporting if the maintainer has enabled it. There is no promised response SLA or
supported-release schedule; development currently targets the main branch.

## Deployment boundaries

The application is intended for trusted operators on a restricted network. Both
accounts have equal access to one shared video source and detection state. Run
one process. Authentication is environment-configured; there is no login rate
limiting, password recovery, role isolation, or automatic retention policy.

Use fresh random secrets, restrict `.env` permissions, and put remote access behind
HTTPS and rate limiting. Set `SESSION_COOKIE_SECURE=true` for HTTPS. CSRF checks
protect state-changing forms, and all detection endpoints require a login. Never
enable Flask's debug server on an exposed interface.

Authenticated camera selection permits server-side network access. Configure
`RTSP_ALLOWED_HOSTS` and enforce network egress restrictions; host checking alone
does not prevent DNS rebinding. Media decoding and inference consume resources:
upload limits are not a sandbox. Keep dependencies patched and do not accept
untrusted operators or model checkpoints. OpenCV/FFmpeg may log camera details;
treat backend stderr and operational logs as sensitive even though application
messages avoid echoing source URLs.

## Known historical exposure and publication checklist

Before public distribution, rotate/revoke:

- Both application account passwords committed in `.env`, and any reuse elsewhere.
- Camera/RTSP credentials embedded in the committed URL, if still valid.
- The old hardcoded Flask signing key; set a new `SECRET_KEY` and invalidate old sessions.
- Historical Oracle database/container passwords in early Compose configuration,
  if they were ever deployed or reused.

No unmasked API token/private key was detected by the local pattern review of
reachable text blobs. This is not a guarantee that every form of secret is absent.
Generated local agent/index files are excluded from Git and Docker builds.

The approved local rewrite removes `.env`, `database/plates.db`, hardcoded/example
credentials, the 20 unconfirmed identity samples, and all checkpoint binaries from
all six branches and two tags. Local PR refs were rewritten too. Rotation remains
required and is managed outside Git. No push was performed: GitHub, forks, cached
views, and other clones still require coordinated cleanup. See
`docs/HISTORY_CLEANUP_RESULT.md` for verification and the push procedure.

The private backup deliberately retains exposed data for recovery. Do not upload
or share it, and restrict its access. Ignore rules prevent ordinary adds of env,
database, and model files but are not protection against inline secrets or forced adds.
