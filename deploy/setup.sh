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
WSGI="$(ls /var/www/*_wsgi.py 2>/dev/null | head -1)"
if [ -z "$WSGI" ]; then
    echo "    !! Geen web-app gevonden in /var/www/."
    echo "       Maak eerst op de Web-tab een web-app aan (Add a new web app ->"
    echo "       Manual configuration), en draai dit script daarna opnieuw."
    exit 1
fi
cp "$REPO/deploy/pa_wsgi.py" "$WSGI"
echo "    geschreven naar $WSGI"

echo "==> 4/4  Dependencies"
if [ -n "$VIRTUAL_ENV" ]; then
    pip install -q -r "$BACKEND/requirements.txt"
    echo "    geïnstalleerd in virtualenv: $VIRTUAL_ENV"
else
    echo "    Geen actieve virtualenv. Activeer 'm en installeer eenmalig:"
    echo "       workon pod-venv && pip install -r $BACKEND/requirements.txt"
fi

echo ""
echo "============================================================"
echo " KLAAR. Ga nu naar de Web-tab en klik op de groene Reload-knop."
echo "============================================================"
