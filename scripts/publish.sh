#!/usr/bin/env bash
# Publish a scrubbed snapshot of pdfbin-src to the public mintfax/pdfbin repo.
#
# Strips from the publish tree:
#   - CLAUDE.md (mentions the private dev URL)
#   - scripts/ (this script and any future internal tooling)
#   - the Caddy dev-URL bullet in README.md
#
# Adds:
#   - static/CNAME so GH Pages serves the public site at pdfbin.net
#
# Force-pushes a single squashed commit to main on the public remote. The
# full history lives in pdfbin-src; the public repo is a publish target,
# not a fork.

set -euo pipefail

PUBLIC_REMOTE="https://github.com/mintfax/pdfbin.git"
CUSTOM_DOMAIN="pdfbin.net"
COMMIT_NAME="mintfax"
COMMIT_EMAIL="35106583+adam-marash@users.noreply.github.com"

PRIVATE_ROOT=$(git rev-parse --show-toplevel)
PRIVATE_SHA=$(git -C "$PRIVATE_ROOT" rev-parse --short HEAD)

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# Snapshot HEAD (only tracked files, .gitignore'd paths excluded by definition).
git -C "$PRIVATE_ROOT" archive HEAD | tar -x -C "$WORKDIR"

cd "$WORKDIR"

# Drop private paths.
rm -f CLAUDE.md
rm -rf scripts

# Scrub the Caddy dev-URL bullet from README.md (a 2-line list item).
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("README.md")
text = p.read_text()
text = re.sub(
    r'^- Caddy at .*?example\.dev.*?\n  .*?\n',
    '',
    text,
    flags=re.MULTILINE,
)
p.write_text(text)
PY

# Belt-and-suspenders: fail loudly if any "example" leak survives.
if grep -r --binary-files=without-match -q 'example' . 2>/dev/null; then
    echo "ERROR: 'example' still appears in publish tree after scrub:" >&2
    grep -rn --binary-files=without-match 'example' . >&2 || true
    exit 1
fi

# Custom domain for GH Pages.
echo "$CUSTOM_DOMAIN" > static/CNAME

# Init fresh, commit with mintfax identity, force-push.
git init -q -b main
git add -A
git \
    -c "user.name=${COMMIT_NAME}" \
    -c "user.email=${COMMIT_EMAIL}" \
    commit -q -m "Publish snapshot from pdfbin-src @ ${PRIVATE_SHA}"
git remote add origin "$PUBLIC_REMOTE"
git push -f origin main

echo "Published pdfbin-src @ ${PRIVATE_SHA} to ${PUBLIC_REMOTE}"
