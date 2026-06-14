# Palia Pod Shop — Ontwerp

**Datum:** 2026-06-14
**Status:** goedgekeurd ontwerp, klaar voor implementatieplan

## Doel

Een fake webwinkel voor de 57 Palia "potato pods". Geen valuta, geen echt geld.
Bezoekers kiezen pods uit een voorraad; een admin beheert de stock en ziet wie welke
pod gekozen heeft, telkens met afbeelding erbij. Draait op PythonAnywhere, gedeployed
volgens hetzelfde patroon als het `bog`-project (platte map, WSGI, SQLite).

## Stack & deployment

- **Eén Flask-app** met Jinja-templates (server-rendered) + SQLite. Geen aparte
  frontend-build — simpelste deploy op PythonAnywhere.
- Lokale poort **8500** (vrij in de lab-poorttabel; `/home/jo/lab/CLAUDE.md` wordt
  bijgewerkt met deze rij).
- `deploy.sh` maakt een `deploy_bundle/` met een platte structuur + `install.sh` en
  `wsgi_pythonanywhere.py`, exact volgens het `bog`-patroon.
- Git init + push naar GitHub bij afronding.

## Datamodel (SQLite, `schema.sql`)

- **`pod`**: `id`, `naam`, `categorie`, `image_bestand`, `stock` (INTEGER, default 1)
- **`claim`**: `id`, `pod_id` (FK → pod, ON DELETE CASCADE), `bezoeker_naam`,
  `tijdstip` (ISO-string, default CURRENT_TIMESTAMP)
- **`setting`**: `sleutel` (PK), `waarde` — bevat o.a. `admin_wachtwoord_hash`

`PRAGMA foreign_keys = ON`. Een pod kiezen gebeurt atomair binnen één transactie:
controleer `stock > 0`, voeg een `claim` toe, verlaag `stock` met 1, commit.
Bij `stock = 0` is de pod niet kiesbaar (geen knop + serverside check).

## Pagina's & routes

### Publiek
- `GET /` — winkelgrid. Pods gegroepeerd per categorie (9 categorieën), met
  afbeelding, naam en resterende stock. Pods met `stock > 0` tonen een "Kies"-knop;
  uitverkochte pods tonen "Uitverkocht".
- `POST /claim` — formulier `{pod_id, bezoeker_naam}`. Serverside: valideer naam
  (niet leeg), controleer stock, registreer claim + verlaag stock. Redirect naar
  bevestigingspagina (PRG-patroon) of terug naar `/` met flash-bevestiging.

### Admin (login vereist via `login_required`)
- `GET/POST /admin/login` — login met één wachtwoord (sessie-cookie).
- `POST /admin/logout`.
- `GET /admin` — stockbeheer: lijst van alle pods met huidige stock en een veld om
  de stock per pod te **zetten** (absolute waarde, admin bepaalt zelf hoeveel).
- `POST /admin/stock` — update stock van één pod.
- `GET /admin/verkopen` — lijst van alle claims: wie koos welke pod, met afbeelding
  en tijdstip. Nieuwste eerst.

### Auth-patroon (overgenomen van bog)
Flask-sessie, `werkzeug.security.check_password_hash`, `login_required`-decorator.
Wachtwoordhash staat in `setting`-tabel, gezet via `set_password.py`. `SECRET_KEY`
uit env (met dev-fallback). Sessie-cookie HttpOnly + SameSite=Lax.

## Data binnenhalen

- **`fetch_images.py`** (eenmalig, lokaal): downloadt de 57 originele webp-bestanden
  van `https://www.paliatracker.com/items/decor/decor-potatopod-*.webp` naar
  `static/pods/`, en schrijft/verifieert `pods.json` met per pod: `naam`,
  `categorie`, `image_bestand`. De 57 pods + bestandsnamen zijn al bekend uit de
  bronpagina en worden in `pods.json` vastgelegd (script downloadt enkel de plaatjes).
- **`seed.py`**: leest `pods.json` en vult de `pod`-tabel met default-stock **1** als
  de tabel leeg is. Idempotent (zoals bog): herhaald draaien voegt niets dubbel toe.

## Projectstructuur

```
pod/
  backend/
    app.py              # Flask routes + auth
    db.py               # get_db / init_db
    schema.sql
    seed.py             # pods.json -> pod-tabel (idempotent)
    set_password.py     # admin-wachtwoordhash in setting-tabel
    fetch_images.py     # eenmalig: download 57 webp's
    pods.json           # 57 pods: naam, categorie, image_bestand
    wsgi.py             # lokale/dev wsgi-entry
    requirements.txt
    static/
      pods/*.webp
      style.css
    templates/
      base.html
      shop.html
      claim_done.html
      admin_login.html
      admin_stock.html
      admin_sales.html
    tests/
      test_claim.py     # stock daalt, niet kiesbaar bij 0
      test_admin.py     # auth + stock zetten
  deploy.sh
  run.sh
  .gitignore
  docs/superpowers/specs/2026-06-14-pod-shop-design.md
```

## Testen (pytest)

- **Claim-logica**: claim verlaagt stock met 1; claim op `stock = 0` wordt geweigerd;
  lege bezoeker-naam wordt geweigerd.
- **Admin-auth**: admin-routes vereisen login; verkeerd wachtwoord faalt; stock zetten
  werkt na login.

## Categorieën (uit bron)

Fancypod, Smartypod, Shinypod, Rockerpod, Potato Pod, Prettypod, Merpod, Bonsai Pod,
Mushpod — samen 57 pods.

## Bewust buiten scope (YAGNI)

- Geen valuta, prijzen, winkelwagen of betaling.
- Geen bezoeker-accounts (enkel naam invullen bij keuze).
- Geen annuleren/teruggeven van claims door bezoekers (admin kan stock weer ophogen).
