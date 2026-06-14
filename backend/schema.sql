CREATE TABLE IF NOT EXISTS pod (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    naam          TEXT NOT NULL,
    categorie     TEXT NOT NULL,
    image_bestand TEXT NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS claim (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pod_id        INTEGER NOT NULL REFERENCES pod(id) ON DELETE CASCADE,
    bezoeker_naam TEXT NOT NULL,
    tijdstip      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS setting (
    sleutel TEXT PRIMARY KEY,
    waarde  TEXT NOT NULL
);
