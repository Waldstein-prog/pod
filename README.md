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

## Deploy op PythonAnywhere

```bash
./deploy.sh                        # maakt deploy_bundle/ + pod_deploy.zip
```

1. Upload `pod_deploy.zip` naar je PythonAnywhere-account.
2. In een Bash-console: `bash deploy_bundle/install.sh` (of unzip handmatig). Dit
   plaatst de app in `~/pod` en seedt de database.
3. Stel het admin-wachtwoord in: `python3 ~/pod/set_password.py`.
4. Web-tab: WSGI-bestand wijzen naar `wsgi_pythonanywhere.py` — pas daarin het pad
   (`POD_USER`) en `SECRET_KEY` aan. Klik **Reload**.

SQLite-bestand (`pod.db`) leeft naast de code; voorraad en claims blijven bewaard
zolang je dat bestand niet overschrijft.
