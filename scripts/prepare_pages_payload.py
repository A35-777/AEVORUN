"""Compute asset hashes and base64 payloads for Cloudflare Pages Direct Upload."""

import hashlib
import base64
import json
from pathlib import Path

WEBSITE_DIR = Path("d:/AEVORUN/website")

files = [
    ("index.html", "text/html"),
    ("styles.css", "text/css"),
    ("app.js", "application/javascript"),
    ("robots.txt", "text/plain"),
    ("sitemap.xml", "application/xml")
]

upload_items = []
manifest = {}

for filename, content_type in files:
    content_bytes = (WEBSITE_DIR / filename).read_bytes()
    md5_hash = hashlib.md5(content_bytes).hexdigest()
    b64_val = base64.b64encode(content_bytes).decode("ascii")

    upload_items.append({
        "key": md5_hash,
        "value": b64_val,
        "metadata": {"contentType": content_type},
        "base64": True
    })
    manifest[f"/{filename}"] = md5_hash

output_payload = {
    "upload_items": upload_items,
    "manifest": manifest
}

Path("d:/AEVORUN/website/pages_payload.json").write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
print(f"Generated pages_payload.json with {len(upload_items)} assets.")
print("Manifest:", manifest)
