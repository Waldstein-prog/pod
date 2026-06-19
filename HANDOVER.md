# Handover — 2026-06-19

## What this session did
- **Live-URL-verwarring opgelost:** de app draait op een PythonAnywhere-account in de **EU-regio** → live = `https://magicmeadow.eu.pythonanywhere.com`. De `.com` zonder `.eu.` is enkel PA's "Coming Soon!"-placeholder, geen down-app. Vastgelegd in memory.
- **Favicon-fix** (`7d9b5ae`): inline SVG-favicon in de templates → geen `/favicon.ico` 404 meer.
- **Regio-bewuste reload** in `deploy/setup.sh` (`5b894ac`): de auto-reload gebruikt nu `PYTHONANYWHERE_SITE`/`PYTHONANYWHERE_DOMAIN`, dus werkt op EU én US.
- **PA-token uit bestand** (`9c59c70`): `setup.sh` leest het API-token uit `~/.pa_api_token` (zoals `tracker`), niet enkel uit `$API_TOKEN` — die env-var verschijnt pas na reload + nieuwe console.
- **Playwright-verificatie** van de flow tegen de live EU-URL (logs in gitignored `.playwright-mcp/`).

## Current state
- Branch: `master` — clean, **in sync met origin/master** (niets unpushed).
- Working tree: clean (enkel gitignored cruft: `.playwright-mcp/`, `deploy_bundle/`, `pod_deploy.zip`, `backend/pod.db`, `.pytest_cache/`).
- Last commit: `9c59c70` fix: lees PA-token uit ~/.pa_api_token.
- Tests: **16/16 groen** (`cd backend && python3 -m pytest`) — 15 unit + 1 e2e.
- Deploy: live op **https://magicmeadow.eu.pythonanywhere.com** (let op `.eu.`). Updaten = `cd ~/pod && bash deploy/setup.sh` → "automatisch herladen gelukt".

## Next steps (in order)
1. **Token roteren (blocker, zie hieronder):** het API-token in `~/.pa_api_token` op de EU-host moet vervangen worden — het oude lekte vandaag in een chat-transcript.
2. Sessie-fixes live zetten (indien nog niet): `cd ~/pod && bash deploy/setup.sh`.
3. Niets verder verplicht openstaand — app is af, getest en live.

## Open questions / blockers
- **Gelekt API-token:** roteer het PythonAnywhere-token (Account-tab → API token → regenereren) en herschrijf `~/.pa_api_token` op de EU-host. Tot dan is het oude token compromitteerbaar.

## Context for picking this up
- Smoke-test/deploy altijd tegen het **`.eu.`-domein**; verifieer met page-title "Palia Pod Giveaway" (placeholder = "Coming Soon: PythonAnywhere").
- Memory: `~/.claude/projects/-home-jo-lab-pod/memory/project-pod-live-url.md` (live-URL, deploy auto-reload, token-rotatie). Oudere stack/flow/valkuilen-context: `~/.claude/projects/-home-jo-lab/memory/project_pod.md`.
- Lokaal draaien: `./run.sh` (poort 8500); deze machine mist `python3-venv` → systeem-`python3`.
- E2e vereist eenmalig `pip install pytest-playwright && python3 -m playwright install chromium` (al gebeurd op deze machine). Zonder Playwright wordt de e2e geskipt.
- Spec + plan: `docs/superpowers/`.
