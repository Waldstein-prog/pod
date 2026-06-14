CREATE TABLE IF NOT EXISTS pod (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    naam          TEXT NOT NULL,
    categorie     TEXT NOT NULL,
    image_bestand TEXT NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 0,  -- huidig aantal (bewerkbaar, auto-save)
    begin_stock   INTEGER NOT NULL DEFAULT 0   -- startwaarde waar Reset naar terugzet
);

CREATE TABLE IF NOT EXISTS claim (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pod_id        INTEGER NOT NULL REFERENCES pod(id) ON DELETE CASCADE,
    bezoeker_naam TEXT NOT NULL,                -- Twitch-naam
    palia_naam    TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | confirmed
    tijdstip      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS setting (
    sleutel TEXT PRIMARY KEY,
    waarde  TEXT NOT NULL
);
