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
    conn.execute("UPDATE setting SET waarde = '1' WHERE sleutel = 'giveaway_live'")
    conn.commit()
    conn.close()

    import app as app_mod
    app = app_mod.create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    os.unlink(path)


def _enter(client, twitch="Alice", palia="AliceP"):
    return client.post("/enter", data={"bezoeker_naam": twitch, "palia_naam": palia})


def _count(table, where=""):
    import db as db_mod
    conn = db_mod.get_db()
    n = conn.execute(f"SELECT COUNT(*) FROM {table} {where}").fetchone()[0]
    conn.close()
    return n


def test_shop_toont_pod(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Test Pod" in resp.data


def test_geen_claimknop_voor_entering(client):
    # Zonder namen ingevuld is er geen claim-knop zichtbaar.
    resp = client.get("/")
    assert b"Claim this pod" not in resp.data


def test_claimknop_na_entering(client):
    _enter(client)
    resp = client.get("/")
    assert b"Claim this pod" in resp.data


def test_claim_registreert_en_vergrendelt(client):
    _enter(client)
    client.post("/claim", data={"pod_id": "1"}, follow_redirects=True)
    import db as db_mod
    conn = db_mod.get_db()
    row = conn.execute("SELECT bezoeker_naam, palia_naam, status FROM claim").fetchone()
    conn.close()
    assert row["bezoeker_naam"] == "Alice"
    assert row["palia_naam"] == "AliceP"
    assert row["status"] == "pending"
    # pod is nu vol -> tweede bezoeker ziet 'Gone'
    resp = client.get("/")
    assert b"Gone" in resp.data


def test_claim_zonder_entering_geweigerd(client):
    client.post("/claim", data={"pod_id": "1"})
    assert _count("claim") == 0


def test_claim_geblokkeerd_als_niet_live(client):
    import db as db_mod
    conn = db_mod.get_db()
    conn.execute("UPDATE setting SET waarde = '0' WHERE sleutel = 'giveaway_live'")
    conn.commit()
    conn.close()
    _enter(client)
    client.post("/claim", data={"pod_id": "1"})
    assert _count("claim") == 0


def test_na_cancel_kan_opnieuw_kiezen(client):
    _enter(client)
    client.post("/claim", data={"pod_id": "1"})
    assert _count("claim") == 1
    # admin cancelt de claim -> rij verdwijnt
    import db as db_mod
    conn = db_mod.get_db()
    conn.execute("DELETE FROM claim")
    conn.commit()
    conn.close()
    # zelfde bezoeker (sessie) is niet langer geblokkeerd en kan opnieuw kiezen
    resp = client.get("/")
    assert b"Claim this pod" in resp.data
    client.post("/claim", data={"pod_id": "1"})
    assert _count("claim") == 1


def test_een_pod_per_bezoeker(client):
    import db as db_mod
    conn = db_mod.get_db()
    conn.execute(
        "INSERT INTO pod (naam, categorie, image_bestand, stock) VALUES ('Pod Two', 'Merpod', 'y.webp', 1)"
    )
    conn.commit()
    conn.close()
    _enter(client)
    client.post("/claim", data={"pod_id": "1"})
    client.post("/claim", data={"pod_id": "2"})
    assert _count("claim") == 1
