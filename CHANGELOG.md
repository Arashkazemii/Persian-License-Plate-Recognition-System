# Changelog

No new release has been created. This file records unreleased changes.

## Unreleased

- Correct setup instructions and describe the actual YOLO11 application without unsupported benchmarks.
- Add AGPL-3.0-only licensing for application source and document unresolved model provenance.
- Stop tracking environment secrets and runtime databases; exclude them from container builds.
- Require explicit credentials, protect forms with CSRF tokens, and protect detection polling.
- Disable debug serving, use Waitress, and repair Compose configuration and persistence.
- Initialize missing databases, handle empty detections, and close streams on disconnect/error.
- Keep model weights, OCR mapping, first-box selection, and duplicate window unchanged.
- Add contributor/security guidance, regression tests, and lightweight CI.
- Rewrite all local public branches/tags to remove historical secrets, databases,
  unconfirmed identity samples, and checkpoint binaries; preserve private backups
  and unchanged model copies. Coordinated GitHub cleanup has not been pushed.
