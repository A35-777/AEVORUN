"""Compile website static assets into a production Cloudflare Pages _worker.js."""

import json
from pathlib import Path

WEBSITE_DIR = Path("d:/AEVORUN/website")

html_content = (WEBSITE_DIR / "index.html").read_text(encoding="utf-8")
css_content = (WEBSITE_DIR / "styles.css").read_text(encoding="utf-8")
js_content = (WEBSITE_DIR / "app.js").read_text(encoding="utf-8")
robots_content = (WEBSITE_DIR / "robots.txt").read_text(encoding="utf-8")
sitemap_content = (WEBSITE_DIR / "sitemap.xml").read_text(encoding="utf-8")

assets = {
    "/": {"body": html_content, "type": "text/html; charset=utf-8"},
    "/index.html": {"body": html_content, "type": "text/html; charset=utf-8"},
    "/styles.css": {"body": css_content, "type": "text/css; charset=utf-8"},
    "/app.js": {"body": js_content, "type": "application/javascript; charset=utf-8"},
    "/robots.txt": {"body": robots_content, "type": "text/plain; charset=utf-8"},
    "/sitemap.xml": {"body": sitemap_content, "type": "application/xml; charset=utf-8"},
}

worker_code = f"""// Cloudflare Pages Worker serving AEVORUN presentation website
const ASSETS = {json.dumps(assets)};

export default {{
  async fetch(request, env, ctx) {{
    const url = new URL(request.url);
    const pathname = url.pathname;

    let asset = ASSETS[pathname];
    if (!asset && !pathname.includes('.')) {{
      asset = ASSETS["/"];
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
print(f"Successfully generated {WEBSITE_DIR / '_worker.js'} ({len(worker_code)} bytes).")
