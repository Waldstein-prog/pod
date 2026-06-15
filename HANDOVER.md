# Handover — 2026-06-15

## What this session did
- Nieuw project **pod** opgezet: fake Palia "potato pod" Twitch-**giveaway** (Flask + Jinja + SQLite), live op **https://magicmeadow.pythonanywhere.com**.
- 57 pods + afbeeldingen gescrapet van paliatracker (`fetch_images.py`), gebundeld in `static/pods/` + `pods.json`.
- Volledige giveaway-flow gebouwd: welkomblok met **Twitch- + Palia-naam** (Submit-gate) → pods kiesbaar → claim vergrendelt de pod. UI volledig Engels, titel "Palia Pod Giveaway".
- Admin: Stock-pagina met **auto-save** aantallen (geen knop), **Go Live / Stop**, **Reset** (wist claims + herstelt startwaarden). Claims-pagina met **Confirm / Cancel** per claim, Twitch- + Palia-naam, status-badge.
- Datamodel-fix: aparte `begin_stock` (vaste startwaarde) naast bewerkbare `stock`; Reset herstelt ernaar. "Save as start values"-knop daarna verborgen (startwaarden liggen vast).
- Bug-fix: "1 pod per bezoeker" nu op **DB-Twitch-naam** i.p.v. sessie → na admin-Cancel kan de bezoeker opnieuw kiezen.
- Deploy vereenvoudigd: `deploy/setup.sh` doet nu zelf de `git pull` → deploy = **één commando**.
- 15 pytest-tests, alle groen. Repo public op GitHub, alles gepusht.

## Current state
- Branch: `master` — clean, **in sync met origin/master** (niets unpushed).
- Working tree: clean (alleen gitignored `deploy_bundle/`, `pod_deploy.zip`, `backend/pod.db`).
- Last commit: `6a59585` chore: verberg 'Save as start values'-knop.
- Tests: **15/15 groen** (`cd backend && python3 -m pytest`).
- Deploy: live op magicmeadow; updaten = `cd ~/pod && bash deploy/setup.sh` → Web-tab Reload.

## Next steps (in order)
1. Niets verplicht openstaand. Project is af, gepusht, getest en live.
2. Bij volgende deploy van deze sessie-wijzigingen op magicmeadow: `cd ~/pod && bash deploy/setup.sh` → Reload. Daarna in **Admin → Stock** de aantallen zetten en **Go Live** klikken (giveaway start standaard op *stopped*).
3. Optioneel: een PythonAnywhere **API token** aanmaken (Account-tab) zodat `setup.sh` voortaan zelf reload doet.

## Open questions / blockers
- Geen.

## Context for picking this up
- Lokaal draaien: `./run.sh` (poort 8500) — maar deze machine mist `python3-venv`; systeem-`python3` + `pip install --user --break-system-packages pytest` werd gebruikt. PythonAnywhere maakt z'n eigen venv.
- PythonAnywhere-valkuilen (allemaal opgelost in `setup.sh`): schrijft naar **álle** `/var/www/*_wsgi.py`, vervangt symlinks door echte bestanden (`cp --remove-destination` — PA volgt symlinks niet), systeem-Flask volstaat (geen venv strikt nodig).
- Durable details + deploy-stappen staan in memory `project_pod` (`~/.claude/projects/-home-jo-lab/memory/project_pod.md`).
- Spec + plan: `docs/superpowers/`.
