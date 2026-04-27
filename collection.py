import api
import db


def acquire_card(card_id, quantity, purchase_price, condition, acquired_date):
    """Fetch a card from the API and record that we now own it."""
    card_data = api.fetch_card_by_id(card_id)

    market_price = api.extract_market_price(card_data)
    price_updated_at = card_data.get("tcgplayer", {}).get("updatedAt")

    db.add_card(
        card_id=card_data["id"],
        name=card_data["name"],
        set_name=card_data["set"]["name"],
        number=card_data["number"],
        rarity=card_data.get("rarity"),
        market_price=market_price,
        price_updated_at=price_updated_at,
        image_url=card_data["images"]["small"],
    )

    db.update_card_price(
        card_id=card_data["id"],
        market_price=market_price,
        price_updated_at=price_updated_at,
    )

    db.add_owned_card(
        card_id=card_id,
        quantity=quantity,
        purchase_price=purchase_price,
        condition=condition,
        acquired_date=acquired_date,
    )