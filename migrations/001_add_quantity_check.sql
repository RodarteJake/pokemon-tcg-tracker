-- Disable FK enforcement during table rebuild.
-- Re-enabled automatically by get_connection() on next connection.
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE owned_cards_new (
    id INTEGER PRIMARY KEY,
    card_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    purchase_price REAL,
    condition TEXT,
    acquired_date TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    CHECK (quantity > 0)
);

INSERT INTO owned_cards_new (id, card_id, quantity, purchase_price, condition, acquired_date)
SELECT id, card_id, quantity, purchase_price, condition, acquired_date FROM owned_cards;

DROP TABLE owned_cards;

ALTER TABLE owned_cards_new RENAME TO owned_cards;

COMMIT;

