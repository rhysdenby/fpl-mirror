# fpl-mirror

Mirrors the public Fantasy Premier League API into flat JSON so it can be read from environments that cannot reach `fantasy.premierleague.com` directly, and from browsers (raw.githubusercontent.com serves `access-control-allow-origin: *`).

No credentials required. Every endpoint pulled here is public.

## Setup

1. Create a **public** repo named `fpl-mirror` on GitHub. Public matters: unauthenticated raw reads and open CORS both depend on it.
2. Add these files at the same paths.
3. Edit `config.json` — set `entry_id` to the number in your FPL team URL and add your mini-league IDs.
4. Settings → Actions → General → Workflow permissions → **Read and write permissions**. Save.
5. Actions tab → *FPL mirror* → **Run workflow**. Then run *FPL mirror (daily deep pull)* once too.
6. Confirm `data/meta.json` exists and `fetched_at` is recent.

## Schedules

- `mirror.yml` — hourly, plus every 10 minutes across UK match windows.
- `daily.yml` — 04:20 UTC, adds per-player match-by-match history for the top ~280 players.

GitHub disables scheduled workflows after 60 days of repository inactivity. Commits made by the Action may not reset that timer, so if the mirror goes quiet, push any commit or hit *Run workflow* to wake it.

## Read URLs

```
https://raw.githubusercontent.com/<user>/fpl-mirror/main/data/meta.json
https://raw.githubusercontent.com/<user>/fpl-mirror/main/data/players.json
https://raw.githubusercontent.com/<user>/fpl-mirror/main/data/fixtures.json
```

Raw responses are cached for 5 minutes (`cache-control: max-age=300`).
