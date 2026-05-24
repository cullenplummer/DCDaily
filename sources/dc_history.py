"""
On This Day in DC module.

This is the one piece that is genuinely better generated than scraped. We ask
Claude for a short, engaging DC-history blurb for today's date.

The honest risk with LLM history is hallucinated dates/facts. Mitigation: we
instruct the model to only state things it is confident are real and verifiable,
to keep it to one well-known event, and to say so plainly if it isn't sure
rather than inventing. For a personal newsletter this is acceptable; if you go
public and want it bulletproof, pin it to a sourced dataset (DC Public Library
archives, Wikipedia "on this day" filtered to DC) instead of free generation.
"""

import datetime
import requests
from .base import Section, Item
from config import ANTHROPIC_API_KEY


def fetch() -> Section:
    if not ANTHROPIC_API_KEY:
        return Section(module_id="dc_history", title="On This Day in DC",
                       ok=False, note="History editor is off (no API key).")

    today = datetime.date.today().strftime("%B %d")
    prompt = (
        f"Write a short, warm 3-4 sentence 'on this day in Washington DC history' "
        f"blurb for {today}. Pick ONE genuinely notable, verifiable DC-area event "
        f"from history that occurred on this date. State only facts you are "
        f"confident are accurate. If you are not confident about a specific {today} "
        f"event, instead share one well-known piece of DC history with a clear, "
        f"correct date. Do not invent dates or details. No preamble, just the blurb."
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
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()

    return Section(module_id="dc_history", title="On This Day in DC",
                   items=[Item(title="", blurb=text)])
