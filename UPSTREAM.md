# Community Edition source boundary

This repository is the public integration and local-run distribution for the
Syntarus Memory Engine. The Compose file pins the tested engine image source to
the `SYNTARUS_ENGINE_REF` commit in the upstream MemoryOS repository. This keeps
the Community Edition small, reproducible, and separate from hosted control
plane code and benchmark data.

To use a later compatible engine revision, set `SYNTARUS_ENGINE_REF` in `.env`
to a reviewed commit before building. The default is the revision tested with
this release.

The SDK in `sdk/` is distributed under the MIT license. See `LICENSE` and
`sdk/LICENSE` for terms.
