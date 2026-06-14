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
        "INSERT INTO pod (naam, categorie, image_bestand, stock) VALUES ('Test Pod', 'Mushpod', 'x.webp', 1)"
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


def test_admin_vereist_login(client):
    resp = client.get("/admin", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_verkeerd_wachtwoord_faalt(client):
    resp = _login(client, "fout")
    assert resp.status_code == 200
    assert b"Verkeerd wachtwoord" in resp.data
    resp2 = client.get("/admin", follow_redirects=False)
    assert resp2.status_code == 302


def test_login_en_stock_zetten(client):
    _login(client)
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b"Test Pod" in resp.data
    client.post("/admin/stock", data={"pod_id": "1", "stock": "7"}, follow_redirects=True)
    import db as db_mod
    conn = db_mod.get_db()
    stock = conn.execute("SELECT stock FROM pod WHERE id = 1").fetchone()[0]
    conn.close()
    assert stock == 7


def test_verkopen_toont_claim(client):
    client.post("/claim", data={"pod_id": "1", "bezoeker_naam": "Alice"})
    _login(client)
    resp = client.get("/admin/verkopen")
    assert resp.status_code == 200
    assert b"Alice" in resp.data
    assert b"Test Pod" in resp.data
