# Licensing scope and third-party dependencies

Copyright (C) 2024-2026 Arash Kazemi. Application source, documentation, and original
UI assets are offered under AGPL-3.0-only; the full text is in `LICENSE`.
This grant does not assert ownership of third-party dependencies, training data,
or the locally supplied model checkpoints. Model redistribution remains an explicit release
blocker until the maintainer establishes provenance and applicable terms.

The license selection follows [Ultralytics' open-source licensing guidance](https://www.ultralytics.com/license)
and [the AGPL text](https://www.gnu.org/licenses/agpl-3.0.html). Ultralytics is the
copyleft dependency driving this choice; a blanket MIT license for the complete
application would not address its AGPL obligations.

Direct package metadata was checked on 2026-10-01 using the official PyPI JSON API:

| Dependency | Upstream terms | Source |
| --- | --- | --- |
| Flask, python-dotenv | BSD-3-Clause | [Flask](https://github.com/pallets/flask), [dotenv](https://github.com/theskumar/python-dotenv) |
| Pillow | MIT-CMU | [Pillow](https://github.com/python-pillow/Pillow) |
| OpenCV Python wheels | Apache-2.0 plus bundled component notices | [opencv-python](https://github.com/opencv/opencv-python) |
| PyTorch | Apache/BSD/MIT/BSL terms and LLVM exception for bundled components | [PyTorch](https://github.com/pytorch/pytorch) |
| torchvision | BSD-3-Clause | [torchvision](https://github.com/pytorch/vision) |
| Ultralytics | AGPL-3.0 (upstream also offers separate enterprise terms) | [Ultralytics](https://github.com/ultralytics/ultralytics) |
| Waitress | ZPL-2.1 | [Waitress](https://github.com/Pylons/waitress) |
| pytest (development only) | MIT | [pytest](https://github.com/pytest-dev/pytest) |
| setuptools (packaging tool) | MIT | [setuptools](https://github.com/pypa/setuptools) |

These permissive dependency terms do not conflict with licensing the application
under AGPL-3.0; their notices must still be retained when redistributing their
packages. OpenCV wheels include third-party libraries such as FFmpeg; preserve
their shipped licenses and check the actual wheel's notices for your platform.
SQLite is provided by Python's standard library, not a `sqlite3` PyPI requirement.

The dependency list is not a complete transitive software bill of materials or a
legal finding about unknown datasets. Distribution of containers and model bundles
requires checking the actual installed artifacts and completing the model notes.
