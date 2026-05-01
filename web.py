from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import db
import api 
import collection
from pydantic import BaseModel

db.init_db()

class AcquireRequest(BaseModel):
    card_id: str
    quantity: int = 1
    purchase_price: float | None = None
    condition: str | None = None
    acquired_date: str | None = None

app = FastAPI()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/cards")
def list_cards():
    rows = db.get_all_cards()
    return [dict(row) for row in rows]


@app.get("/cards/{card_id}")
def get_card(card_id: str):
    row = db.get_card_by_id(card_id)
    if row is None:
        return {"error": "Card not found"}
    return dict(row)

@app.get("/cards/{card_id}/ownership")
def card_ownership(card_id: str):
    """Return all ownership rows for a given card."""
    return db.get_ownership_rows(card_id)

@app.get("/stats/total-value")
def total_value():
    return {"total_value": db.get_total_collection_value()}


@app.get("/stats/total-spent")
def total_spent():
    return {"total_spent": db.get_total_amount_spent()}


@app.get("/stats/by-set")
def by_set():
    rows = db.get_value_by_set()
    return [dict(row) for row in rows]

@app.get("/api/search")
def search(
    name: str | None = None,
    set_id: str | None = None,
    rarity: str | None = None,
    types: str | None = None,
    supertype: str | None = None,
    subtype: str | None = None,
    artist: str | None = None,
    series: str | None = None,
    hp_min: int | None = None,
    hp_max: int | None = None,
    page: int = 1,
    page_size: int = 12,
):
    """Search the Pokémon TCG API with arbitrary filters."""
    return api.search_cards(
        name=name,
        set_id=set_id,
        rarity=rarity,
        types=types,
        supertype=supertype,
        subtype=subtype,
        artist=artist,
        series=series,
        hp_min=hp_min,
        hp_max=hp_max,
        page=page,
        page_size=page_size,
    )

@app.post("/collection/refresh-prices")
def refresh_prices():
    """Refresh market prices for every card in the collection."""
    collection.refresh_all_prices()
    return {"status": "ok"}

@app.post("/collection/acquire")
def acquire(request: AcquireRequest):
    """Acquire a card: fetch from API, save metadata, record ownership."""
    collection.acquire_card(
        card_id=request.card_id,
        quantity=request.quantity,
        purchase_price=request.purchase_price,
        condition=request.condition,
        acquired_date=request.acquired_date,
    )
    return {"status": "ok"}

class UpdateOwnedRequest(BaseModel):
    quantity: int
    purchase_price: float | None = None
    condition: str
    acquired_date: str | None = None


@app.patch("/collection/owned/{owned_id}")
def update_owned(owned_id: int, body: UpdateOwnedRequest):
    """Update an existing ownership row."""
    db.update_owned_card(
        owned_id=owned_id,
        quantity=body.quantity,
        purchase_price=body.purchase_price,
        condition=body.condition,
        acquired_date=body.acquired_date,
    )
    return {"status": "ok"}


@app.delete("/collection/owned/{owned_id}")
def delete_owned(owned_id: int):
    """Delete an ownership row. Cascades: if it was the last row for that card, also delete the card."""
    card_id = db.delete_owned_card(owned_id)
    if card_id is None:
        return {"status": "not_found"}

    remaining = db.count_ownership_rows(card_id)
    if remaining == 0:
        db.delete_card(card_id)
        return {"status": "ok", "cascade_deleted_card": True}
    return {"status": "ok", "cascade_deleted_card": False}

@app.get("/api/filters/sets")
def filter_sets():
    return api.get_sets()


@app.get("/api/filters/types")
def filter_types():
    return api.get_types()


@app.get("/api/filters/subtypes")
def filter_subtypes():
    return api.get_subtypes()


@app.get("/api/filters/supertypes")
def filter_supertypes():
    return api.get_supertypes()


@app.get("/api/filters/rarities")
def filter_rarities():
    return api.get_rarities()

@app.get("/stats/last-updated")
def last_updated():
    return {"last_updated": db.get_last_price_update()}

# Serve all files in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")