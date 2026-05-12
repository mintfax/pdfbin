# pdfbin

Source repo for pdfbin.net - a CC0 library of test PDFs at stable flat URLs.
See `docs/superpowers/specs/2026-05-12-pdfbin-net-design.md` for the design.

## Working rules

- Commit and push after every change.
- Do not run `hugo server`. A one-shot `hugo --minify` is fine and is how you
  refresh the preview - Caddy serves `public/` publicly at
  https://pdfbin.example.dev. Rebuild after each push to verify.
- The Python pipeline regenerates everything. Run `python -m generate.pipeline`
  from the repo root. Output lives in `static/` (PDFs + catalog.json + llms.txt
  + openapi.json) and in `content/preview/` (one markdown stub per PDF, used
  by Hugo to materialize per-PDF preview pages). CI fails if
  `git diff --exit-code static/ content/preview/` shows drift after a
  regenerate.
- Single-branch flow. `main` is the default branch; every push triggers
  both the build verification and the GH Pages deploy.
- Fixtures are immutable. Never change the bytes at an existing `/<id>.pdf`.
  If a fixture is wrong, add a new ID and mark the old one
  `"status": "deprecated"` in catalog.json with a `superseded_by` pointer.
- Facet vocabularies live in `generate/facets.py` and are the single source
  of truth. Adding a value bumps the catalog schema_version.

## Dev URL

This project's `public/` folder is accessible at https://pdfbin.example.dev (Caddy wildcard route, rebuilt with `hugo --minify`).
