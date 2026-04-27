import api
import db


def acquire_card(card_id, quantity, purchase_price, condition, acquired_date):
    """Fetch a card from the API and record that we now own it."""
    # 1. Fetch from API
    card_data = api.fetch_card_by_id(card_id)

    # 2. Save card metadata to local cards table
    db.add_card(
        card_id=card_data["id"],
        name=card_data["name"],
        set_name=card_data["set"]["name"],
        number=card_data["number"],
        rarity=card_data.get("rarity"),
        market_price=None,  # we'll handle pricing later
        image_url=card_data["images"]["small"],
    )

    # 3. Record the ownership
    db.add_owned_card(
        card_id=card_id,
        quantity=quantity,
        purchase_price=purchase_price,
        condition=condition,
        acquired_date=acquired_date,
    )