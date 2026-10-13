# Releasing ZTPU

1. Install the ZLang packages pinned in `contracts/toolchain.json`.
2. Run `make release-check` from a clean branch containing one root commit.
3. Run `make release-package`.
4. Verify the archive and metadata checksums in `build/release/SHA256SUMS`.
5. Create a signed version tag and attach the three files from `build/release/`
   to the GitHub release.

`make release-package` is deterministic for a given commit. It only packages
files tracked at `HEAD`; ignored build output is excluded.

The release tools do not create tags, push commits, or change repository
visibility.
