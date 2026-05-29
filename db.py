import json
import sqlite3
import os
from contextlib import closing

DB_PATH = os.environ.get("DB_PATH", "collection.db")

# DUPLICATED in data-loaders.js — update both
CONDITION_VALUE_PERCENTS = {
    "Near Mint": 1.0,
    "Lightly Played": 0.85,
    "Moderately Played": 0.65,
    "Heavily Played": 0.45,
    "Damaged": 0.25,
}

# connection & migrations

def get_connection():
    """Open a connection to the database with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def run_migrations():
    """Run all migration scripts in the migrations/ directory and record which ones have been applied."""
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("SELECT name FROM schema_migrations")
        applied = set(row["name"] for row in cursor.fetchall())
        migration_files = sorted(f for f in os.listdir("migrations") if f.endswith(".sql"))
        # the migration files run BEGIN TRANSACTION and COMMIT themselves, so don't wrap this loop in a transaction
        for filename in migration_files:
            if filename in applied:
                continue
            with open(os.path.join("migrations", filename), "r") as f:
                sql = f.read()
                print(f"Applying migration: {filename}")
                cursor.executescript(sql)
            cursor.execute("INSERT INTO schema_migrations (name) VALUES (?)", (filename,))
        conn.commit()

# card catalog

def get_all_cards():
    """Return every card in the cards table."""
    with closing(get_connection()) as conn:
        return conn.execute("SELECT * FROM cards").fetchall()

def get_card_by_id(card_id):
    """Return a single card by its ID, or None if not found."""
    with closing(get_connection()) as conn:
        return conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()

def get_cards_by_set(set_name):
    """Return all cards from a given set. Returns an empty list if no cards found."""
    with closing(get_connection()) as conn:
        return conn.execute("SELECT * FROM cards WHERE set_name = ?", (set_name,)).fetchall()

def get_last_price_update():
    """Return the most recent price_updated_at timestamp across all cards. None if no cards."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT MAX(price_updated_at) AS last_updated FROM cards"
        ).fetchone()["last_updated"]

def add_card(conn, card_id, name, set_name, number, rarity, market_price, price_updated_at, image_url):
    """Insert a new card or update an existing one's price. Caller is responsible for committing the transaction."""
    conn.execute(
        """
        INSERT INTO cards
        (id, name, set_name, number, rarity, market_price, price_updated_at, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
            market_price = excluded.market_price,
            price_updated_at = excluded.price_updated_at
        """,
        (card_id, name, set_name, number, rarity, market_price, price_updated_at, image_url),
    )

def update_card_price(card_id, market_price, price_updated_at):
    """Update the market price and price_updated_at for a card by its ID."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "UPDATE cards SET market_price = ?, price_updated_at = ? WHERE id = ?",
            (market_price, price_updated_at, card_id),
        )

def delete_card(card_id):
    """Delete a card from the cards table by id."""
    with closing(get_connection()) as conn, conn:
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))

# ownership 

def get_owned_cards(user_id):
    """Return all owned cards for a given user, including metadata and ownership details."""
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT owned_cards.id as owned_id, owned_cards.card_id, owned_cards.quantity, owned_cards.purchase_price, owned_cards.condition, owned_cards.acquired_date, 
            cards.name, cards.set_name, cards.number, cards.rarity, cards.market_price, cards.image_url
            FROM owned_cards
            JOIN cards ON owned_cards.card_id = cards.id
            WHERE owned_cards.user_id = ?
            ORDER BY owned_cards.acquired_date DESC
        """, (user_id,)).fetchall()

def get_ownership_rows(card_id, user_id):
    """Return all ownership rows in owned_cards for the given card_id and user_id, newest first."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT * FROM owned_cards WHERE card_id = ? AND user_id = ? ORDER BY acquired_date DESC",
            (card_id, user_id),
        ).fetchall()

def count_ownership_rows(card_id):
    """Return how many ownership rows exist globally for the given card_id (used for catalog cascade cleanup)."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT COUNT(*) AS cnt FROM owned_cards WHERE card_id = ?",
            (card_id,),
        ).fetchone()["cnt"]

