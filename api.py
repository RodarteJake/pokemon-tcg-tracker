import requests

BASE_URL = "https://api.pokemontcg.io/v2"

def fetch_card_by_id(card_id):
    """Fetch a single card from the Pokémon TCG API by its ID."""
    response = requests.get(f"{BASE_URL}/cards/{card_id}")
    response.raise_for_status()
    return response.json()["data"]

def search_cards_by_name(name, page=1, page_size=12):
    """Search the Pokémon TCG API. Returns full pagination envelope: data, page, pageSize, totalCount."""
    params = {
        "q": f'name:"{name}"',
        "page": page,
        "pageSize": page_size,
    }
    response = requests.get(f"{BASE_URL}/cards", params=params)
    response.raise_for_status()
    return response.json()  

def extract_market_price(card_data):
    """Pick the highest 'market' price across all TCGPlayer variants. Returns None if no pricing available."""
    tcgplayer = card_data.get("tcgplayer")
    if not tcgplayer:
        return None

    prices = tcgplayer.get("prices")
    if not prices:
        return None

    market_prices = []
    for variant_name, variant_prices in prices.items():
        market = variant_prices.get("market")
        if market is not None:
            market_prices.append(market)

    if not market_prices:
        return None

    return max(market_prices)