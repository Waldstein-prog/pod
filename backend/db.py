import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pod.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn):
    """Voeg ontbrekende kolommen/instellingen toe aan bestaande databases."""
    claim_cols = {r[1] for r in conn.execute("PRAGMA table_info(claim)")}
    if "palia_naam" not in claim_cols:
        conn.execute("ALTER TABLE claim ADD COLUMN palia_naam TEXT NOT NULL DEFAULT ''")
    if "status" not in claim_cols:
        conn.execute("ALTER TABLE claim ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
    # Giveaway start standaard 'niet live' tot de admin op Go Live klikt.
    conn.execute(
        "INSERT OR IGNORE INTO setting (sleutel, waarde) VALUES ('giveaway_live', '0')"
    )


def init_db():
    conn = get_db()
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        conn.executescript(f.read())
    _migrate(conn)
    conn.commit()
    conn.close()
