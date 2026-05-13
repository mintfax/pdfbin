# pdfbin

Source repository for [pdfbin.net](https://pdfbin.net) - a free CC0 library of
test PDFs at stable URLs you can drop into your test suite.

Built by [mintfax](https://mintfax.com), a developer-first fax API.

Each PDF does one specific thing: it's clean, or corrupt in a known way, or
encrypted with a documented password, or oversized, or PDF/A compliant, or a
scan, or a form, or shaped like a real-world document (fax cover, invoice,
IRS 1040, lab report). Every PDF carries typed facet metadata so the same
PDF is discoverable along multiple axes.

URLs are flat and immutable. The bytes at `/<id>.pdf` today are the same
bytes there next year. If a PDF turns out to be wrong, a new ID ships and the
old one stays.

## Discovery surfaces

- https://pdfbin.net/                  HTML index, multi-view
- https://pdfbin.net/catalog.json      typed catalog with facets per PDF
- https://pdfbin.net/openapi.json      OpenAPI 3.1 spec
- https://pdfbin.net/llms.txt          AI-agent summary
- https://pdfbin.net/preview/<id>/     per-PDF preview page with metadata

## License

All PDFs CC0-1.0. Site and pipeline code MIT.

## Working with this repo

See `CLAUDE.md` for working rules. See `docs/superpowers/specs/` for the
design spec and `docs/superpowers/plans/` for the implementation plan.

Note on terminology: user-facing copy uses "PDFs" / "test PDFs". Code-level
identifiers (the `FixtureRecord` class, the `fixtures` array in catalog.json,
test function names) keep "fixture" because it's the precise programming term
for what these objects are in a test-suite context.

## Development

```bash
# Install Python deps
pip install -r requirements.txt

# Regenerate every fixture + catalog.json + llms.txt + openapi.json
# and content/preview/<id>.md stubs.
python -m generate.pipeline

# Build the Hugo site (output to ./public/).
hugo --minify

# Run tests
pytest
```

System dependencies (also handled by the CI Dockerfile):

- `qpdf` (used by pikepdf for encryption)
- `ghostscript` (used for PDF/A generation and scan rasterization)

CI fails if `git diff --exit-code static/ content/preview/` shows drift after
a regenerate. Regenerate locally and commit.

Single-branch flow:

- `main` is the default branch. Every push triggers both the `build`
  workflow (pytest, catalog-shape check, Hugo smoke build) and the
  `deploy` workflow (Hugo build + publish to GitHub Pages).

Note on regeneration semantics:

- Most fixtures are byte-stable: same input -> same output bytes across
  regenerations. Reportlab uses `invariant=1`; size-padding is a
  deterministic SHA-256 expansion.
- Encrypted (`aes*`, `rc4-*`) and Ghostscript-produced PDF/A fixtures and a
  few platypus-built documents use a "once authored, never regenerated"
  pattern: if a file already exists on disk, its bytes are reused. To
  deliberately rotate one of those, delete the file and re-run the
  pipeline. The reason is that qpdf and Ghostscript both emit per-save
  random bytes (encryption salt, internal IDs) that pikepdf cannot fully
  pin. Per the project's URL-immutability rule, this matches the design
  intent anyway.
