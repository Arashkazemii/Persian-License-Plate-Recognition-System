# Quarantined model checkpoints

The application uses `best detector.pt` for plate localization and `best ocr.pt`
for character detection. Checkpoint binaries have been removed from all rewritten
local branches, tags, and PR refs pending provenance clearance. Both generations
are preserved outside Git in the maintainer's private cleanup backup; the current
pair also remains in the ignored local `models/` directory for existing inference.
No checkpoint bytes were modified. A fresh clone does not contain weights and
there is no cleared public download. GitHub still has the old history until the
separately coordinated push and server-side cleanup.

## Audit scope and limits

On 2026-10-01, all 33 commits reachable from the repository's six public branches
and two tags were inspected. The ten advertised pull-request heads are already
contained in that history. There are two historical versions of each checkpoint.
The ZIP containers and pickle instructions were inspected statically; this audit
did not unpickle, import checkpoint globals, execute reducers, or load tensor data.
The working-tree hashes match the checkpoints at `a93bd4c`.

Metadata is evidence of what an artifact records, not authenticated evidence of
who trained it, what images were used, or what rights its uploader owns. Stored
dates have no timezone. No trained model file was changed.

## Current checkpoints

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| best detector.pt | 51,170,258 | `7cd7c5db4785a3ab20554544bc825b7798ebb99231e9a2cb0e140739a070d42e` |
| best ocr.pt | 51,240,530 | `afef2a311970d1b6394f9e04a183030f21238122b55b61f231fa1a0912b20132` |

Both current checkpoints record:

- `version: 8.3.55` and `ultralytics.nn.tasks.DetectionModel`.
- YOLO11 architecture metadata: scale `l`, `yolo11l.yaml`, and modules including
  `C3k2` and `C2PSA`. Their stored `train_args.model` is `yolo11l.pt`.
- `task: detect`, `pretrained: true`, `epochs: 50`, `batch: 16`, `imgsz: 640`,
  `optimizer: auto`, `seed: 0`, and `resume: false`.
- An absolute local dataset-path reference whose basename is `dataset.yaml`.
  This YAML is not in any inspected repository revision. The filename does not
  identify a dataset, source, version, license, or train/validation split.
