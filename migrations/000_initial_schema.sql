-- Initial schema, extracted from db.init_db(). Uses IF NOT EXISTS so existing production DBs no-op cleanly.
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    set_name TEXT,
    number TEXT,
    rarity TEXT,
    market_price REAL,
    price_updated_at TEXT,
    image_url TEXT
);


CREATE TABLE IF NOT EXISTS owned_cards (
    id INTEGER PRIMARY KEY,
    card_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    purchase_price REAL,
    condition TEXT,
    acquired_date TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

COMMIT;