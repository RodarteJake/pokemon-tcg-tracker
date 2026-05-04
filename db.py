import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "collection.db")

def init_db():
    """Create tables if they don't exist. Safe to run on every startup."""
    conn = get_connection()
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
    conn.commit()
    conn.close()

def get_connection():
    """Open a connection to the database with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_all_cards():
    """Return every card in the cards table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_card_by_id(card_id):
    """Return a single card by its ID, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_cards_by_set(set_name):
    """Return all cards from a given set. Returns an empty list if no cards found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE set_name = ?", (set_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_price_update():
    """Return the most recent price_updated_at timestamp across all cards. None if no cards."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(price_updated_at) AS last_updated FROM cards")
    row = cursor.fetchone()
    conn.close()
    return row["last_updated"]

def add_card(card_id, name, set_name, number, rarity, market_price, price_updated_at, image_url):
    """Add a new card to the cards table. Silently ignores duplicates."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO cards
        (id, name, set_name, number, rarity, market_price, price_updated_at, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (card_id, name, set_name, number, rarity, market_price, price_updated_at, image_url)
    )
    conn.commit()
    conn.close()

def add_owned_card(card_id, quantity, purchase_price, condition, acquired_date):
    """Add a new owned card record. Silently ignores if card_id doesn't exist in cards table."""
    conn = get_connection()
    cursor = conn.cursor()  
    cursor.execute(
        """
        INSERT INTO owned_cards
        (card_id, quantity, purchase_price, condition, acquired_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (card_id, quantity, purchase_price, condition, acquired_date)
    )
    conn.commit()
    conn.close()

def get_total_collection_value():
    """Return the total current market value of the entire collection."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(cards.market_price * owned_cards.quantity) AS total_value
        FROM owned_cards
        JOIN cards ON owned_cards.card_id = cards.id
    """)
    row = cursor.fetchone()
    conn.close()
    return row["total_value"] or 0

def update_card_price(card_id, market_price, price_updated_at):
    """Update the market price of an existing card."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE cards
        SET market_price = ?, price_updated_at = ?
        WHERE id = ?
        """,
        (market_price, price_updated_at, card_id)
    )
    conn.commit()
    conn.close()

def get_total_amount_spent():
    """Return the total amount of money spent on the collection (purchase prices)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(purchase_price * quantity) AS total_spent
        FROM owned_cards
    """)
    row = cursor.fetchone()
    conn.close()
    return row["total_spent"] or 0

def get_value_by_set():
    """Return a list of (set_name, total_value) rows, sorted by value descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cards.set_name, SUM(cards.market_price * owned_cards.quantity) AS set_value
        FROM owned_cards
        JOIN cards ON owned_cards.card_id = cards.id
        GROUP BY cards.set_name
        ORDER BY set_value DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows 

def get_ownership_rows(card_id):
    """Return all ownership rows in owned_cards for the given card_id, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM owned_cards WHERE card_id = ? ORDER BY acquired_date DESC",
        (card_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_owned_card(owned_id, quantity, purchase_price, condition, acquired_date):
    """Update an existing ownership row with new values."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE owned_cards
           SET quantity = ?,
               purchase_price = ?,
               condition = ?,
               acquired_date = ?
         WHERE id = ?
        """,
        (quantity, purchase_price, condition, acquired_date, owned_id),
    )
    conn.commit()
    conn.close()


def delete_owned_card(owned_id):
    """Delete an ownership row by id. Returns the card_id of the deleted row, for cascade logic."""
    conn = get_connection()
    cursor = conn.cursor()
    # Find the card_id first so caller can decide whether to cascade
    cursor.execute("SELECT card_id FROM owned_cards WHERE id = ?", (owned_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None
    card_id = row["card_id"]
    cursor.execute("DELETE FROM owned_cards WHERE id = ?", (owned_id,))
    conn.commit()
    conn.close()
    return card_id


def count_ownership_rows(card_id):
    """Return how many ownership rows exist for the given card_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM owned_cards WHERE card_id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return row["cnt"]


def delete_card(card_id):
    """Delete a card from the cards table by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()