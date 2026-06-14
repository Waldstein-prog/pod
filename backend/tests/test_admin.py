import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    import db as db_mod
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_mod.DB_PATH = path
    db_mod.init_db()
    conn = db_mod.get_db()
    conn.execute(
        "INSERT INTO pod (naam, categorie, image_bestand, stock) VALUES ('Test Pod', 'Mushpod', 'x.webp', 2)"
    )
    conn.execute(
        "INSERT INTO setting (sleutel, waarde) VALUES ('admin_wachtwoord_hash', ?)",
        (generate_password_hash("geheim"),),
    )
    conn.commit()
    conn.close()

    import app as app_mod
    app = app_mod.create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    os.unlink(path)


def _login(client, wachtwoord="geheim"):
    return client.post("/admin/login", data={"wachtwoord": wachtwoord}, follow_redirects=True)


def _db():
    import db as db_mod
    return db_mod.get_db()


def test_admin_vereist_login(client):
    resp = client.get("/admin", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_verkeerd_wachtwoord_faalt(client):
    resp = _login(client, "fout")
    assert b"Wrong password" in resp.data
    assert client.get("/admin", follow_redirects=False).status_code == 302


def test_stock_auto_save(client):
    _login(client)
    resp = client.post("/admin/stock", data={"pod_id": "1", "stock": "7"})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    conn = _db()
    stock = conn.execute("SELECT stock FROM pod WHERE id = 1").fetchone()[0]
    conn.close()
    assert stock == 7


def test_live_en_stop(client):
    _login(client)
    client.post("/admin/live")
    conn = _db()
    assert conn.execute("SELECT waarde FROM setting WHERE sleutel='giveaway_live'").fetchone()[0] == "1"
    conn.close()
    client.post("/admin/stop")
    conn = _db()
    assert conn.execute("SELECT waarde FROM setting WHERE sleutel='giveaway_live'").fetchone()[0] == "0"
    conn.close()


def test_confirm_en_cancel(client):
    conn = _db()
    conn.execute(
        "INSERT INTO claim (pod_id, bezoeker_naam, palia_naam, status) VALUES (1, 'Bob', 'BobP', 'pending')"
    )
    conn.commit()
    conn.close()
    _login(client)

    # verkopen-pagina toont de claim
    resp = client.get("/admin/verkopen")
    assert b"Bob" in resp.data and b"BobP" in resp.data

    # confirm zet status op confirmed
    client.post("/admin/claim/1/confirm")
    conn = _db()
    assert conn.execute("SELECT status FROM claim WHERE id=1").fetchone()[0] == "confirmed"
    conn.close()

    # cancel verwijdert de claim (pod weer vrij)
    client.post("/admin/claim/1/cancel")
    conn = _db()
    assert conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 0
    conn.close()


def test_reset_wist_claims(client):
    conn = _db()
    conn.execute("INSERT INTO claim (pod_id, bezoeker_naam, palia_naam) VALUES (1, 'A', 'Ap')")
    conn.execute("INSERT INTO claim (pod_id, bezoeker_naam, palia_naam) VALUES (1, 'B', 'Bp')")
    conn.commit()
    conn.close()
    _login(client)
    client.post("/admin/reset")
    conn = _db()
    assert conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 0
    # stock (startwaarde) blijft ongemoeid
    assert conn.execute("SELECT stock FROM pod WHERE id=1").fetchone()[0] == 2
    conn.close()
