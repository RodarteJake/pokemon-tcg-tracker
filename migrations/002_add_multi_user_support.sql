
BEGIN;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (user_id, email, username, hashed_password) VALUES (1, 'admin@example.com', 'JRodarte', '!');

CREATE TABLE owned_cards_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    card_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    purchase_price REAL,
    condition TEXT,
    acquired_date TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    CHECK (quantity > 0)
);

INSERT INTO owned_cards_new (id, card_id, quantity, purchase_price, condition, acquired_date, user_id)
SELECT id, card_id, quantity, purchase_price, condition, acquired_date, 1
FROM owned_cards;

DROP TABLE owned_cards;

ALTER TABLE owned_cards_new RENAME TO owned_cards;

COMMIT;