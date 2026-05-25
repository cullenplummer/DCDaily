"""
Shared helper for calling the Anthropic API.

Keeping the call in one place means the model name, error handling, and any
future fixes live in a single file instead of being copy-pasted across three
modules. Crucially, on a non-200 response it prints Anthropic's ACTUAL error
message (the thing a bare raise_for_status() hides), so failures are
diagnosable instead of just "400 Bad Request".
"""

import sys
import requests
from config import ANTHROPIC_API_KEY

# Sonnet is the right model for these simple text tasks: cheaper than Opus and
# more than capable of a history blurb, a recipe, or news simplification.
MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"


def ask_claude(prompt: str, max_tokens: int = 600, timeout: int = 40) -> str:
    """Send a single-prompt request. Returns the text, or raises with the real
    error message from Anthropic so we can see what actually went wrong."""
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    if resp.status_code >= 400:
        # Print the real body so the CI log tells us the actual cause.
        print(f"  [anthropic] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        resp.raise_for_status()
    data = resp.json()
    return "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    ).strip()
