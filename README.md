# Pokémon TCG Collection Tracker

[Live Demo](https://pokemon-tcg-tracker.fly.dev/)

A personal Pokémon Trading Card Game collection tracker with live pricing, statistics, and a search-driven acquisition flow. Built as a full-stack project to learn SQL, REST APIs, and modern web fundamentals. 

Used Claude as a pair-programmer and tutor. I made the architecture and implementation decisions; Claude helped me reason through tradeoffs, catch bugs, and turn my notes into clear issues and documentation.

## Features

- **Live pricing** — fetches current market values from the Pokémon TCG API
- **Collection dashboard** — total value, total spent, gain/loss, and value-by-set breakdown
- **Search & acquire** — search the entire Pokémon TCG catalog with paginated results, click to add cards to your collection
- **Auth** — visitors get read-only access; log in with a password to add, edit, delete, or refresh prices
- **Local-first storage** — SQLite database, no cloud dependencies
- **Resilient price refresh** — batch refresh handles individual API failures without aborting

## Screenshots

**Collection dashboard**
<img width="1917" height="890" alt="Collection dashboard showing total value, gain/loss, and set breakdown" src="https://github.com/user-attachments/assets/e965ce2f-15bc-40af-9011-d37617ce408a" />

**Search**
<img width="1915" height="919" alt="Search results page" src="https://github.com/user-attachments/assets/ce28b097-7b26-46f2-85ea-b169d8516c66" />

**Add to collection**
<img width="429" height="563" alt="Add to collection modal" src="https://github.com/user-attachments/assets/4df39816-b7c9-4320-9bc6-380719e1046d" />

**Card detail**
<img width="565" height="396" alt="Owned card detail view" src="https://github.com/user-attachments/assets/dbb5dfdf-808d-4c00-bf05-7d9243b7a89a" />

## How it's built

**Backend**
- Python 3.11
- FastAPI — REST API framework
- SQLite — local database
- `requests` — Pokémon TCG API client

**Frontend**
- Vanilla HTML / CSS / JavaScript (no framework)
- Inter + JetBrains Mono via Google Fonts
- CSS Grid for responsive layout

**Architecture**
- `db.py` — database access layer
- `api.py` — Pokémon TCG API client
- `collection.py` — service layer bridging the API and the database
- `web.py` — FastAPI HTTP layer
- `seed.py` — reproducible test data setup
- `static/index.html` — single-page frontend

## Running locally

Requires Python 3.11+ installed.

```bash
# Clone the repo
git clone https://github.com/RodarteJake/pokemon-tcg-tracker.git
cd pokemon-tcg-tracker

# Set up a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Seed the database with sample data
python seed.py

# Run the web server
uvicorn web:app --reload
```

Then open http://127.0.0.1:8000 in your browser.

## Auth

Visitors get read-only access. To add, edit, delete, or refresh prices, log in with a single shared password.

Required env vars:

- `EDIT_PASSWORD` — the password the editor types in. If unset, login is disabled and the site is read-only.
- `SESSION_SECRET` — used to sign the session cookie. If unset, a random one is generated at startup (sessions expire on restart, fine for dev).
- `COOKIE_SECURE` — set to `true` in production (HTTPS-only cookie). Defaults to `false` for local dev.

For local dev, `EDIT_PASSWORD=hunter2 uvicorn web:app --reload` is enough.

For Fly:

```bash
flyctl secrets set EDIT_PASSWORD='<long random password>'
flyctl secrets set SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

`COOKIE_SECURE=true` is already set in `fly.toml`.

## Data sources

Card data and pricing courtesy of the [Pokémon TCG API](https://docs.pokemontcg.io/), with prices from TCGPlayer.

## License

MIT — see LICENSE file

## Credits

Favicon: [Pokemon icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/pokemon)