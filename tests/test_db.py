import db
import pytest
import sqlite3

def test_add_card_round_trip(fresh_db):
    conn = db.get_connection()
    db.add_card(
        conn,
        card_id="base1-4",
        name="Charizard",
        set_name="Base Set",
        number="4",
        rarity="Holo Rare",
        market_price=350.00,
        price_updated_at="2026-05-07T00:00:00Z",
        image_url="https://example.com/charizard.png",
    )
    conn.commit()
    conn.close()

    row = db.get_card_by_id("base1-4")

    assert row is not None
    assert row["name"] == "Charizard"
    assert row["market_price"] == 350.00

def test_total_collection_value_multiplies_price_by_quantity(fresh_db, user_factory):
    user_id = user_factory("testuser")
    conn = db.get_connection()
    db.add_card(
        conn,
        card_id="base1-4",
        name="Charizard",
        set_name="Base Set",
        number="4",
        rarity="Holo Rare",
        market_price=350.00,
        price_updated_at="2026-05-07T00:00:00Z",
        image_url="https://example.com/charizard.png",
    )
    db.add_card(
        conn,
        card_id="base1-5",
        name="Blastoise",
        set_name="Base Set",
        number="5",
        rarity="Holo Rare",
        market_price=200.00,
        price_updated_at="2026-05-07T00:00:00Z",
        image_url="https://example.com/blastoise.png",
    )
    db.add_owned_card(
        conn,
        card_id="base1-4",
        quantity=2,
        purchase_price=300.00,
        condition="Near Mint",
        acquired_date="2026-05-01",
        user_id=user_id,
    )
    db.add_owned_card(
        conn,
        card_id="base1-5",
        quantity=3,
        purchase_price=150.00,  
        condition="Lightly Played",
        acquired_date="2026-05-02",
        user_id=user_id,
    )
    conn.commit()
    conn.close()

    total_value = db.get_total_collection_value(user_id)
    expected_value = (350.00 * 2) + (200.00 * 3)  # $700 + $600 = $1300
    assert total_value == pytest.approx(expected_value)

def test_add_card_upsert(fresh_db):
    conn = db.get_connection()
    db.add_card(
        conn,
        card_id="base1-4",
        name="Charizard",
        set_name="Base Set",
        number="4",
        rarity="Holo Rare",
        market_price=350.00,
        price_updated_at="2026-05-03",
        image_url="https://example.com/charizard.png",
    )
    conn.commit()

    # Update the same card with new price
    db.add_card(
        conn,
        card_id="base1-4",
        name="Charizard",
        set_name="Base Set",
        number="4",
        rarity="Holo Rare",
        market_price=400.00,  # Updated price
        price_updated_at="2026-05-07",
        image_url="https://example.com/charizard.png",
    )
    conn.commit()
    conn.close()

    row = db.get_card_by_id("base1-4")
    assert row is not None
    assert row["market_price"] == pytest.approx(400.00)  # Price should be updated

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) FROM cards WHERE id = ?", ("base1-4",)).fetchone()[0]
    conn.close()
    assert count == 1

def test_fk_violation_on_owned_cards(fresh_db, user_factory):
    user_id = user_factory("testuser")
    conn = db.get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        db.add_owned_card(
            conn,
            card_id="nonexistent-card",
            quantity=1,
            purchase_price=100.00,
            condition="Near Mint",
            acquired_date="2026-05-01",
            user_id=user_id,
        )
    conn.close()

def test_fk_violation_on_owned_cards_bad_card(fresh_db, user_factory):
    # Real user, fake card — only the card FK can fire
    user_id = user_factory("testuser")
    conn = db.get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        db.add_owned_card(
            conn,
            card_id="nonexistent-card",
            quantity=1,
            purchase_price=100.00,
            condition="Near Mint",
            acquired_date="2026-05-01",
            user_id=user_id,
        )
    conn.close()

def test_fk_violation_on_owned_cards_bad_user(fresh_db):
    # Real card, fake user — only the user FK can fire
    conn = db.get_connection()
    db.add_card(
        conn,
        card_id="base1-4",
        name="Charizard",
        set_name="Base Set",
        number="4",
        rarity="Holo Rare",
        market_price=350.00,
        price_updated_at="2026-05-07",
        image_url="https://example.com/charizard.png",
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.add_owned_card(
            conn,
            card_id="base1-4",
            quantity=1,
            purchase_price=100.00,
            condition="Near Mint",
            acquired_date="2026-05-01",
            user_id=999,  # Nonexistent user ID
        )
    conn.close()    