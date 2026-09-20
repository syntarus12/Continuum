# Community Edition release checklist

1. Review the engine commit in SYNTARUS_ENGINE_REF.
2. Run the local checks:

       docker compose config --quiet
       python -m pip install -e ./sdk
       python -m pytest sdk/tests -q

3. Create a release tag:

       git tag v0.1.0
       git push origin v0.1.0

4. The Publish Community Edition images workflow builds and publishes:

   - ghcr.io/syntarus12/continuum-backend:<tag>
   - ghcr.io/syntarus12/continuum-console:<tag>

5. Set both GHCR packages to public before announcing the release. A clean
   user checkout must be able to pull them without credentials.
6. Verify the clean-install path from a separate directory:

       git clone https://github.com/syntarus12/Continuum.git
       cd Continuum
       ./scripts/start.sh

7. Verify the console, write/search loop, restart persistence, and
   docker compose down -v reset before publishing release notes.

Never publish .env, provider keys, customer data, benchmark datasets, or
production-only backend source in this repository.
