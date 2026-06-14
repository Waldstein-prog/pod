"""Vul de pod-tabel uit pods.json. Idempotent: doet niets als al gevuld."""
import json
import os

from db import get_db, init_db

HERE = os.path.dirname(os.path.abspath(__file__))
PODS_JSON = os.path.join(HERE, "pods.json")
DEFAULT_STOCK = 1


def seed():
    init_db()
    db = get_db()
    try:
        aantal = db.execute("SELECT COUNT(*) FROM pod").fetchone()[0]
        if aantal > 0:
            print(f"pod-tabel bevat al {aantal} rijen — overslaan.")
            return
        with open(PODS_JSON) as fh:
            pods = json.load(fh)
        for p in pods:
            db.execute(
                "INSERT INTO pod (naam, categorie, image_bestand, stock) VALUES (?, ?, ?, ?)",
                (p["naam"], p["categorie"], p["image_bestand"], DEFAULT_STOCK),
            )
        db.commit()
        print(f"{len(pods)} pods toegevoegd (stock {DEFAULT_STOCK}).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
