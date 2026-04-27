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


# Serve all files in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")