import os
import secrets
import sqlite3

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

import auth
import db
import api
import collection

load_dotenv()

db.init_db()
db.run_migrations()

EDIT_PASSWORD = os.environ.get("EDIT_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"


class AcquireRequest(BaseModel):
    card_id: str
    quantity: int = 1
    purchase_price: float | None = None
    condition: str | None = None
    acquired_date: str | None = None


class LoginRequest(BaseModel):
    identifier: str  # username or email
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=COOKIE_SECURE,
    max_age=60 * 60 * 24 * 30,
)

def require_auth(request: Request):
    if not request.session.get("authed"):
        raise HTTPException(status_code=401, detail="Login required")

@app.post("/auth/logout")
def logout(response: Response):
    """Log out by clearing the auth cookie."""
    response.delete_cookie(
        key="access_token",
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return {"status": "ok"}


@app.get("/auth/status")
def auth_status(user_id: int | None = Depends(auth.get_optional_user)):
    """Return current user info if authenticated, or null."""
    if user_id is None:
        return {"user": None}
    user = db.get_user_by_id(user_id)
    if user is None:
        return {"user": None}  
    return {"user": {"user_id": user["user_id"], "username": user["username"], "email": user["email"]}}


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
def total_value(user_id: int = Depends(auth.get_current_user)):
    return {"total_value": db.get_total_collection_value(user_id)}

@app.get("/stats/total-spent")
def total_spent(user_id: int = Depends(auth.get_current_user)):
    return {"total_spent": db.get_total_amount_spent(user_id)}


@app.get("/stats/by-set")
def by_set(user_id: int = Depends(auth.get_current_user)):
    rows = db.get_value_by_set(user_id)
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
def refresh_prices(user_id: int = Depends(auth.get_current_user)):
    """Refresh market prices for every card in the collection."""
    collection.refresh_all_prices()
    return {"status": "ok"}

@app.post("/collection/acquire")
def acquire(request: AcquireRequest, user_id: int = Depends(auth.get_current_user)):
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
def update_owned(owned_id: int, body: UpdateOwnedRequest, user_id: int = Depends(auth.get_current_user)):
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
def delete_owned(owned_id: int, user_id: int = Depends(auth.get_current_user)):
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

def set_auth_cookie(response: Response, user_id: int) -> None:
    """Issue a JWT access token and set it as an HttpOnly cookie."""
    token = auth.create_access_token(user_id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=auth.JWT_EXPIRY_MINUTES * 60,
    )

@app.post("/auth/register")
def register(body: RegisterRequest, response: Response):
    """Register a new user with username, email, and password. Returns user info and sets auth cookie."""
    username = body.username.strip()
    email = body.email.strip().lower()
    hashed_password = auth.hash_password(body.password)

    try:
        user_id = db.create_user(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    set_auth_cookie(response, user_id)

    return {"user_id": user_id, "username": username, "email": email}

@app.post("/auth/login")
def login(body: LoginRequest, response: Response):
    """Authenticate a user with username/email and password. Returns user info and sets auth cookie."""
    identifier = body.identifier.strip()

    user = db.get_user_for_login(identifier)
    if user is None or not auth.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")

    set_auth_cookie(response, user["user_id"])

    return {"user_id": user["user_id"], "username": user["username"], "email": user["email"]}

# Serve all files in /static at the /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")