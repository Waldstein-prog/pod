#!/bin/bash
# PythonAnywhere one-shot setup voor de pod shop.
#
#   cd ~/pod && git pull && bash deploy/setup.sh
#
# Doet: database seeden, admin-wachtwoord (alleen indien nog niet gezet),
# WSGI-bestand op z'n plek zetten, dependencies installeren.
# Daarna hoef je alleen nog op de Web-tab op Reload te klikken.
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO/backend"

echo "==> 1/4  Database seeden"
python3 "$BACKEND/seed.py"

echo "==> 2/4  Admin-wachtwoord"
if python3 - "$BACKEND/pod.db" <<'PY'
import sys, sqlite3
con = sqlite3.connect(sys.argv[1])
row = con.execute(
    "SELECT 1 FROM setting WHERE sleutel='admin_wachtwoord_hash'"
).fetchone()
sys.exit(0 if row else 1)
PY
then
    echo "    al ingesteld (overslaan). Opnieuw zetten? python3 $BACKEND/set_password.py"
else
    python3 "$BACKEND/set_password.py"
fi

echo "==> 3/4  WSGI-bestand koppelen"
WROTE=0
for f in /var/www/*_wsgi.py; do
    [ -e "$f" ] || continue
    if [ "$f" -ef "$REPO/deploy/pa_wsgi.py" ]; then
        echo "    al gekoppeld (symlink) -> $f"
    else
        cp "$REPO/deploy/pa_wsgi.py" "$f"
        echo "    geschreven naar $f"
    fi
    WROTE=1
done
if [ "$WROTE" = 0 ]; then
    echo "    !! Geen web-app gevonden in /var/www/."
    echo "       Maak eerst op de Web-tab een web-app aan (Add a new web app ->"
    echo "       Manual configuration), en draai dit script daarna opnieuw."
    exit 1
fi

echo "==> 4/4  Dependencies"
if [ -n "$VIRTUAL_ENV" ]; then
    pip install -q -r "$BACKEND/requirements.txt"
    echo "    geïnstalleerd in virtualenv: $VIRTUAL_ENV"
else
    echo "    Geen actieve virtualenv. Activeer 'm en installeer eenmalig:"
    echo "       workon pod-venv && pip install -r $BACKEND/requirements.txt"
fi

echo "==> 5/5  Web-app herladen"
RELOADED=0
DOMAIN="$(echo "$USER" | tr 'A-Z' 'a-z').pythonanywhere.com"
if [ -n "$API_TOKEN" ]; then
    if curl -sf -X POST \
        "https://www.pythonanywhere.com/api/v0/user/$USER/webapps/$DOMAIN/reload/" \
        -H "Authorization: Token $API_TOKEN" >/dev/null 2>&1; then
        echo "    automatisch herladen gelukt ($DOMAIN)"
        RELOADED=1
    fi
fi

echo ""
echo "============================================================"
if [ "$RELOADED" = 1 ]; then
    echo " KLAAR. Open https://$DOMAIN — de pod-winkel draait."
else
    echo " BIJNA KLAAR. Eén klik nog: Web-tab -> groene Reload-knop."
    echo " (auto-reload kon niet: geen API-token. Account-tab -> 'API token'"
    echo "  aanmaken en dit script opnieuw draaien laat 't voortaan vanzelf gaan.)"
fi
echo "============================================================"
