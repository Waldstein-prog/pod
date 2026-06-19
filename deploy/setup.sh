#!/bin/bash
# PythonAnywhere one-shot setup voor de pod shop.
#
#   cd ~/pod && bash deploy/setup.sh
#
# Doet ALLES in één keer: laatste code ophalen (git pull), database seeden,
# admin-wachtwoord (alleen indien nog niet gezet), WSGI-bestand op z'n plek
# zetten, dependencies installeren en de web-app herladen.
# Zonder API-token hoef je daarna enkel nog op de Web-tab op Reload te klikken.
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$REPO/backend"

echo "==> 1/6  Laatste code ophalen (git pull)"
git -C "$REPO" pull --ff-only

echo "==> 2/6  Database seeden"
python3 "$BACKEND/seed.py"

echo "==> 3/6  Admin-wachtwoord"
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

echo "==> 4/6  WSGI-bestand koppelen"
WROTE=0
for f in /var/www/*_wsgi.py; do
    [ -e "$f" ] || continue
    # --remove-destination vervangt ook een bestaande symlink door een echt
    # bestand (PythonAnywhere volgt symlinks niet altijd).
    cp --remove-destination "$REPO/deploy/pa_wsgi.py" "$f"
    echo "    geschreven naar $f"
    WROTE=1
done
if [ "$WROTE" = 0 ]; then
    echo "    !! Geen web-app gevonden in /var/www/."
    echo "       Maak eerst op de Web-tab een web-app aan (Add a new web app ->"
    echo "       Manual configuration), en draai dit script daarna opnieuw."
    exit 1
fi

echo "==> 5/6  Dependencies"
if [ -n "$VIRTUAL_ENV" ]; then
    pip install -q -r "$BACKEND/requirements.txt"
    echo "    geïnstalleerd in virtualenv: $VIRTUAL_ENV"
else
    echo "    Geen actieve virtualenv. Activeer 'm en installeer eenmalig:"
    echo "       workon pod-venv && pip install -r $BACKEND/requirements.txt"
fi

echo "==> 6/6  Web-app herladen"
RELOADED=0
# PythonAnywhere zet PYTHONANYWHERE_DOMAIN per regio: 'pythonanywhere.com' (US)
# of 'eu.pythonanywhere.com' (EU). Zo werkt reload in beide regio's.
PA_HOST="${PYTHONANYWHERE_DOMAIN:-pythonanywhere.com}"
DOMAIN="$(echo "$USER" | tr 'A-Z' 'a-z').$PA_HOST"
if [ -n "$API_TOKEN" ]; then
    if curl -sf -X POST \
        "https://$PA_HOST/api/v0/user/$USER/webapps/$DOMAIN/reload/" \
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
    echo " (auto-reload kon niet: geen API-token gevonden in \$API_TOKEN."
    echo "  Account-tab -> 'API token' aanmaken, dan een NIEUWE Bash-console"
    echo "  openen (bestaande consoles kennen het token nog niet) en dit script"
    echo "  daar opnieuw draaien -> voortaan herlaadt 't vanzelf.)"
fi
echo "============================================================"
