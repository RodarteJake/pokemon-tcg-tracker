import sqlite3


def get_connection():
    """Open a connection to the database with row_factory set."""
    conn = sqlite3.connect("collection.db")
    conn.row_factory = sqlite3.Row
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