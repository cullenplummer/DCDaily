"""
DC Headlines module.

Pulls from official RSS feeds and shows HEADLINE + LINK only. We deliberately
do not reproduce article bodies. This respects PoPville's personal-use terms
(they forbid redistributing/repurposing their feed content) and is also just
correct RSS etiquette. Link-out is more defensible AND less fragile than
trying to scrape full posts.

If you go public, this is the module that matters most legally: keep it
headline+teaser+link, never the full post.
"""

import feedparser
from .base import Section, Item

FEEDS = [
    ("PoPville",      "https://www.popville.com/feed/"),
    ("Washingtonian", "https://www.washingtonian.com/feed/"),
    ("DCist",         "https://dcist.com/feed/"),
    # Add/remove freely. Each is independent; a dead one just contributes nothing.
]

MAX_PER_FEED = 3


def fetch() -> Section:
    items = []
    for source_name, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:MAX_PER_FEED]:
                # Teaser = first ~140 chars of summary, stripped. Never full body.
                raw = getattr(entry, "summary", "") or ""
                teaser = _strip_to_teaser(raw, 140)
                items.append(Item(
                    title=f"{entry.title}  ({source_name})",
                    url=entry.link,
                    blurb=teaser,
                ))
        except Exception as e:
            # One bad feed shouldn't kill the section; just skip it.
            print(f"  [dc_news] feed failed {source_name}: {e}")
            continue
    return Section(module_id="dc_news", title="DC Headlines", items=items)


def _strip_to_teaser(html: str, n: int) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", html)          # strip tags
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:n] + "...") if len(text) > n else text
