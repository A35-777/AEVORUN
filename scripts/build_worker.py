"""Compile all website static assets into a production Cloudflare Pages _worker.js."""

import json
from pathlib import Path

WEBSITE_DIR = Path("d:/AEVORUN/website")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

assets = {}

for p in WEBSITE_DIR.glob("**/*"):
    if p.is_file() and p.name not in ["_worker.js", "pages_payload.json"]:
        rel_path = "/" + p.relative_to(WEBSITE_DIR).as_posix()
        mime = MIME_TYPES.get(p.suffix, "text/plain; charset=utf-8")
        content = p.read_text(encoding="utf-8")
        assets[rel_path] = {"body": content, "type": mime}
        if rel_path == "/index.html":
            assets["/"] = {"body": content, "type": mime}

worker_code = f"""// Cloudflare Pages Worker serving AEVORUN presentation website
const ASSETS = {json.dumps(assets)};

export default {{
  async fetch(request, env, ctx) {{
    const url = new URL(request.url);
    let pathname = url.pathname;

    if (pathname.endsWith('/') && pathname !== '/') {{
      pathname = pathname.slice(0, -1);
    }}

    let asset = ASSETS[pathname];
    if (!asset && !pathname.includes('.')) {{
      asset = ASSETS[pathname + '.html'] || ASSETS['/index.html'];
    }}

    if (asset) {{
      return new Response(asset.body, {{
        headers: {{
          "Content-Type": asset.type,
          "Cache-Control": "public, max-age=3600",
          "X-Content-Type-Options": "nosniff"
        }}
      }});
    }}

    return new Response("Not Found", {{ status: 404 }});
  }}
}};
"""

(WEBSITE_DIR / "_worker.js").write_text(worker_code, encoding="utf-8")
print(f"Successfully generated {WEBSITE_DIR / '_worker.js'} with {len(assets)} assets ({len(worker_code)} bytes).")
