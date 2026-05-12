---
title: "Credits - pdfbin.net"
description: "Source-asset provenance for imported PDFs (the IRS Form 1040 from irs.gov) and font credits (IBM Plex Sans and Mono)."
layout: text-page
---

Most PDFs in this library are generated programmatically (reportlab + pikepdf
+ Ghostscript - see the [source repo](https://github.com/mintfax/pdfbin) if
you care). A handful are imported verbatim from explicitly CC0 or
public-domain sources. Each import is documented below.

## irs-1040-blank.pdf

- **Source:** https://www.irs.gov/pub/irs-pdf/f1040.pdf
- **License:** US federal government work, public domain (17 U.S.C. § 105)
- **Downloaded:** 2026-05-12
- **Format:** PDF 1.7
- **Notes:** The IRS rotates this form annually under the same URL. If we
  ever re-import for a newer tax year, the existing fixture will be renamed
  (e.g. `irs-1040-blank-2026.pdf`) and a new one shipped under a new ID,
  per the project's URL-immutability rule. Until then, this fixture
  reflects the form as it was on the download date.

## Synthesized documents

The remaining document-shape fixtures (invoice, receipt, bank statement,
contract NDA, lab report, fax cover sheet) are synthesized in
`generate/builders/documents.py` with deliberately fake entities
(Jane Doe, Acme Widgets Inc., Globex Corp.). They are not based on any
real document.

## Fonts

The site uses [IBM Plex Sans and IBM Plex Mono](https://www.ibm.com/plex/)
via Google Fonts. IBM Plex is released under the SIL Open Font License 1.1.
