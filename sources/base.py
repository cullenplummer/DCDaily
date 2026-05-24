"""
The contract every source module obeys.

Each source exposes fetch() -> Section. fetch() must NEVER raise. If anything
goes wrong (network, parse, missing key, source changed its HTML), it catches
the error, records it, and returns a Section with ok=False and a short
human-readable note. The renderer then shows "unavailable today" for that one
block and ships everything else.

This is the single most important design rule in the project. Silent total
failure (no email at 7am) is the thing that kills these projects. Partial
graceful failure (one section blank, logged) is survivable and debuggable.
"""

from dataclasses import dataclass, field
from typing import Callable
import traceback
import sys


@dataclass
class Item:
    title: str
    url: str = ""
    blurb: str = ""          # short teaser only; never full article body


@dataclass
class Section:
    module_id: str
    title: str
    ok: bool = True
    items: list = field(default_factory=list)
    note: str = ""           # shown when ok=False, e.g. "source unavailable"
    error: str = ""          # full error for logs, never shown to readers


def safe_fetch(module_id: str, title: str, fn: Callable) -> Section:
    """Wrap a fetch function so it can never crash the run."""
    try:
        section = fn()
        if not isinstance(section, Section):
            raise TypeError(f"{module_id} fetch returned {type(section)}")
        # Log success/empty for visibility in CI logs.
        status = "OK" if section.items else "EMPTY"
        print(f"[{module_id}] {status} ({len(section.items)} items)", file=sys.stderr)
        return section
    except Exception as e:
        print(f"[{module_id}] FAILED: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return Section(
            module_id=module_id,
            title=title,
            ok=False,
            note="Unavailable today.",
            error=str(e),
        )
