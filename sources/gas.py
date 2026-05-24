"""
Gas Prices module.

Honest scope: there is NO clean free API for "cheapest specific station near
me." GasBuddy forbids scraping and enforces it. So this module reports the AAA
DC-metro average, which is publicly published daily and defensible to display.
We do NOT attempt cheapest-station, because that feature is not worth the legal
exposure once the list grows.

AAA publishes averages on a page rather than a clean API. This fetches the
public average. If AAA changes their page structure this degrades gracefully to
"unavailable" like every other module. If you ever want per-station prices,
pay for a legitimate fuel-price API rather than scraping.
"""

import requests
import re
from .base import Section, Item

# AAA Gas Prices publishes state/metro averages. This is a light fetch of the
# DC state average from their public data endpoint. Treat as best-effort.
AAA_URL = "https://gasprices.aaa.com/?state=DC"
TIMEOUT = 15


def fetch() -> Section:
    resp = requests.get(AAA_URL, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    # Look for the regular-grade average dollar figure on the page.
    m = re.search(r"\$\s?([0-9]\.[0-9]{2,3})", html)
    if not m:
        return Section(module_id="gas", title="Gas Prices", ok=False,
                       note="Couldn't read today's average.")
    avg = m.group(1)
    return Section(module_id="gas", title="Gas Prices",
                   items=[Item(title=f"DC average (regular): ${avg}/gal",
                               blurb="Source: AAA daily averages.")])
