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

- `/` — winkel: pods per categorie, met afbeelding en resterende voorraad. Kiezen = naam invullen.
- `/admin` — voorraadbeheer (login vereist): stel per pod in hoeveel exemplaren beschikbaar zijn.
- `/admin/verkopen` — overzicht van wie welke pod koos, met afbeelding en tijdstip.

## Deploy op PythonAnywhere (git pull, zoals bog)

De code staat gekloond op PythonAnywhere; updaten = `git pull` + Reload. De code
leeft in `~/pod/backend/`, dus de WSGI wijst naar die map. `pod.db` is gitignored
en blijft staan over pulls heen, dus voorraad en claims blijven bewaard.

### Eenmalige setup (Bash-console op PythonAnywhere)

```bash
cd ~
git clone https://github.com/Waldstein-prog/pod.git
cd pod/backend
python3 seed.py                 # vult de 57 pods, stock 1
python3 set_password.py         # vraagt je admin-wachtwoord
mkvirtualenv pod-venv --python=/usr/bin/python3.10
pip install -r requirements.txt
```

Web-tab → **Add a new web app** → **Manual configuration** → zelfde Python-versie.
- **Virtualenv**: `pod-venv`
- **WSGI configuration file** (klik de link, wis de inhoud, plak dit):

```python
import sys, os
path = '/home/JOUWNAAM/pod/backend'          # <-- jouw username
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['SECRET_KEY'] = 'ZET-HIER-EEN-LANG-RANDOM-STRING'
os.environ['SESSION_COOKIE_SECURE'] = '1'
from db import init_db
from app import app as application
init_db()
```

Klik **Reload**.

### Updaten (na elke push)

```bash
cd ~/pod && git pull
# alleen als requirements.txt wijzigde:  workon pod-venv && pip install -r backend/requirements.txt
```

Daarna Web-tab → **Reload**.

## Deploy als zip (alternatief)

```bash
./deploy.sh                        # maakt deploy_bundle/ + pod_deploy.zip (platte structuur)
```
Upload `pod_deploy.zip`, draai `bash deploy_bundle/install.sh`, en wijs de WSGI naar
`~/pod` (plat) i.p.v. `~/pod/backend`. Bedoeld voor accounts zonder git-toegang.
