"""
Daily Recipe module.

GENERATED, not scraped. This is deliberate: recipe sites have strong terms and
active anti-scraping, scraping them is fragile and risky, and an LLM produces
original content you own, never breaks, and can be tuned precisely to "easy and
healthy." See the conversation notes for the full reasoning.

The one real risk is an off quantity or vague step. We mitigate by constraining
the output tightly: exact amounts, exact times, numbered steps, a short
ingredient list, and a hard time cap. Keep recipes simple enough that any error
is obvious to a cook.

RECIPE_BRIEF is the one knob you'll actually tune. Edit it freely; it does not
touch any logic.
"""

import random
import requests
from .base import Section, Item
from config import ANTHROPIC_API_KEY

# ---- Standing constraints. Plain English. Edit freely; touches no logic. ----
# Nightshades are listed by NAME on purpose. "Avoid nightshades" alone will
# still get you paprika or peppers, because recipes aren't written in those
# terms. The model needs the offenders spelled out or it fails silently.
NIGHTSHADES = (
    "tomatoes, all peppers (bell, chili, jalapeno, etc.), potatoes (white/red/"
    "yellow; sweet potatoes are fine), eggplant, tomatillos, and "
    "paprika/cayenne/chili powder/crushed red pepper"
)

DIET_BRIEF = (
    "high in protein, lower-carb but NOT zero-carb (a modest portion of rice, "
    "grains, beans, or sweet potato is welcome), and completely free of "
    f"nightshades, specifically: {NIGHTSHADES}"
)

# Meal type is a weighted choice per day: mostly dinner, with occasional
# surprises. This is what makes it feel like an editor picking, not a template.
MEAL_TYPES = (
    ["dinner"] * 7 +
    ["lunch"] * 1 +
    ["breakfast"] * 1 +
    ["a healthy snack or small plate"] * 1
)

# Most days ~30 min; occasionally allow a longer 45+ min cook.
TIME_OPTIONS = ["about 30 minutes or less"] * 4 + ["up to 45 minutes if it's worth it"] * 1


def fetch() -> Section:
    if not ANTHROPIC_API_KEY:
        return Section(module_id="recipe", title="Tonight's Recipe",
                       ok=False, note="Recipe of the day is off (no API key).")

    meal = random.choice(MEAL_TYPES)
    time_cap = random.choice(TIME_OPTIONS)

    prompt = (
        f"Create an easy, healthy {meal} recipe for two people, ready in "
        f"{time_cap}.\n\n"
        f"Dietary requirements (strict): the recipe must be {DIET_BRIEF}.\n"
        f"Double-check before finishing that NO nightshade ingredient appears, "
        f"including in spice blends and condiments (many contain paprika or "
        f"chili). If a classic version would use one, substitute it out.\n\n"
        "Requirements:\n"
        "- Give it a short appealing name.\n"
        "- List ingredients with EXACT quantities (real measurements).\n"
        "- Number the steps. Each concrete, with times and temperatures.\n"
        "- State total active time and total time.\n"
        "- Genuinely simple: a competent beginner should succeed.\n"
        "- Real, sensible recipe only. No implausible combinations, nothing unsafe.\n"
        "Format as clean plain text with clear INGREDIENTS and STEPS sections. "
        "No preamble."
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
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=40,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
    ).strip()

    # Title reflects the meal so a breakfast surprise doesn't say "Tonight's".
    if meal == "dinner":
        section_title = "Tonight's Recipe"
    elif meal == "breakfast":
        section_title = "Breakfast Idea"
    elif meal == "lunch":
        section_title = "Lunch Idea"
    else:
        section_title = "A Little Something"

    return Section(module_id="recipe", title=section_title,
                   items=[Item(title="", blurb=text)])
