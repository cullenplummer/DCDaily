"""
Configuration and subscriber model for the DC Daily newsletter.

Design decision that matters: every subscriber carries their own set of
enabled modules. This is built in from day one so that adding people with
different preferences later is zero migration work. The renderer loops over
MODULE_REGISTRY and skips anything a subscriber has switched off.

Secrets come from environment variables (set as GitHub Actions secrets),
never hardcoded. If a key is missing, the dependent module degrades to
"unavailable today" rather than crashing the whole send.
"""

import os

# ---- Secrets (set these as GitHub Actions repository secrets) ----
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Sender identity. CAN-SPAM legally requires a real physical mailing address
# in any bulk email, even free ones, the moment this goes beyond you two.
# Fill these before adding any third subscriber.
SENDER_NAME = "DC Daily"
SENDER_EMAIL = "you@yourdomain.com"          # must be a Brevo-verified sender
PHYSICAL_ADDRESS = "PO Box / address here"   # required for CAN-SPAM at scale

# ---- The module registry ----
# Each key is a module id. "default_on" decides whether a brand-new subscriber
# gets it unless they say otherwise. "core" modules can't be toggled off (the
# whole point of the newsletter). Everything else is a toggle.
MODULE_REGISTRY = {
    "dc_news":      {"title": "DC Headlines",        "default_on": True,  "core": True},
    "things_to_do": {"title": "Things To Do",        "default_on": True,  "core": False},
    "dc_history":   {"title": "On This Day in DC",   "default_on": True,  "core": False},
    "restaurants":  {"title": "DC Food & Restaurants","default_on": True, "core": False},
    "recipe":       {"title": "Tonight's Recipe",    "default_on": True,  "core": False},
    "gas":          {"title": "Gas Prices",          "default_on": True,  "core": False},
    "world_simple": {"title": "The World, Simply",    "default_on": True,  "core": False},
    "parks":        {"title": "Parks & Trails",      "default_on": False, "core": False},
    # National / optional toggles, built last:
    "sports":       {"title": "Sports",              "default_on": False, "core": False},
    "markets":      {"title": "Markets",             "default_on": False, "core": False},
    "pop_culture":  {"title": "Pop Culture",         "default_on": False, "core": False},
    "politics":     {"title": "National Politics",   "default_on": False, "core": False},
}


def default_modules():
    """Module set a new subscriber gets if they express no preference."""
    return {mid for mid, m in MODULE_REGISTRY.items() if m["default_on"]}


# ---- Subscribers ----
# For v1 (you + girlfriend) this is just a list in code. When you go public,
# this becomes a row in a DB or a row in a Google Sheet / Brevo list, but the
# SHAPE stays the same: an email plus a set of enabled module ids. Keeping the
# shape stable now is what makes that later swap painless.
SUBSCRIBERS = [
    {
        "email": "you@example.com",
        "name": "You",
        "modules": default_modules(),
    },
    {
        "email": "girlfriend@example.com",
        "name": "Her",
        # Example of a personalized feed: she skips politics & markets, adds parks.
        "modules": (default_modules() | {"parks"}) - {"politics", "markets"},
    },
]
