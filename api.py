import requests

BASE_URL = "https://api.pokemontcg.io/v2"


def fetch_card_by_id(card_id):
    """Fetch a single card from the Pokémon TCG API by its ID."""
    response = requests.get(f"{BASE_URL}/cards/{card_id}")
    response.raise_for_status()
    return response.json()["data"]

def search_cards_by_name(name):
    """Search the Pokémon TCG API for cards matching a name. Returns a list."""
    response = requests.get(
        f"{BASE_URL}/cards",
        params={"q": f'name:"{name}"'}
    )
    response.raise_for_status()
    return response.json()["data"]