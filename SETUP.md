# Shia Hot Leads — public status page setup

This turns the daily GHL pull into a free web page hosted on GitHub Pages,
refreshed automatically once a day by GitHub Actions — no Claude session,
no desktop app, and no Claude tokens involved.

**Heads up — this page is fully public, no login, and includes full lead
detail (name, phone, email), by your explicit choice.** Anyone who has the
link can see it, and it can be indexed by search engines. If you ever
change your mind, edit `scripts/pull_leads.py` to drop the `email`/`phone`
(or the whole `leads` list) from what gets written, and it'll stop
appearing on future pulls — but anything already published stays visible
in the site's history until you scrub it from GitHub too.

## 1. Create the repository

1. Go to https://github.com/new
2. Name it something like `shia-hot-leads`
3. Set visibility to **Public** (required for free GitHub Pages)
4. Click "Create repository"

## 2. Upload these files

In your new (empty) repo, use "Add file → Upload files" (or "create new
file" and paste each one in) to add, preserving the folder structure exactly:

```
index.html
data/latest.json
data/manifest.json
data/days/2026-09-11.json
scripts/pull_leads.py
.github/workflows/daily-pull.yml
```

All six files are in the zip Ghadi received alongside this guide — just
drag the whole folder structure into GitHub's upload box, or create each
file by path and paste its contents.

## 3. Add your GHL API key as a secret

1. In the repo, go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `GHL_API_KEY`
4. Value: your GoHighLevel Private Integration token (the same `pit-...`
   key already in use for the daily desktop pull)
5. Save

This key is encrypted by GitHub and is never exposed in the repo, logs, or
the public page — only the workflow run can read it.

## 4. Turn on GitHub Pages

1. Go to **Settings → Pages**
2. Under "Build and deployment", set **Source** to "Deploy from a branch"
3. Branch: `main`, folder: `/ (root)`
4. Save — GitHub will give you a URL like
   `https://<your-username>.github.io/shia-hot-leads/`
   (may take a minute or two to go live the first time)

## 5. Test the daily pull

1. Go to the **Actions** tab
2. Click "Daily hot lead pull" → "Run workflow" → "Run workflow" (this
   triggers it immediately instead of waiting for the 06:00 UTC schedule)
3. Wait ~30 seconds, refresh the page — you should see a new commit
   updating `data/latest.json`
4. Open your Pages URL — the numbers should match what the Claude
   dashboard shows

From then on, it runs automatically every day at 06:00 UTC (~9am
Damascus) with no further action needed.

## Notes

- To change the daily time, edit the `cron:` line in
  `.github/workflows/daily-pull.yml` (cron times are always UTC).
- If GHL rotates or revokes the API key, just update the `GHL_API_KEY`
  secret value — nothing else needs to change.
