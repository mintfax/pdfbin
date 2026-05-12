# pdfbin pipeline build environment.
# Build: `docker build -t pdfbin-build .`
# Run (from repo root):
#   docker run --rm -v "$(pwd):/work" pdfbin-build
# This re-runs the pipeline against ./static and ./content/preview.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      qpdf \
      ghostscript \
      build-essential \
      libffi-dev \
      libssl-dev \
      git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY requirements.txt /work/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /work

CMD ["python", "-m", "generate.pipeline"]
