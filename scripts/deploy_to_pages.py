"""Deploy AEVORUN presentation website to Cloudflare Pages.
"""

from pathlib import Path

def main():
    compact_worker = Path("d:/AEVORUN/website/_worker_compact.js")
    if not compact_worker.exists():
        import subprocess
        subprocess.run(["python", "d:/AEVORUN/scripts/build_super_compact.py"], check=True)
    
    print(f"Deploy ready. Worker size: {len(compact_worker.read_text(encoding='utf-8'))} bytes.")
    print("Project: aevorun (https://aevorun.pages.dev)")

if __name__ == "__main__":
    main()
