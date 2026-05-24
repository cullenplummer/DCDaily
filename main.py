"""
Orchestrator. The entry point GitHub Actions runs at 7am.

Flow:
  1. Fetch every source ONCE (not per subscriber). Each fetch is wrapped in
     safe_fetch so it can't crash the run.
  2. For each subscriber, render an email containing only their enabled modules.
  3. Send via Brevo.

Run locally with  python main.py --dry-run  to write HTML files to ./preview/
instead of sending, so you can eyeball the newsletter without emailing anyone.
"""

import sys
import datetime
import pathlib

from sources.base import safe_fetch
from sources import dc_news, dc_history, restaurants, recipe, gas, things_to_do, world_simple
from render import render_email
from send import send
from config import SUBSCRIBERS, MODULE_REGISTRY

# Map module_id -> fetch function. Modules not listed here simply won't render.
FETCHERS = {
    "dc_news":       dc_news.fetch,
    "things_to_do":  things_to_do.fetch,
    "dc_history":    dc_history.fetch,
    "restaurants":   restaurants.fetch,
    "recipe":        recipe.fetch,
    "gas":           gas.fetch,
    "world_simple":  world_simple.fetch,
}


def fetch_all() -> dict:
    """Fetch every registered source once. Returns {module_id: Section}."""
    sections = {}
    for module_id, fn in FETCHERS.items():
        title = MODULE_REGISTRY.get(module_id, {}).get("title", module_id)
        sections[module_id] = safe_fetch(module_id, title, fn)
    return sections


def main(dry_run: bool = False):
    print(f"=== DC Daily run {datetime.datetime.now().isoformat()} ===", file=sys.stderr)
    sections = fetch_all()
    subject = "DC Daily — " + datetime.date.today().strftime("%A, %b %-d")

    if dry_run:
        out = pathlib.Path("preview")
        out.mkdir(exist_ok=True)

    for sub in SUBSCRIBERS:
        html = render_email(sections, sub)
        if dry_run:
            f = out / f"{sub['email'].replace('@', '_at_')}.html"
            f.write_text(html, encoding="utf-8")
            print(f"[dry-run] wrote {f}", file=sys.stderr)
        else:
            send(sub["email"], sub.get("name", ""), subject, html)

    print("=== run complete ===", file=sys.stderr)


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
