import sqlite3

conn = sqlite3.connect("collection.db")
cursor = conn.cursor()

conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
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
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS owned_cards (
        id INTEGER PRIMARY KEY,
        card_id TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        purchase_price REAL,
        condition TEXT, 
        acquired_date TEXT,
        FOREIGN KEY (card_id) REFERENCES cards(id)
    );
""")

# Insert sample cards
sample_cards = [
    # (id, name, set_name, number, rarity, market_price, price_updated_at, image_url) 
    ("base1-4",   "Charizard",  "Base",        "4",    "Rare Holo", 350.00, "2026-04-27", "https://images.pokemontcg.io/base1/4.png"),
    ("base1-2",   "Blastoise",  "Base",        "2",    "Rare Holo", 120.00, "2026-04-27", "https://images.pokemontcg.io/base1/2.png"),
    ("base1-15",  "Venusaur",   "Base",        "15",   "Rare Holo",  90.00, "2026-04-27", "https://images.pokemontcg.io/base1/15.png"),
    ("base1-58",  "Pikachu",    "Base",        "58",   "Common",      8.00, "2026-04-27", "https://images.pokemontcg.io/base1/58.png"),
    ("base1-10",  "Mewtwo",     "Base",        "10",   "Rare Holo",  75.00, "2026-04-27", "https://images.pokemontcg.io/base1/10.png"),
    ("jungle-12", "Jolteon",    "Jungle",      "4",    "Rare Holo",  35.00, "2026-04-27", "https://images.pokemontcg.io/jungle/4.png"),
    ("jungle-51", "Eevee",      "Jungle",      "51",   "Common",      3.00, "2026-04-27", "https://images.pokemontcg.io/jungle/51.png"),
    ("fossil-2",  "Articuno",   "Fossil",      "2",    "Rare Holo",  45.00, "2026-04-27", "https://images.pokemontcg.io/fossil/2.png"),
    ("neo1-9",    "Lugia",      "Neo Genesis", "9",    "Rare Holo", 220.00, "2026-04-27", "https://images.pokemontcg.io/neo1/9.png"),
    ("swsh4-25",  "Charizard",  "Vivid Voltage","25",  "Rare",       12.00, "2026-04-27", "https://images.pokemontcg.io/swsh4/25.png"),
]

cursor.executemany(
    """
    INSERT OR IGNORE INTO cards
    (id, name, set_name, number, rarity, market_price, price_updated_at, image_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    sample_cards
)

# Insert sample ownership records
sample_owned = [
    # (card_id, quantity, purchase_price, condition, acquired_date)
    ("base1-4",    1, 280.00, "Near Mint",        "2024-08-15"),
    ("base1-4",    1, 150.00, "Lightly Played",   "2025-02-03"),
    ("base1-2",    2,  95.00, "Near Mint",        "2024-11-20"),
    ("base1-58",   4,   2.00, "Near Mint",        "2025-01-10"),
    ("jungle-51",  3,   1.50, "Lightly Played",   "2025-03-22"),
    ("fossil-2",   1,  40.00, "Near Mint",        "2025-06-01"),
    ("neo1-9",     1, 180.00, "Near Mint",        "2024-12-25"),
    ("swsh4-25",   2,  10.00, "Near Mint",        "2026-01-15"),
]

cursor.executemany(
    """
    INSERT INTO owned_cards
    (card_id, quantity, purchase_price, condition, acquired_date)
    VALUES (?, ?, ?, ?, ?)
    """,
    sample_owned
)

print(f"Seeded {len(sample_cards)} cards and {len(sample_owned)} ownership records.")

conn.commit()

print("\n--- Cards ---")
for row in cursor.execute("SELECT id, name, set_name, market_price FROM cards"):
    print(dict(row))

print("\n--- Owned cards ---")
for row in cursor.execute("SELECT card_id, quantity, condition, purchase_price FROM owned_cards"):
    print(dict(row))

conn.close()