def get_total_collection_value(user_id):
    """Return the total current market value of the given user's collection."""
    with closing(get_connection()) as conn:
        rows = conn.execute("""
            SELECT cards.market_price, owned_cards.quantity, owned_cards.condition
            FROM owned_cards
            JOIN cards ON owned_cards.card_id = cards.id
            WHERE owned_cards.user_id = ?
        """, (user_id,)).fetchall()

        total = 0
        for row in rows:
            multiplier = CONDITION_VALUE_PERCENTS.get(row["condition"], 1.0)
            total += row["market_price"] * row["quantity"] * multiplier
        return total

def get_total_amount_spent(user_id):
    """Return the total amount of money spent on the user_id's collection (purchase prices)."""
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT SUM(purchase_price * quantity) AS total_spent
            FROM owned_cards
            WHERE owned_cards.user_id = ?
        """, (user_id,)).fetchone()["total_spent"] or 0


def get_value_by_set(user_id):
    """Return a list of (set_name, total_value) rows owned by the user, sorted by value descending."""
    with closing(get_connection()) as conn:
        rows = conn.execute("""
            SELECT cards.set_name, cards.market_price, owned_cards.quantity, owned_cards.condition
            FROM owned_cards
            JOIN cards ON owned_cards.card_id = cards.id
            WHERE owned_cards.user_id = ?
        """, (user_id,)).fetchall()

        set_totals = {}
        for row in rows:
            set_name = row["set_name"]
            multiplier = CONDITION_VALUE_PERCENTS.get(row["condition"], 1.0)
            value = row["market_price"] * row["quantity"] * multiplier
            set_totals[set_name] = set_totals.get(set_name, 0) + value

        return [
            {"set_name": name, "set_value": value}
            for name, value in sorted(set_totals.items(), key=lambda x: x[1], reverse=True)
        ]

def add_owned_card(conn, card_id, quantity, purchase_price, condition, acquired_date, user_id):
    """Insert a new ownership row for an existing card. Caller is responsible for committing the transaction.
    
    Raises:
    sqlite3.IntegrityError: 
        if card_id does not exist in the cards table,
        or if quantity is not positive (CHECK constraint)."""
    conn.execute(
        """
        INSERT INTO owned_cards
        (card_id, quantity, purchase_price, condition, acquired_date, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (card_id, quantity, purchase_price, condition, acquired_date, user_id),
    )

def update_owned_card(owned_id, quantity, purchase_price, condition, acquired_date, user_id):
    """Update an existing ownership row owned by the given user_id.
    
    Returns owned_id on success, or None if the row doesn't exist or doesn't belong to user_id.
    """
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT user_id FROM owned_cards WHERE id = ?",
            (owned_id,),
        ).fetchone()
        if row is None or row["user_id"] != user_id:
            return None
        with conn:
            conn.execute(
                """
                UPDATE owned_cards
                SET quantity = ?, purchase_price = ?, condition = ?, acquired_date = ?
                WHERE id = ? AND user_id = ?
                """,
                (quantity, purchase_price, condition, acquired_date, owned_id, user_id),
            )
        return owned_id

def delete_owned_card(owned_id, user_id):
    """Delete an ownership row by id and user_id. Returns the card_id of the deleted row, for cascade logic."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT card_id FROM owned_cards WHERE id = ? AND user_id = ?",
            (owned_id, user_id),
        ).fetchone()
        if row is None:
            return None
        card_id = row["card_id"]
        with conn:
            conn.execute(
                "DELETE FROM owned_cards WHERE id = ? AND user_id = ?",
                (owned_id, user_id),
            )
        return card_id

# users / auth

def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    """Look up a user by ID. Returns the row or None if not found."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT user_id, username, email, created_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

def get_user_for_login(identifier: str) -> sqlite3.Row | None:
    """Look up a user by username or email for login purposes. Returns the row (including hashed_password) or None if not found."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT user_id, username, email, hashed_password FROM users WHERE username = ? OR email = ?",
            (identifier, identifier),
        ).fetchone()

def create_user(username: str, email: str, hashed_password: str) -> int:
    """Create a new user and return their user_id.

    Raises:
        sqlite3.IntegrityError: if username or email is already taken.
    """
    with closing(get_connection()) as conn, conn:
        return conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (username, email, hashed_password),
        ).lastrowid

# filter cache

def get_filter_cache(key:str) -> list | None:
    """Return the cached value for the given filter key, or None if not cached."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT value FROM filter_cache WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])


def set_filter_cache(key: str, value: list) -> None:
    """Cache or update the filter value for the given key. Bumps updated_at on write."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            INSERT INTO filter_cache (key, value)
            VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(value)),
        )