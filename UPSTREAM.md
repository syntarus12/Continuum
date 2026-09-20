# Continuum Community Edition source boundary

This repository is the public integration and local-run distribution for the
Continuum memory engine. Release Compose files use the versioned backend image
published by the Community Edition workflow. This keeps the Continuum
distribution small, reproducible, and separate from hosted control-plane code
and benchmark data. A monorepo checkout can add
`docker-compose.source.yml` to build the sibling `backend/` source locally;
the public checkout intentionally has no private engine source.

To use a private image mirror, set
`SYNTARUS_BACKEND_IMAGE` and `SYNTARUS_CONSOLE_IMAGE`.

The SDK in `sdk/` is distributed under the MIT license. See `LICENSE` and
`sdk/LICENSE` for terms.
