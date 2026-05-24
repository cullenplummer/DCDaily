"""
The World, Simply module (ELI5 markets / economy / world news).

Design choice that matters: the LLM NEVER free-generates "today's news" (it
would confidently invent plausible events). Instead we fetch REAL current
headlines from business/world RSS feeds, then the model's only job is to
rewrite what we hand it in plain, ELI5 language and briefly explain why it
matters. It cannot report an event that isn't in the fetched list.

No market-data API on purpose. Index levels in isolation ("S&P at 5,900") add a
keyed, rate-limited dependency for little ELI5 value. The value is the WHY, and
that comes from the news feeds. If you ever want real numbers, adding Alpha
Vantage/Finnhub is a contained change, but it's deliberately left out for now.

Degrades gracefully: no Anthropic key -> shows plain headlines + links.
"""

import re
import feedparser
import requests
from .base import Section, Item
from config import ANTHROPIC_API_KEY

FEEDS = [
    ("Reuters Business", "https://www.reutersagency.com/feed/?best-topics=business-finance"),
    ("NPR Economy",      "https://feeds.npr.org/1017/rss.xml"),
    ("BBC World",        "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business",     "https://feeds.bbci.co.uk/news/business/rss.xml"),
    # Feeds are independent; a dead one just contributes nothing. Verify on first run.
]

MAX_ITEMS = 12
TIMEOUT = 30


def fetch() -> Section:
    raw = _gather()
    if not raw:
        return Section(module_id="world_simple", title="The World, Simply",
                       ok=False, note="No headlines available right now.")

    if not ANTHROPIC_API_KEY:
        # Fallback: plain link-out list, no simplification.
        return Section(module_id="world_simple", title="The World, Simply",
                       items=raw[:6])

    try:
        return _simplified(raw)
    except Exception as e:
        print(f"  [world_simple] simplification failed, falling back to list: {e}")
        return Section(module_id="world_simple", title="The World, Simply",
                       items=raw[:6])


def _gather():
    items = []
    for source_name, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:5]:
                raw = getattr(entry, "summary", "") or ""
                teaser = re.sub(r"<[^>]+>", "", raw)
                teaser = re.sub(r"\s+", " ", teaser).strip()
                items.append(Item(
                    title=entry.title,
                    url=getattr(entry, "link", ""),
                    blurb=(teaser[:160] + "...") if len(teaser) > 160 else teaser,
                ))
        except Exception as e:
            print(f"  [world_simple] feed failed {source_name}: {e}")
            continue
    return items[:MAX_ITEMS]


def _simplified(raw):
    listing = "\n".join(f"- {it.title} :: {it.blurb}" for it in raw)
    prompt = (
        "Below are REAL current news headlines about the economy, markets, and "
        "world events. Pick the 3 to 4 most significant and explain each in "
        "plain, simple language a smart 10-year-old would understand: what "
        "happened, and why it matters, in 1 to 2 short sentences each. No jargon "
        "(if you must use a term like 'inflation', explain it in three words). "
        "Use ONLY the headlines below; do not add events that aren't listed and "
        "do not invent numbers. Warm, calm tone. Plain text, short label then "
        "explanation, no preamble.\n\n"
        f"HEADLINES:\n{listing}"
    )

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-7",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    ).strip()

    items = [Item(title="", blurb=text), Item(title="", blurb="—")]
    for it in raw[:5]:
        items.append(it)
    return Section(module_id="world_simple", title="The World, Simply", items=items)
