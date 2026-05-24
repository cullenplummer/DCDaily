"""
DC Restaurants module.

Same safe pattern as DC news: pull from food-section RSS feeds and link out
with a headline + short teaser only. No full-article reproduction, no scraping
of recipe/review bodies. Eater DC and Washingtonian Food both publish feeds.

If you later want "new restaurant openings near you" specifically, the durable
source is Open Data DC's business/licensing datasets (basic business licenses),
which is API-backed rather than scraped. Left as a note rather than guessing a
stale endpoint.
"""

import feedparser
import re
from .base import Section, Item

FEEDS = [
    ("Eater DC",            "https://dc.eater.com/rss/index.xml"),
    ("Washingtonian Food",  "https://www.washingtonian.com/food/feed/"),
]

MAX_PER_FEED = 3


def fetch() -> Section:
    items = []
    for source_name, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:MAX_PER_FEED]:
                raw = getattr(entry, "summary", "") or ""
                teaser = re.sub(r"<[^>]+>", "", raw)
                teaser = re.sub(r"\s+", " ", teaser).strip()
                teaser = (teaser[:140] + "...") if len(teaser) > 140 else teaser
                items.append(Item(
                    title=f"{entry.title}  ({source_name})",
                    url=entry.link,
                    blurb=teaser,
                ))
        except Exception as e:
            print(f"  [restaurants] feed failed {source_name}: {e}")
            continue
    return Section(module_id="restaurants", title="DC Food & Restaurants", items=items)
