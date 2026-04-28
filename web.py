from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import db
import api 
import collection
from pydantic import BaseModel


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
def search(name: str, page: int = 1, page_size: int = 12):
    """Search the Pokémon TCG API. Returns a pagination envelope: data, page, pageSize, totalCount."""
    return api.search_cards_by_name(name, page=page, page_size=page_size)


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

# Serve all files in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")