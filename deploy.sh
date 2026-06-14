#!/bin/bash
# Maakt een deploy-klare zip voor PythonAnywhere
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR/deploy_bundle"
B="$SCRIPT_DIR/backend"

rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

for f in app.py db.py schema.sql seed.py set_password.py pods.json wsgi.py requirements.txt; do
  cp "$B/$f" "$DEPLOY_DIR/"
done
cp -r "$B/templates" "$DEPLOY_DIR/templates"
cp -r "$B/static" "$DEPLOY_DIR/static"

cat > "$DEPLOY_DIR/install.sh" << 'SCRIPT'
#!/bin/bash
set -e
cd ~
rm -rf pod
unzip pod_deploy.zip
mv deploy_bundle pod
python3 pod/seed.py
echo "Stel nu het admin-wachtwoord in: python3 pod/set_password.py"
echo "Daarna: Web-tab -> Reload."
SCRIPT

cat > "$DEPLOY_DIR/wsgi_pythonanywhere.py" << 'WSGI'
import sys, os
path = '/home/POD_USER/pod'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['SECRET_KEY'] = 'VERANDER-DIT-NAAR-EEN-LANG-RANDOM-STRING'
os.environ['SESSION_COOKIE_SECURE'] = '1'
from db import init_db
from app import app as application
init_db()
WSGI

cd "$SCRIPT_DIR" && rm -f pod_deploy.zip && (cd "$DEPLOY_DIR" && zip -qr ../pod_deploy.zip .)
echo "Deploy bundle klaar: $DEPLOY_DIR  (pod_deploy.zip)"
du -sh "$DEPLOY_DIR"
