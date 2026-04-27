import db

cards = db.get_all_cards()
print(f"Found {len(cards)} cards in the database.\n")

for card in cards:
    print(f"{card['name']:15} {card['set_name']:15} ${card['market_price']}")

charizard = db.get_card_by_id("base1-4")
print(f"\nLooked up base1-4: {charizard['name']} from {charizard['set_name']}, ${charizard['market_price']}")

base_cards = db.get_cards_by_set("Base")
print(f"\nBase set has {len(base_cards)} cards:")
for card in base_cards:
    print(f"  {card['name']}")

total = db.get_total_collection_value()
print(f"\nTotal collection value: ${total:.2f}")