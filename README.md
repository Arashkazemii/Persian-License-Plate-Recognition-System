# Persian License Plate Recognition System

A small Flask application that detects Persian license plates and reads their
characters using two local Ultralytics YOLO11 checkpoints. It accepts a camera
source, an uploaded image, or an uploaded video, streams annotated frames to the
browser, and stores recognized plates in SQLite with a five-minute duplicate window.

This is an experimental application. The repository does not contain a published
evaluation dataset, reproducible training pipeline, or verified accuracy/latency
benchmarks. Both configured accounts have the same access; role-based authorization
is not implemented. The detection list in the browser is session-local, not a database viewer.

## Licensing and model provenance

The application source, documentation, and original UI assets are licensed under
[AGPL-3.0-only](LICENSE), consistent with the open-source Ultralytics dependency.
The old requirement to obtain permission before reusing the application source is removed.
Third-party dependencies retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

**Model checkpoints are not distributed in the rewritten Git history.**
Their training data, upstream weights, and redistribution rights still need maintainer
confirmation. [models/README.md](models/README.md) records the evidence and outstanding
questions. Do not describe the complete model bundle as cleared for OSS distribution
until these questions are resolved. No training data is supplied. The source-code
license does not independently relicense privately supplied weights.

## Setup

Use Python 3.11 and Git. Docker is an alternative, not a prerequisite for a local run.
Inference requires two trusted, locally supplied files named `models/best detector.pt`
and `models/best ocr.pt`. They are intentionally absent from Git and ignored to
prevent accidental redistribution. No cleared public download is provided yet.
The maintainer's existing local copies are preserved; a fresh clone can run the
mocked web tests without weights, but cannot perform recognition until authorized
checkpoints are provided.

```bash
git clone https://github.com/Arashkazemii/Persian-License-Plate-Recognition-System.git
cd Persian-License-Plate-Recognition-System
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on Linux/macOS, or
`.\.venv\Scripts\Activate.ps1` in Windows PowerShell.

For a CPU installation on supported platforms, install PyTorch first:

```bash
python -m pip install --upgrade pip setuptools==84.0.0
python -m pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

If those CPU wheels are unavailable on your platform, follow the
[official PyTorch installation instructions](https://pytorch.org/get-started/locally/)
for the pinned versions. CUDA installations need a matching PyTorch/torchvision pair.
Pins cover direct dependencies; transitive dependencies are not a full lockfile.
The checkpoints report Ultralytics 8.3.55; the pinned runtime is newer, so validate
outputs on your own representative inputs before relying on it operationally.

Copy `.env.example` to `.env` (`cp .env.example .env`, or `Copy-Item .env.example .env`
in PowerShell). Fill in `SECRET_KEY`, `USER_1_USERNAME`, and `USER_1_PASSWORD` with
fresh values. There are no default accounts or session keys. Generate a session key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The second account is optional. Keep `.env` private; never paste it into an issue.
`RTSP_URL=0` selects the first local camera. Alternatively, configure an authorized
`rtsp://` or `rtsps://` camera URL. `RTSP_ALLOWED_HOSTS` can restrict destination
hostnames/IPs. Leave `SESSION_COOKIE_SECURE=false` for local HTTP; enable it behind HTTPS.

```bash
python app.py
```

Visit <http://127.0.0.1:5000> and sign in. The app uses Waitress with one process and
four threads, creates a missing database automatically, and loads weights on the
first inference request. Only load trusted `.pt` files: PyTorch checkpoints can
contain executable serialized objects.

## Docker

Configure `.env` and supply the two authorized model files locally first, then:

```bash
docker compose up --build
```

The service is bound to `127.0.0.1:5000`, runs as a non-root user, reads the model
directory as read-only, and stores detections in the `plate-data` named volume.
Secrets, local databases, uploads, and agent indexes are excluded from the build
context, including checkpoint binaries. The private read-only model bind mount
supplies inference weights at runtime. Do not distribute those files or an image
containing them until their rights are cleared. Do not run
`docker compose down --volumes` unless you intend to discard detections.
An RTSP camera is the easiest container input; `0` does not expose a host webcam
inside Docker without platform-specific device configuration.

## Usage and limitations

- Use the input tabs to select a camera, image, or video. Requests changing state
  require the CSRF token supplied by the page. Logout is a POST request.
- Uploaded images are validated and limited to 20 megapixels. Videos accept
  `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, and `.m4v`; codec support depends on OpenCV.
  Request bodies are limited to 100 MB by default (`MAX_UPLOAD_MB`).
- Source selection, models, latest plate, and upload filenames are shared within
  one process. This is a trusted-operator tool, not a multi-tenant service. Do not
  run multiple worker processes or assume accounts isolate detections.
- The existing first-box selection, OCR left-to-right ordering, 31-class mapping,
  eight-character acceptance rule, and YOLO inference defaults are retained.
  The special multi-character class label needs evaluation against actual data;
  changing it requires a model/format decision.
- No login rate limiting or account-management system is provided. Remote use
  needs HTTPS, network controls, and rate limiting. Allowed camera hostnames are
  not a substitute for network egress controls or protection against DNS rebinding.
- Plate data and camera media may be sensitive. Use authorized sources and set
  an appropriate retention policy. The old database has been removed from tracking;
  the local rewritten history removes it, credentials, identity samples, and model
  binaries. GitHub and other copies remain unchanged until coordinated remote cleanup.

## Structure

```text
app.py                 Flask routes, frame processing, lazy model loading
database/database.py   SQLite initialization (database generated locally)
models/                Provenance notes; privately supplied ignored checkpoints
templates/             Login and main page
static/                CSS and browser JavaScript
images/                Historical UI screenshots
tests/                 Web, database, and stream regression tests
.github/               CI and issue/PR templates
```

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use temporary storage and mock inference, so they do not need camera access,
download weights, or measure model accuracy. CI is configured for Python 3.11
and 3.12. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[CHANGELOG.md](CHANGELOG.md). No versioned release is asserted by the UI or changelog.

After installing the full runtime, run `python tests/smoke_models.py` for an optional
CPU check of both checkpoints and a synthetic video upload/stream. It uses temporary
storage and synthetic credentials, leaves the weights unchanged, and is not an accuracy benchmark.

Historical screenshots: [login](images/login-page.png) and [main page](images/main-page.png).
They show the earlier interface, not proof of recognition quality.

For remote deployments, set `SOURCE_URL` to the complete corresponding source of
the version you actually run; the UI links to it and the license. No warranty is provided.
