# SEOnaut on the owner's Mac

Fork: https://github.com/divjotdhindsa11-create/seonaut
Upstream: https://github.com/StJudeWasHere/seonaut (MIT).
Service folder: /Users/divjotai/Services/seonaut
Source folder: /Users/divjotai/Services/seonaut/source

## Current state

SEOnaut and MySQL are configured to listen only on 127.0.0.1:9000 and 127.0.0.1:3306. MySQL X protocol is disabled. The database uses a 64 MB InnoDB buffer, 15 maximum connections and disabled performance schema and binary logging. App connection pool is six, with two idle connections. Crawling uses one worker, and the app permits only one concurrent crawl. The app runs with GOMAXPROCS=1 and a 192 MiB Go memory target (not a hard process limit).

Planned external address: https://seo.getpickcard.com . NOT live until the Cloudflare token blocker is resolved. No DNS changes or tunnel have been made. A Worker alone cannot run this Go/MySQL app. A named Tunnel is the intended route. Existing site and email records must be preserved.

App and database are user LaunchAgents, requiring the Mac to be awake and the owner logged in. Sleeping, shutdown or internet loss makes remote access unavailable. A login service cannot guarantee 24-hour access while the Mac sleeps. No power settings were changed.

## Account setup

No owner account or password has been created. Registration is closed. After the Tunnel and HTTPS are verified, enable SEONAUT_SIGNUP_OPEN=true in the app LaunchAgent, set SEONAUT_SECURE_COOKIES=true and update private/config server URL to the HTTPS hostname. Restart the app. The signup form permits only harchaind@gmail.com. After successful signup it writes private/signup.closed and further GET/POST registrations return 403, including after restarts. Also reset SEONAUT_SIGNUP_OPEN=false after verifying the owner's account. A database trigger assigns the five precreated unowned projects to the owner's account. Keep this marker and private folder out of Git.

Cloudflare Access is not configured. The free tier advertises up to 50 users, but whether this account can activate it without a card is unverified. Do not enable billing or submit payment details.

## Start and stop

LaunchAgent files are in ~/Library/LaunchAgents:
- com.enanto.seonaut.mysql.plist
- com.enanto.seonaut.app.plist

Start (run database first):
```
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.enanto.seonaut.mysql.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.enanto.seonaut.app.plist
```
Restart a loaded service:
```
launchctl kickstart -k gui/$(id -u)/com.enanto.seonaut.app
```
Stop (app first):
```
launchctl bootout gui/$(id -u)/com.enanto.seonaut.app
launchctl bootout gui/$(id -u)/com.enanto.seonaut.mysql
```
Do not run `brew services start mysql` as a second database instance.

## Data and dashboard

/overview is authenticated and restricted to the owner. It combines live database crawl summaries with saved Google reports and cached suggestions, using the same app sign-in. Google date boundaries are displayed explicitly. Current implementation shows the latest saved 28-day window, without an interactive date picker.

Search Console: Fraser Fix, Pick Card, Invites Cafe and Enanto return real data. Mobillify is missing from the connected account; add and verify sc-domain:mobillify.com.
GA4 properties: Fraser Fix 562959699, Pick Card 408079808, Invites Cafe 428111393, Enanto 547385340, Mobillify 565575884. All return successful reports. Mobillify currently has zero report rows, which is displayed as no data, not an error.
Google data is fetched through the owner's connected account and saved in private/connected-metrics.json. No OAuth tokens are copied into the repository. Daily refresh is handled by the bot's scheduled automation, not an exposed local API. Independent service-account/OAuth refresh without OpenMausBot is not implemented.
Google autocomplete: one seed per site per refresh, cached in private/overview.json. No API key required. PageSpeed keyless test returned HTTP 429; waiting for a free PageSpeed API key. Bing is waiting for a free Webmaster API key and verified sites. Google Trends public endpoint also returned HTTP 429, so Trends is omitted rather than treated as a reliable data source. No paid feeds are used.

Snapshot format: connected-metrics.json has `results`, `start` and `end`. The results contain a `response.data` object. Order: three GSC reports (totals, top 50 queries, top 50 pages) for Fraser Fix, Pick Card, Invites Cafe and Enanto, followed by five GA4 batch reports in that same site order plus Mobillify. Each GA4 batch contains totals (sessions,totalUsers), top 20 pagePath/screenPageViews, top 20 sessionSourceMedium/sessions. Top rows are intentionally limited and labelled, not claimed to be all queries.

To rebuild the display cache:
```
cd /Users/divjotai/Services/seonaut/source
python3 integration/refresh.py
```

## Update

Check `memory_pressure` and `sysctl vm.swapusage` first. Run one build at a time. Preserve local patches, private config and database. Fetch upstream and review changes before merging. Do not reset the fork to upstream.
```
cd /Users/divjotai/Services/seonaut/source
git fetch upstream
# Review and merge upstream/main, preserving our changes.
GOMAXPROCS=1 /opt/homebrew/bin/go test -p 1 ./internal/routes ./internal/config ./internal/services
GOMAXPROCS=1 /opt/homebrew/bin/go build -p 1 -o ../seonaut.new ./cmd/server
# Stop app, replace ../seonaut with ../seonaut.new, then start app.
```
If upstream CSS changes, compile with pinned esbuild 0.25.12 using `make front` options. Never commit credentials or snapshot data. Private credentials are mode 600 under private/ (directory mode 700), outside the repository. Database root credentials are in private/root.cnf. Do not print them.

Logs: logs/app.log, logs/mysql.log, logs/mysql-launch.log. Database: /opt/homebrew/var/mysql. App content archives stay under source/archive. Back up the database using mysqldump with the private credentials file, never placing passwords in command arguments.

Before running the setup CLI, stop the app LaunchAgent. SEOnaut startup deletes unfinished crawl records, so the setup crawler and app must never run at the same time. Restart the app only after the setup crawl exits successfully.