- `license: AGPL-3.0 (https://ultralytics.com/license)` and an upstream docs link.
  This corrects the earlier incomplete inspection that reported no license marker.
  The same license string is automatically written by the
  [Ultralytics 8.3.55 checkpoint-saving code](https://github.com/ultralytics/ultralytics/blob/v8.3.55/ultralytics/engine/trainer.py).
  It does **not** prove the trainer owned the data or had permission to relicense
  any third-party weights.
- `epoch: -1`, with optimizer and EMA fields cleared. The artifacts contain
  `train_metrics` and `train_results`, including 50 stored epoch entries. These
  are unauthenticated embedded training records, not independently verified
  benchmarks; no accuracy or latency claim is made here.

| Artifact | Stored date (timezone unknown) | Stored classes |
| --- | --- | --- |
| best detector.pt | `2025-01-14T13:16:12.632881` | 1: `License_Plate` |
| best ocr.pt | `2025-01-08T13:42:11.893578` | 31 character-detection labels |

The OCR checkpoint's indexed labels match the existing 31-entry `charmap` in
`app.py` exactly, including its descriptive Persian labels. This is a detection
model used for characters, not a separate sequence-recognition architecture.
It does not establish coverage or accuracy for all Persian plate formats.

The architecture agrees with the
[versioned upstream YOLO11 configuration](https://github.com/ultralytics/ultralytics/blob/v8.3.55/ultralytics/cfg/models/11/yolo11.yaml).
The base-weight filename and `pretrained: true` are evidence of recorded training
configuration only. The exact starting checkpoint, download URL, checksum, and
upstream training dataset are **unknown**; do not assume official COCO weights
solely from the filename.

## Original repository history (before cleanup)

The commit IDs below identify the original history retained in the private backup,
not commits/checkpoints available in the rewritten repository. The original remote
has not yet been updated.

- `771efeeab5545f20546b0ad4fa9411476e0e3559` (2025-05-01) first committed
  the two smaller checkpoints. Both record Ultralytics `8.3.55`, scale `n`,
  `yolo11n.yaml`, base-weight reference `yolo11n.pt`, `pretrained: true`,
  `dataset.yaml`, and the same upstream AGPL metadata. Their classes are the
  same one detector class and 31 OCR labels as the current artifacts.
- `2a7f671c9465f74cfc0ef7a2a0fc74131785071e` changed the application loader
  from `torch.hub.load` / YOLOv5 to `ultralytics.YOLO`. It did not replace model
  bytes. Thus the older README/loader's YOLOv5 wording is not proof these
  checkpoints were trained with YOLOv5; both older artifacts identify YOLO11n.
- `725bf604df9d3280f2f3ce9f86ccd2876baddb0d` (2025-05-08) replaced both
  files with the current YOLO11l artifacts. Other still-advertised branches retain
  the older pair in the original history. Both generations were removed from the
  rewritten history and require clearance before any future redistribution.

| Earlier artifact | Bytes | Stored date | SHA-256 |
| --- | ---: | --- | --- |
| best detector.pt (nano) | 5,447,059 | `2024-12-31T12:06:36.926161` | `273a83d26eebe20c1d5dd816ac2706783e47ee1756eb2ffcccd6647c27ee86ee` |
| best ocr.pt (nano) | 5,482,771 | `2024-12-31T14:12:36.064766` | `de1ff8d416da5f6724569a0b726af9db75716e19b81faa0315d35216dcef9ece` |

Historical requirements did not pin Ultralytics or PyTorch. The current
`ultralytics==8.4.170` inference dependency is not the recorded training version.
No training script/notebook, dataset manifest, dataset license, original
base-weight checksum, model-specific rights statement, or authenticated trainer
identity was found in the inspected history. Git authorship and uploading a file
are not proof of model authorship. Original Python/PyTorch/CUDA versions, custom
training-code modifications, and dataset provenance remain unknown.

## Information the maintainer must provide before public redistribution

Provide evidence **for each of the four hashes above**, or explicitly confirm and
document a shared provenance chain where applicable:

1. **Trainer and authority:** who trained it; whether it was your own work or
   downloaded; original artifact URL if downloaded; employer/client/coauthor
   permissions; and evidence that the rights holder authorizes AGPL-compatible
   redistribution. An uploader name is insufficient.
2. **Starting weights:** exact `yolo11l.pt` / `yolo11n.pt` source, release/version,
   SHA-256, original license and notices, any intermediate fine-tuning checkpoints,
   and whether enterprise or other contractual terms applied. A matching filename
   is insufficient.
3. **Training data:** actual detector and OCR `dataset.yaml` files (with private
   filesystem paths removed), dataset sources/versions, license texts or written
   permissions, and terms permitting the training and redistribution of derived
   weights. Identify any noncommercial, research-only, attribution, or share-alike
   restrictions. Explain consent/privacy/anonymization handling for plate images
   and personal data; do not publish private data to satisfy this checklist.
4. **Training source and environment:** original scripts/notebooks and commands,
   configuration, preprocessing/labeling code, exact dependency versions and any
   upstream fork/patch, plus available original run logs. Publish the corresponding
   source and notices needed for the applicable license. Determine the required
   scope of data/material disclosure from the actual terms, not assumptions.
5. **Artifact license:** an explicit model-specific rights/license notice and
   attribution chain, reconciled with the upstream AGPL metadata and dataset/base
   weight terms. If these conflict or authority is unclear, obtain permission or
   qualified legal review before distributing the artifacts.

Verified evaluation is useful for a model card but is not a substitute for these
rights checks. Supported formats and performance remain unverified.

Ultralytics states that its trained models are AGPL-3.0 by default unless separately
licensed: [upstream licensing](https://www.ultralytics.com/license). AGPL-compatible
application dependencies do not establish rights to unknown datasets or third-party
weights. The application's source grant does not independently relicense these
artifacts. **Redistribution clearance remains unresolved**, including older copies
in backups and the unchanged remote history. Keep private artifacts unchanged;
do not publish a model bundle until the missing evidence is supplied and reviewed.

Only load trusted checkpoints. `.pt` files may contain executable serialized Python
objects; a hash identifies a file but does not prove it is safe or licensed.
