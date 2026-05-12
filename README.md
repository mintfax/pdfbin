# pdfbin

Source repository for [pdfbin.net](https://pdfbin.net) - a free CC0 library of
test PDFs at stable URLs you can drop into your test suite.

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
