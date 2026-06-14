"""Stel het admin-wachtwoord in (hash in setting-tabel).

Niet-interactief: leest uit env POD_ADMIN_WACHTWOORD indien gezet, anders prompt.
"""
import getpass
import os
import sys

from werkzeug.security import generate_password_hash

from db import get_db, init_db


def main():
    init_db()
    wachtwoord = os.environ.get("POD_ADMIN_WACHTWOORD")
    if not wachtwoord:
        wachtwoord = getpass.getpass("Admin-wachtwoord: ")
        if wachtwoord != getpass.getpass("Bevestig: "):
            print("Wachtwoorden komen niet overeen.")
            sys.exit(1)
    if not wachtwoord:
        print("Wachtwoord mag niet leeg zijn.")
        sys.exit(1)
    db = get_db()
    try:
        db.execute(
            "INSERT INTO setting (sleutel, waarde) VALUES ('admin_wachtwoord_hash', ?) "
            "ON CONFLICT(sleutel) DO UPDATE SET waarde = excluded.waarde",
            (generate_password_hash(wachtwoord),),
        )
        db.commit()
        print("Admin-wachtwoord ingesteld.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
