"""End-to-end test van alle giveaway-features met Playwright.

Vereist eenmalig:  pip install pytest-playwright && python3 -m playwright install chromium
Draaien:           python3 -m pytest tests/test_e2e.py   (vanuit backend/)

Start de Flask-app als subprocess tegen een tijdelijke DB en stuurt een echte
browser door de volledige flow: landing, namen-gate, claim, één-per-bezoeker,
admin-login, voorraad auto-save, confirm/cancel, reset en stop.
"""
import os
import socket
import subprocess
import sys
import tempfile
import time

import pytest
from werkzeug.security import generate_password_hash

pytest.importorskip("playwright")

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8599
BASE = f"http://127.0.0.1:{PORT}"
CLAIM_BTN = "form[action$='/claim'] button[name=pod_id]"


@pytest.fixture(scope="session")
def live_server():
    fd, db_path = tempfile.mkstemp(suffix=".e2e.db")
    os.close(fd)
    sys.path.insert(0, BACKEND)
    import db as dbmod

    dbmod.DB_PATH = db_path
    dbmod.init_db()
    conn = dbmod.get_db()
    conn.execute(
        "INSERT INTO pod (naam, categorie, image_bestand, stock, begin_stock) "
        "VALUES ('Alpha Pod', 'Mushpod', 'decor-potatopod-24-mushroom-agaric.webp', 1, 1)"
    )
    conn.execute(
        "INSERT INTO pod (naam, categorie, image_bestand, stock, begin_stock) "
        "VALUES ('Beta Pod', 'Merpod', 'decor-potatopod-16-water-kelp.webp', 2, 2)"
    )
    conn.execute(
        "INSERT INTO setting (sleutel, waarde) VALUES ('admin_wachtwoord_hash', ?)",
        (generate_password_hash("pw"),),
    )
    conn.execute("UPDATE setting SET waarde = '1' WHERE sleutel = 'giveaway_live'")
    conn.commit()
    conn.close()

    env = dict(os.environ, POD_DB_PATH=db_path, SECRET_KEY="e2e")
    proc = subprocess.Popen(
        [sys.executable, "-c", f"from app import app; app.run(host='127.0.0.1', port={PORT})"],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("server kwam niet op")
    yield BASE
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    os.unlink(db_path)


def test_full_giveaway_flow(live_server, browser):
    # === Bezoeker: landing toont welkom + beide velden, nog geen claim-knop ===
    visitor = browser.new_context()
    vp = visitor.new_page()
    vp.goto(live_server)
    assert "Welcome to the Magic Meadow Giveaway" in vp.content()
    assert vp.locator("input[name=bezoeker_naam]").count() == 1
    assert vp.locator("input[name=palia_naam]").count() == 1
    assert vp.locator(CLAIM_BTN).count() == 0

    # === Namen invullen -> pods worden kiesbaar ===
    vp.fill("input[name=bezoeker_naam]", "streamerX")
    vp.fill("input[name=palia_naam]", "MeadowX")
    vp.click(".enterform button[type=submit]")
    vp.wait_for_load_state()
    assert vp.locator(CLAIM_BTN).count() >= 1

    # === Claim Alpha Pod (id 1) -> bevestiging ===
    vp.click("button[name=pod_id][value='1']")
    vp.wait_for_load_state()
    assert "You're in, streamerX" in vp.content()

    # === Terug naar shop: al geclaimd, geen knoppen meer ===
    vp.goto(live_server)
    assert "You've claimed Alpha Pod" in vp.content()
    assert vp.locator(CLAIM_BTN).count() == 0

    # === Admin: login ===
    admin = browser.new_context()
    ap = admin.new_page()
    ap.goto(live_server + "/admin/login")
    ap.fill("input[name=wachtwoord]", "pw")
    ap.click("button[type=submit]")
    ap.wait_for_load_state()
    assert "Stock management" in ap.content()
    assert "LIVE" in ap.content()

    # === Claims-pagina: claim met Twitch + Palia zichtbaar, dan Confirm ===
    ap.goto(live_server + "/admin/verkopen")
    assert "streamerX" in ap.content() and "MeadowX" in ap.content()
    assert "Alpha Pod" in ap.content()
    ap.click(".acties button.go")  # Confirm (geen dialog)
    ap.wait_for_load_state()
    assert "confirmed" in ap.content().lower()

    # === Voorraad auto-save: Beta (id 2) -> 5 via de input ===
    ap.goto(live_server + "/admin")
    ap.eval_on_selector(
        ".stock-input[data-pod='2']",
        "el => { el.value = '5'; el.dispatchEvent(new Event('change', {bubbles:true})); }",
    )
    ap.wait_for_timeout(500)
    ap.goto(live_server + "/admin")
    assert ap.input_value(".stock-input[data-pod='2']") == "5"

    # === Cancel de claim -> bezoeker kan weer kiezen ===
    ap.goto(live_server + "/admin/verkopen")
    ap.once("dialog", lambda d: d.accept())
    ap.click(".acties button.danger")  # Cancel (met confirm-dialog)
    ap.wait_for_load_state()
    assert "No one has claimed a pod yet." in ap.content()
    vp.goto(live_server)
    assert vp.locator(CLAIM_BTN).count() >= 1

    # === Reset: Beta op 0 zetten, resetten -> terug naar startwaarde 2 ===
    ap.goto(live_server + "/admin")
    ap.eval_on_selector(
        ".stock-input[data-pod='2']",
        "el => { el.value = '0'; el.dispatchEvent(new Event('change', {bubbles:true})); }",
    )
    ap.wait_for_timeout(400)
    ap.once("dialog", lambda d: d.accept())
    ap.click(".adminbar form[action$='/reset'] button")
    ap.wait_for_load_state()
    assert ap.input_value(".stock-input[data-pod='2']") == "2"

    # === Stop: bezoeker ziet 'not live', geen knoppen ===
    ap.click(".adminbar form[action$='/stop'] button")  # geen dialog
    ap.wait_for_load_state()
    vp.goto(live_server)
    assert "not live" in vp.content().lower()
    assert vp.locator(CLAIM_BTN).count() == 0

    visitor.close()
    admin.close()
