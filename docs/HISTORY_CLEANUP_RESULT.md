# Local history cleanup

The approved local rewrite was completed on 2026-10-01. This is a record of that
operation, not a claim that GitHub or other copies have been sanitized. No real
push, new release, or new tag has been performed.

## Scope and preservation

`git-filter-repo --sensitive-data-removal --no-fetch` processed all six branches,
two existing tags, and ten advertised PR heads in a fresh private mirror. It removed:

- Historical `.env` files and `database/plates.db`.
- Hardcoded signing keys, application/Oracle passwords, credential-bearing camera
  configuration, and documented default passwords; obsolete Oracle defaults were cleared.
- The 20 identity/plate samples whose synthetic status could not be established.
- All four checkpoint versions at the two model filenames, pending rights clearance.

All 33 original commits were processed; 30 remained after three empty commits were
pruned. Existing authors and dates were preserved. The cleaned main baseline is
`00751613967591e27e0a76831949f9d2495c4e20`; subsequent OSS-readiness commits build on it.
Legacy branch/tag tips retain legacy code, not the new main-branch runtime fixes.

A complete private workspace snapshot, original Git mirror/metadata, commit/ref
maps, detailed audit reports, and original remote-ref leases are retained in the
maintainer's restricted local backup. They contain exposed material and must never
be published or copied into this repository. Both generations of checkpoint files
were preserved outside Git, with unchanged SHA-256 hashes recorded in
[models/README.md](../models/README.md). Current local weights remain ignored.

## Verification limits

At cleanup completion, `git fsck --full` passed and scans covered every local blob
and commit/tag object, including unreachable objects. No old commit objects,
checkpoint/database blobs, forbidden paths, known exposed values or identity
identifiers, recognized API tokens, or private-key blocks were found in clean Git.
These checks do not certify unknown encodings or secrets in image pixels.

Ignore rules allow `.env.example` while excluding private env files, databases,
uploads, checkpoints, and generated local tooling files. Ignores cannot prevent
inline secrets or forced adds. Model/data redistribution remains unresolved.

## Coordinated remote cleanup still required

Rotate exposed credentials outside Git; see [SECURITY.md](../SECURITY.md).
Freeze collaborator changes and check remote tips with `git ls-remote`, without
fetching old history into this clone. Use the privately retained eight-ref atomic
push procedure with exact old-tip leases, first with `--dry-run`. Stop on a stale
lease or protection failure; do not blindly refresh leases or use `--mirror`.
The real push requires separate coordinated approval.

After an authorized push, verify all six remote branches and both existing tags,
scan a fresh clone, restore protections, and arrange collaborator re-clones.
Review artifacts, releases, and forks separately. GitHub's read-only PR refs and
cached views need separate server-side handling where eligible under
[GitHub's sensitive-data removal policy](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
The first changed original commit is `22221a7300881f9fc332fd7b4e19f9c00e64e4b5`;
affected PR heads are 2, 3, 4, 6, 7, 8, 9, 13, 14, and 16. No LFS objects were used.
Server-side purge and erasure of forks/other clones cannot be guaranteed.
