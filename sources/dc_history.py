"""
On This Day in DC module.

Generated, with hallucination mitigations: the model is told to state only
facts it's confident are accurate and not to invent dates. Acceptable for a
personal newsletter; pin to a sourced dataset if you ever want it bulletproof.

Uses the shared llm helper, which prints Anthropic's real error on failure.
"""

import datetime
from .base import Section, Item
from config import ANTHROPIC_API_KEY
from .llm import ask_claude


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

    text = ask_claude(prompt, max_tokens=300)
    return Section(module_id="dc_history", title="On This Day in DC",
                   items=[Item(title="", blurb=text)])
