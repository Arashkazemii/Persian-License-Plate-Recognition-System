# Contributing

Small, focused fixes and reproducible bug reports are welcome. Discuss changes to
model outputs, class mappings, datasets, or checkpoints before implementing them.
Do not add weights or camera/plate data without provenance and redistribution rights.

Use Python 3.11 or 3.12 and a virtual environment. Install `requirements-dev.txt`
for web/database tests, or `requirements.txt` as well for actual inference. Configure
your private `.env` as described in README; never commit it.

Before submitting:

```bash
python -m pytest -q
python -m compileall -q app.py database tests
```

Include the problem, intended behavior, and validation in the PR. Tests should
cover regressions and use temporary storage; inference mocks do not establish
recognition accuracy. If changing inference, report results on authorized inputs
and keep the class mapping, thresholds, and checkpoint provenance explicit.

Keep runtime dependencies small and pinned. `sqlite3` belongs to Python's standard
library. Preserve upstream notices and contribute only work you may license under
the application's AGPL-3.0-only terms. The privately preserved models have unresolved
provenance; see `models/README.md`.

Report vulnerabilities privately using `SECURITY.md`. Remove credentials, camera
URLs, identifying plates, and private media from logs, screenshots, and examples.
