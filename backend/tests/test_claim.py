import os
import tempfile

import pytest


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
    conn.commit()
    conn.close()

    import app as app_mod
    app = app_mod.create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    os.unlink(path)


def test_shop_toont_pod(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Test Pod" in resp.data


def test_claim_verlaagt_stock(client):
    resp = client.post("/claim", data={"pod_id": "1", "bezoeker_naam": "Alice"}, follow_redirects=True)
    assert resp.status_code == 200
    import db as db_mod
    conn = db_mod.get_db()
    stock = conn.execute("SELECT stock FROM pod WHERE id = 1").fetchone()[0]
    claims = conn.execute("SELECT bezoeker_naam FROM claim WHERE pod_id = 1").fetchall()
    conn.close()
    assert stock == 0
    assert claims[0][0] == "Alice"


def test_claim_geweigerd_bij_stock_nul(client):
    client.post("/claim", data={"pod_id": "1", "bezoeker_naam": "Alice"})
    client.post("/claim", data={"pod_id": "1", "bezoeker_naam": "Bob"})
    import db as db_mod
    conn = db_mod.get_db()
    aantal = conn.execute("SELECT COUNT(*) FROM claim WHERE pod_id = 1").fetchone()[0]
    conn.close()
    assert aantal == 1


def test_claim_lege_naam_geweigerd(client):
    client.post("/claim", data={"pod_id": "1", "bezoeker_naam": "  "})
    import db as db_mod
    conn = db_mod.get_db()
    aantal = conn.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
    stock = conn.execute("SELECT stock FROM pod WHERE id = 1").fetchone()[0]
    conn.close()
    assert aantal == 0
    assert stock == 1
