# Continuum Community Edition source boundary

This repository is the public integration and local-run distribution for the
Continuum memory engine. Release Compose files use the versioned backend image
published by the Community Edition workflow. A remote source build, pinned by
`SYNTARUS_ENGINE_REF`, remains available as a contributor fallback. This keeps
the Continuum distribution small, reproducible, and separate from hosted
control-plane code and benchmark data.

To test a later compatible engine revision, set `SYNTARUS_ENGINE_REF` in `.env`
to a reviewed commit before a source build. The default is the revision tested
with this release. To use a private image mirror, set
`SYNTARUS_BACKEND_IMAGE` and `SYNTARUS_CONSOLE_IMAGE`.

The SDK in `sdk/` is distributed under the MIT license. See `LICENSE` and
`sdk/LICENSE` for terms.
