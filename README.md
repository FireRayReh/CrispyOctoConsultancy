# Canada Economic Opportunities Dashboard

A small, self-running pipeline that scans Canadian government, consulting,
and tech/startup RSS feeds, ranks items by how likely they are to point at
an actionable business opportunity, and produces a markdown report — daily
and weekly — with every claim linked back to its original source.

Built for someone with a day job: this doesn't try to *decide* opportunities
for you, it surfaces signal (grants, procurement, policy shifts, funding
programs, sector demand) so you can go verify and act on the ones worth it.

## How it works

1. **`sources.yaml`** — the list of RSS/Atom feeds to pull from, grouped by
   category (government, consulting, economic indicators, startup/tech).
2. **`pipeline/fetch.py`** — fetches each feed. A dead or changed feed URL
   doesn't crash the run — it's logged and shown in the report's own
   "Source Health" section so you know what to fix.
3. **`pipeline/score.py`** — scores each item against a weighted keyword
   list (grants, SR&ED, procurement, RFPs, digitization, nearshoring, etc.).
   Higher score = stronger opportunity signal, not just generic news.
4. **`pipeline/report.py`** — dedupes, filters to the report window (last
   24h for daily, last 7 days for weekly), and renders a markdown report
   grouped by category with links, dates, and matched signal keywords.
5. **`main.py`** — orchestrates the above and writes to `reports/`.
6. **`.github/workflows/report.yml`** — runs it on a schedule (daily +
   weekly cron), commits the report into `reports/`, and opens a GitHub
   Issue with the report body so it shows up as a notification.

## Running it yourself

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --window daily     # or --window weekly
```

Output lands in `reports/YYYY-MM-DD-daily.md` and `reports/latest-daily.md`
(same pattern for `weekly`).

## First-run checklist

I couldn't verify these feed URLs from a live network in the environment
that built this (sandboxed egress) — some of the less common ones (bank
economics RSS in particular) may have moved or need a different path.
On the first scheduled run:

1. Check the **Source Health** section at the bottom of the report.
2. For anything marked "Failed", open the publisher's site, find their
   current RSS/Atom link (usually `/feed` or linked in the page footer),
   and update the URL in `sources.yaml`.
3. Re-run via **Actions → Canada Economic Opportunities Report → Run
   workflow** to confirm the fix.

## Extending it

- **Add a source**: append an entry to `sources.yaml` — no code changes
  needed.
- **Tune relevance**: edit `KEYWORD_WEIGHTS` in `pipeline/score.py`. Raise
  weights for signals you care about more (e.g. your specific tech stack,
  a sector you're targeting).
- **Change delivery**: right now the report lands as a committed file +
  GitHub Issue. To add email or Slack delivery, add a step at the end of
  `.github/workflows/report.yml` that reads `reports/latest-<window>.md`
  and posts it via your provider's API (store the API key as a repo
  secret under Settings → Secrets → Actions).
- **Change schedule**: edit the `cron` lines in
  `.github/workflows/report.yml` (times are UTC).

## Testing

```bash
pip install pytest
pytest tests/
```

Tests cover scoring weights and report assembly (windowing, dedup, source
health reporting) with mocked data — no network calls.
