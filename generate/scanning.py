"""Rasterize a PDF and re-pack it as a 'scanned' PDF with optional noise/skew.

Used by `provenance.py` and `documents.py` to derive scanned variants. The
rasterization uses Ghostscript; the image manipulation uses Pillow; the
re-pack uses img2pdf.

Determinism: the noise is generated from a seeded random.Random instance so
the same (input bytes, ScanProfile, seed) produces the same output bytes.
img2pdf is asked to use a fixed CreationDate so the resulting PDF has no
per-run timestamp drift.
"""

from __future__ import annotations

import datetime as dt
import io
import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import img2pdf
from PIL import Image


@dataclass(frozen=True)
class ScanProfile:
    dpi: int
    noise: str          # "" | "low" | "high"
    skew_degrees: float


# Fixed pin so img2pdf doesn't embed a per-run timestamp.
FIXED_DATETIME = dt.datetime(2026, 5, 12, 0, 0, 0, tzinfo=dt.UTC)


def _rasterize_with_gs(pdf_bytes: bytes, dpi: int) -> list[Image.Image]:
    if shutil.which("gs") is None:
        raise RuntimeError("Ghostscript not installed; required for scanning.")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src.pdf"
        src.write_bytes(pdf_bytes)
        out_pattern = str(Path(tmp) / "page-%03d.png")
        cmd = [
            "gs",
            f"-r{dpi}",
            "-dBATCH", "-dNOPAUSE", "-dQUIET",
            "-sDEVICE=pnggray",
            f"-sOutputFile={out_pattern}",
            str(src),
        ]
        subprocess.run(cmd, check=True)
        images: list[Image.Image] = []
        for png_path in sorted(Path(tmp).glob("page-*.png")):
            images.append(Image.open(png_path).copy())
        return images


def _apply_noise(img: Image.Image, level: str, rng: random.Random) -> Image.Image:
    """Apply speckle noise to an image using a seeded RNG (deterministic)."""
    px = img.load()
    w, h = img.size
    intensity = 30 if level == "low" else 90
    speckle_density = 0.01 if level == "low" else 0.05
    speckles = int(w * h * speckle_density)
    for _ in range(speckles):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        cur = px[x, y]
        delta = rng.randint(-intensity, intensity)
        if isinstance(cur, tuple):
            px[x, y] = tuple(max(0, min(255, c + delta)) for c in cur)
        else:
            px[x, y] = max(0, min(255, cur + delta))
    return img


def _apply_skew(img: Image.Image, degrees: float) -> Image.Image:
    return img.rotate(degrees, resample=Image.BICUBIC, fillcolor=255, expand=True)


def scan_pdf(pdf_bytes: bytes, profile: ScanProfile, seed: str = "pdfbin") -> bytes:
    """Return a new PDF that simulates the input as a scanned document.

    `seed` controls the noise RNG so callers can ensure stable output across
    regenerations - same seed -> same bytes.
    """
    rng = random.Random(f"{seed}:{profile.dpi}:{profile.noise}:{profile.skew_degrees}")
    pages = _rasterize_with_gs(pdf_bytes, profile.dpi)
    processed: list[bytes] = []
    for img in pages:
        if profile.noise:
            img = _apply_noise(img, profile.noise, rng)
        if profile.skew_degrees:
            img = _apply_skew(img, profile.skew_degrees)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=False)
        processed.append(buf.getvalue())
    return img2pdf.convert(processed, creationdate=FIXED_DATETIME, moddate=FIXED_DATETIME)
