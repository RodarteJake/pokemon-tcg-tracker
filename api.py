import requests

BASE_URL = "https://api.pokemontcg.io/v2"

def fetch_card_by_id(card_id):
    """Fetch a single card from the Pokémon TCG API by its ID."""
    response = requests.get(f"{BASE_URL}/cards/{card_id}")
    response.raise_for_status()
    return response.json()["data"]

def search_cards(
    name=None,
    set_id=None,
    rarity=None,
    types=None,
    supertype=None,
    subtype=None,
    artist=None,
    series=None,
    hp_min=None,
    hp_max=None,
    page=1,
    page_size=12,
):
    """
    Search the Pokémon TCG API with arbitrary filters.
    Any filter can be None (omitted). At least one should be provided in practice.
    Returns the full pagination envelope.
    """
    query_parts = []

    if name:
        # Fuzzy name match: wildcard at both ends
        query_parts.append(f'name:*{name}*')
    if set_id:
        query_parts.append(f'set.id:{set_id}')
    if rarity:
        query_parts.append(f'rarity:"{rarity}"')
    if types:
        query_parts.append(f'types:{types}')
    if supertype:
        query_parts.append(f'supertype:{supertype}')
    if subtype:
        query_parts.append(f'subtypes:"{subtype}"')
    if artist:
        query_parts.append(f'artist:"{artist}"')
    if series:
        query_parts.append(f'set.series:"{series}"')
    if hp_min is not None:
        query_parts.append(f'hp:[{hp_min} TO *]')
    if hp_max is not None:
        query_parts.append(f'hp:[* TO {hp_max}]')

    # If no filters at all, search wildcard (returns all cards, but we still need *something*)
    if not query_parts:
        query_parts.append("*:*")

    query = " ".join(query_parts)

    params = {
        "q": query,
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

def get_sets():
    """Fetch all sets from the Pokémon TCG API. Returns a list of set objects."""
    response = requests.get(f"{BASE_URL}/sets")
    response.raise_for_status()
    return response.json()["data"]


def get_types():
    """Fetch all Pokémon types (Fire, Water, etc.). Returns a list of strings."""
    response = requests.get(f"{BASE_URL}/types")
    response.raise_for_status()
    return response.json()["data"]


def get_subtypes():
    """Fetch all card subtypes (Stage 1, VMAX, etc.). Returns a list of strings."""
    response = requests.get(f"{BASE_URL}/subtypes")
    response.raise_for_status()
    return response.json()["data"]


def get_supertypes():
    """Fetch all card supertypes (Pokémon, Trainer, Energy). Returns a list of strings."""
    response = requests.get(f"{BASE_URL}/supertypes")
    response.raise_for_status()
    return response.json()["data"]


def get_rarities():
    """Fetch all card rarities (Common, Rare Holo, etc.). Returns a list of strings."""
    response = requests.get(f"{BASE_URL}/rarities")
    response.raise_for_status()
    return response.json()["data"]