# First Deploy Checklist

Work through this top to bottom. It takes the project from "files on disk" to
"newsletter arriving every morning." Do NOT skip the manual test run (step 6) —
that's where you catch problems before the 7am schedule depends on them.

---

## 1. Get the repo onto GitHub

- Create a new repository on GitHub (private is fine and recommended).
- Push this project folder to it. From inside the `dc-daily` folder:
  ```
  git init
  git add .
  git commit -m "DC Daily newsletter"
  git branch -M main
  git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
  git push -u origin main
  ```

## 2. Add the two secrets (this is where your keys go — NOT in any file)

In the repo: **Settings → Secrets and variables → Actions → New repository secret.**
Add each of these:

| Name | Value |
|------|-------|
| `BREVO_API_KEY` | your Brevo key |
| `ANTHROPIC_API_KEY` | your Anthropic key |

Names must match EXACTLY (case-sensitive). GitHub encrypts these and never shows
them again or prints them in logs. The workflow already reads them.

## 3. Fill the non-secret config in `config.py`

These are NOT secrets and go directly in the file:

- `SENDER_EMAIL` — must be a sender you've verified in Brevo (Senders, Domains &
  Dedicated IPs → add + verify your from-address first, or sends will fail).
- `SENDER_NAME` — e.g. "DC Daily".
- `PHYSICAL_ADDRESS` — fill before adding anyone beyond you two (CAN-SPAM).
- `SUBSCRIBERS` — put your real email and your girlfriend's. Start with just you
  two. Each entry's `modules` set is that person's personal feed.

Commit and push these changes.

## 4. Verify your Brevo sender

In Brevo, confirm `SENDER_EMAIL` shows as verified. Unverified senders are the
single most common reason a first send silently fails. Do this before testing.

## 5. (Optional but smart) Local dry run first

If you have Python locally, from the project folder:
```
pip install -r requirements.txt
python main.py --dry-run
```
This writes HTML files to `./preview/` instead of emailing. Open them in a
browser to see the newsletter. No keys needed for the dry run (LLM/feed sections
will just show "unavailable" locally if keys/network aren't set — that's fine,
you're checking layout).

## 6. Manual test run on GitHub (the real test)

- Repo → **Actions** tab → "DC Daily Newsletter" → **Run workflow** → Run.
- Watch the run. Click into it and read the log. Every module prints one of:
  - `[module_id] OK (N items)` — working
  - `[module_id] EMPTY (0 items)` — ran but found nothing (often a dead feed URL)
  - `[module_id] FAILED: ...` — broke; the error tells you why
- Check that the email actually arrived in your inbox.

## 7. Read the log and fix what's flagged

Expected things to check on first run:
- **gas** may FAIL (the AAA page blocks bots) — known fragile module.
- **feed modules** (dc_news, things_to_do, restaurants, world_simple): if any
  show EMPTY, one or more feed URLs in that module need correcting.
- **LLM modules** (dc_history, recipe, world_simple): if they FAIL with a
  model-not-found error, the model string `claude-opus-4-7` in the source needs
  updating to a current model name from console.anthropic.com docs.

For anything flagged, copy the relevant `[module_id] FAILED` log line and the
error — that's exactly what's needed to fix that one module.

## 8. Trust the schedule

Once a manual run produces a good email, the cron in
`.github/workflows/daily.yml` takes over: it fires daily at 11:00 UTC (≈7am ET
in summer). Adjust the cron to `0 12 * * *` in winter if you want exact 7am
year-round, or leave it — a one-hour seasonal drift is harmless.

---

## If the email never arrives but the run says it sent

- Check spam/promotions folder.
- Confirm `SENDER_EMAIL` is Brevo-verified (step 4).
- Check Brevo's own dashboard → Transactional → Logs for the send status and any
  bounce/block reason.
