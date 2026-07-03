# Vev community phishing feed

A globally-maintained, crowd-confirmed list of phishing hosts — seeded by
Vev's on-device AI (Huma Guard) and confirmed by real users. It is a plain
public JSON file, fetched at runtime by every Vev browser (like the URLhaus
threat feed), and maintained entirely by a GitHub Action — **no server**.

This directory is the **scaffold** for that repo. To go live: push it to a
public repo (default expected location
`github.com/aryansrao/community-phishing-feed`), enable Actions, and point
Vev at it (it already defaults to the raw URL below; override with
`community_feed_url` in `config.json`).

## The feed: `flagged.json`

```json
{
  "version": 1,
  "updated": "2026-07-04T00:00:00Z",
  "hosts": {
    "secure-paypal.account-verify.tk": { "percent": 92, "reports": 40 },
    "login-microsoft.verify-account.cf": { "percent": 100, "reports": 12 }
  }
}
```

- `percent` — share of reports that **confirmed** the host is phishing
  (`confirms / (confirms + denials)`, 0–100). This is the "accurate real
  percentage of being a flagged URL" shown in the browser.
- `reports` — total reports backing the entry.

Vev fetches this from:

```
https://raw.githubusercontent.com/aryansrao/community-phishing-feed/main/flagged.json
```

A host is shown as *"Community-confirmed phishing: 92% (40 reports)"* in the
Huma island. Subdomains inherit a parent-domain entry.

## How reports arrive

Vev only submits when a user **manually** clicks **Report** on a phishing
warning, and only if they have opted in (`community_reporting: true` in
`config.json`). The submission is the **plaintext host + the AI score** — never
the full URL, never browsing history. Off by default.

A submission is a small JSON `POST` to the configured `report_endpoint`
(a serverless function or a GitHub-App bot). The endpoint appends the report
as a file under `reports/` (or opens an issue the Action parses):

```
reports/2026-07-04T00-00-00Z_secure-paypal.account-verify.tk.json
{ "host": "secure-paypal.account-verify.tk", "ai_score": 0.97, "vote": "confirm" }
```

"Allow anyway" in the browser is a **deny** vote for that host and can be
submitted the same way, so false positives self-correct.

## How the feed is maintained (the Action)

`aggregate.py` rebuilds `flagged.json` from every report in `reports/`:
confirms and denials per host → `percent` + `reports`, dropping hosts below a
confidence floor. The workflow runs on every push to `reports/` and on a daily
schedule, then commits the regenerated `flagged.json`.

Copy `aggregate-flags.yml` into `.github/workflows/` in the live repo.

## Trust & abuse notes

- A host needs a minimum number of independent reports before it appears
  (`MIN_REPORTS` in `aggregate.py`) so one actor can't flag a competitor.
- The AI score is advisory context, not a vote — humans confirm.
- Everything is public and auditable; anyone can inspect `reports/` and
  `flagged.json` and open a PR to remove a wrongly-listed host.
