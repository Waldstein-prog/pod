# Palia Pod Shop 🥔

Een fake webwinkel voor de 57 Palia "potato pods". Geen valuta, geen echt geld:
bezoekers kiezen pods uit de voorraad door hun naam in te vullen, en een admin
beheert de stock en ziet wie welke pod koos — telkens met afbeelding erbij.

Flask + Jinja-templates + SQLite. Eén Python-stack, geen build-stap.

## Lokaal draaien

```bash
./run.sh          # poort 8500
```

`run.sh` maakt (indien mogelijk) een venv, installeert dependencies, seedt de
pod-tabel en start de app op http://localhost:8500.

Eerste keer: stel een admin-wachtwoord in.

```bash
cd backend
python3 set_password.py            # vraagt om wachtwoord
# of niet-interactief:
POD_ADMIN_WACHTWOORD=geheim python3 set_password.py
```

## Pod-data verversen

De 57 pods + afbeeldingen komen van
[paliatracker.com](https://www.paliatracker.com/furniture-tracker/potato-pods).
Ze zijn al gebundeld in `backend/static/pods/` + `backend/pods.json`. Opnieuw ophalen:

```bash
cd backend && python3 fetch_images.py
```

## Pagina's

- `/` — giveaway: bezoeker vult eerst Twitch-naam + Palia-naam in en klikt Submit; pas
  daarna zijn de pods kiesbaar. Eén claim per bezoeker; een geclaimde pod ligt vast voor
  anderen. Werkt alleen wanneer de giveaway "live" staat.
- `/admin` — voorraadbeheer (login vereist): per pod het aantal instellen (**auto-save**,
  geen knop), plus **Go Live / Stop** om de giveaway te starten/stoppen en **Reset** (met
  bevestiging) om alle claims te wissen en de hoeveelheden naar de startwaarden te zetten.
- `/admin/verkopen` — alle claims met afbeelding, Twitch- en Palia-naam, status en tijdstip;
  per claim een **Confirm** (definitief maken) en **Cancel** (pod weer vrijgeven).

## Deploy op PythonAnywhere

Alles loopt via één script: **`deploy/setup.sh`**. Dat doet de `git pull`, seedt de
database, zet (eenmalig) het admin-wachtwoord, schrijft het WSGI-bestand op z'n plek,
installeert dependencies en herlaadt de web-app. `pod.db` is gitignored en blijft staan
over pulls heen, dus voorraad en claims blijven bewaard.

### Eenmalige setup
1. Web-tab → **Add a new web app** → **Manual configuration** → Python 3.10. (Zet
   **Virtualenv** op `pod-venv` als je er een gebruikt.)
2. Bash-console:
   ```bash
   cd ~ && git clone https://github.com/Waldstein-prog/pod.git
   cd pod && bash deploy/setup.sh
   ```
   Het script vraagt eenmalig een admin-wachtwoord en regelt de rest.
3. Web-tab → **Reload** (of automatisch als er een PythonAnywhere `API_TOKEN` is).

### Updaten (na elke push)
```bash
cd ~/pod && bash deploy/setup.sh
```
Eén commando — het haalt de nieuwste code op en deployt. Daarna Web-tab → **Reload**
(of automatisch met API-token).

## Deploy als zip (alternatief)

```bash
./deploy.sh                        # maakt deploy_bundle/ + pod_deploy.zip (platte structuur)
```
Upload `pod_deploy.zip`, draai `bash deploy_bundle/install.sh`, en wijs de WSGI naar
`~/pod` (plat) i.p.v. `~/pod/backend`. Bedoeld voor accounts zonder git-toegang.
