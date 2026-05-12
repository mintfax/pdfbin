---
title: "About - pdfbin.net"
description: "Why pdfbin.net exists: a CC0 library of test PDFs at stable flat URLs you can pin in CI suites, with a typed multi-axis catalog."
layout: text-page
---

pdfbin.net is a free CC0 library of test PDFs you can drop into your test
suite. Every PDF lives at a stable flat URL; bytes are immutable; multi-axis
typed metadata lives in [catalog.json](../catalog.json).

## Why this exists

The practice for "I need a sample PDF for my test suite" today is: find a PDF
on GitHub, right-click save into the repo, pray it stays addressable.
pdfbin.net replaces that with:

- Flat immutable URLs
- Explicit CC0 licensing
- A typed multi-axis catalog
- Real corruption / encryption / scan / document-shape variants

## URL contract

Every PDF is served at `https://pdfbin.net/<id>.pdf`. The bytes never change.
If a PDF turns out to be wrong, a new ID ships and the old one stays
available, marked `status: deprecated` in `catalog.json`.

## Source

Source code at [github.com/mintfax/pdfbin](https://github.com/mintfax/pdfbin).
Issues and contributions welcome.
