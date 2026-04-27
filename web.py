from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import db

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


# Serve all files in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")