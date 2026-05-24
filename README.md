# DC Daily

A personalized morning newsletter for Washington, DC. Runs as a single
scheduled GitHub Actions job, fetches a set of sources, and emails a per-person
newsletter via Brevo. Built to fail gracefully: one dead source never stops the
7am send.

## How it works

```
GitHub Actions (daily 11:00 UTC ≈ 7am ET)
  → main.py
      → fetch every source ONCE (each wrapped so it can't crash the run)
      → for each subscriber: render only their enabled modules → send via Brevo
```

## Setup

1. Push this folder to a GitHub repo.
2. In the repo: Settings → Secrets and variables → Actions → add:
   - `BREVO_API_KEY` (reuse from your existing project)
   - `ANTHROPIC_API_KEY` (powers the history blurb + recipe)
3. Edit `config.py`:
   - `SENDER_EMAIL` must be a Brevo-verified sender.
   - `PHYSICAL_ADDRESS` — required by CAN-SPAM before you add anyone beyond
     yourself. This is a legal requirement for bulk email, not optional.
   - Fill in real subscriber emails (just you + her to start).
4. Test before trusting it: Actions tab → "DC Daily Newsletter" → "Run workflow".
   Or locally: `pip install -r requirements.txt && python main.py --dry-run`
   (writes HTML to ./preview/ instead of emailing).

## The honest maintenance reality

The fragile part is one module:
- **gas.py** hits a page that blocks bots and can change structure. It returned
  a 403 in testing from a bare server request. When it breaks it degrades to
  "unavailable today" rather than killing the email.
- **dc_news.py**, **restaurants.py**, and **things_to_do.py** (RSS) are robust.
  Feeds rarely break. If one feed in a multi-feed module dies, the others carry it.
- **dc_history.py** and **recipe.py** (LLM) never "break" structurally but can
  occasionally produce an off fact or quantity. Kept simple to make errors obvious.

When something breaks: open the failed Actions run, copy the log (each module
prints `[module_id] OK/EMPTY/FAILED`), and that tells you exactly which one and why.

## Legal notes you should not ignore

- **PoPville** terms forbid redistributing their feed content. This project
  only links out (headline + short teaser + link), which is defensible. Do NOT
  change the news module to reproduce full post bodies.
- **Gas**: no cheapest-station feature on purpose. GasBuddy forbids scraping
  and enforces it. AAA metro average only.
- **CAN-SPAM**: the moment a third person subscribes, you legally need a working
  unsubscribe link and a physical mailing address in every email. The template
  has placeholders for both. Brevo handles unsubscribe via `{{unsubscribe}}`.

## Adding a module

1. Create `sources/yourmodule.py` exposing `fetch() -> Section` (copy an existing one).
2. Register it in `config.py` MODULE_REGISTRY with a title, default_on, core.
3. Add it to `FETCHERS` in `main.py`.
4. It now appears as a per-subscriber toggle automatically.

## Per-person feeds

Each subscriber in `config.py` has a `modules` set. That's their feed. Example:
her set adds `parks` and drops `politics`/`markets`. When you go public, swap the
in-code list for a DB/sheet — keep the same shape (email + module set) and nothing
else changes.
