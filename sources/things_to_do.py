"""
Things To Do module: week-ahead (Mondays) and weekend plan (Thu/Fri).

Cadence is deliberate. This block does NOT appear every day. On Mondays it's a
"week ahead" framing; Thursday and Friday it's a "weekend plan"; other days it
returns nothing and the section is simply omitted. That scarcity is the point:
content that changes shape by day doesn't become wallpaper the way an
every-day block does.

Sourcing: curated feeds built for exactly this (washington.org's weekend
roundup, Washingtonian things-to-do). We link out, never reproduce article
bodies. If ANTHROPIC_API_KEY is set, the editor reads the fetched headlines and
writes a short "for you two" pick across a MIX of free / date-night / active
options. Without a key it degrades to a plain link-out list. Either way it only
points at real fetched items with links, so anything can be verified before you
act on it.

Tune CURATION_BRIEF (the kind of things to lean toward) freely; no logic touched.
"""

import datetime
import re
import feedparser
import requests
from .base import Section, Item
from config import ANTHROPIC_API_KEY

FEEDS = [
    # Verified live (WordPress /feed/ pattern confirmed via fetch):
    ("Washingtonian", "https://washingtonian.com/sections/things-to-do/feed/"),
    ("Washingtonian Weekend", "https://washingtonian.com/tag/weekend-events/feed/"),
    # Surfaced in search, directly relevant; verify on first real run:
    ("DC Theater Arts", "https://dctheaterarts.org/feed/"),
    ("KidFriendly DC", "https://kidfriendlydc.com/feed/"),
    # NOTE: washington.org had no discoverable RSS feed, so it was removed
    # rather than ship a URL likely to 404. If you find their real feed, add it.
]

# What the editor leans toward when picking. Plain English, edit freely.
CURATION_BRIEF = (
    "a mix for a couple: at least one free or cheap option (parks, free "
    "museums, festivals), at least one date-night option (dinner out, a show, "
    "a bar), and at least one active/outdoorsy option (a hike, run, bike, or "
    "outdoor event). Favor things that are genuinely doable on a weekend."
)

MAX_ITEMS = 12          # how many feed items to hand the editor
TIMEOUT = 30


def fetch() -> Section:
    weekday = datetime.date.today().weekday()  # Mon=0 ... Sun=6

    if weekday == 0:
        mode, title = "week", "The Week Ahead"
    elif weekday in (3, 4):
        mode, title = "weekend", "Your Weekend Plan"
    else:
        # Not a publish day for this block. Return empty so it's omitted.
        return Section(module_id="things_to_do", title="Things To Do", items=[])

    raw_items = _gather_feed_items()
    if not raw_items:
        return Section(module_id="things_to_do", title=title, ok=False,
                       note="No event listings available right now.")

    # If we have a key, let the editor curate. Otherwise plain link-out list.
    if ANTHROPIC_API_KEY:
        try:
            return _curated_section(raw_items, mode, title)
        except Exception as e:
            print(f"  [things_to_do] curation failed, falling back to list: {e}")

    return Section(module_id="things_to_do", title=title, items=raw_items[:6])


def _gather_feed_items():
    items = []
    for source_name, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:8]:
                raw = getattr(entry, "summary", "") or ""
                teaser = re.sub(r"<[^>]+>", "", raw)
                teaser = re.sub(r"\s+", " ", teaser).strip()
                items.append(Item(
                    title=f"{entry.title}  ({source_name})",
                    url=getattr(entry, "link", ""),
                    blurb=(teaser[:140] + "...") if len(teaser) > 140 else teaser,
                ))
        except Exception as e:
            print(f"  [things_to_do] feed failed {source_name}: {e}")
            continue
    return items[:MAX_ITEMS]


def _curated_section(raw_items, mode, title):
    framing = ("the upcoming week" if mode == "week" else "this coming weekend")
    listing = "\n".join(
        f"- {it.title} | {it.url} | {it.blurb}" for it in raw_items
    )
    prompt = (
        f"You are a friendly local editor writing a short 'things to do' pick "
        f"for {framing} in Washington DC, for a couple. From ONLY the real "
        f"listings below, choose 3 to 4 and write one warm sentence each on why "
        f"it's worth it. Aim for {CURATION_BRIEF}\n\n"
        f"Do not invent events or details not in the list. Keep each pick to: a "
        f"short label, then your one-sentence reason. Plain text, no preamble.\n\n"
        f"LISTINGS:\n{listing}"
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

    # Editor's curated prose, followed by the real source links to verify/click.
    items = [Item(title="", blurb=text)]
    items.append(Item(title="", blurb="—"))
    for it in raw_items[:6]:
        items.append(it)
    return Section(module_id="things_to_do", title=title, items=items)
