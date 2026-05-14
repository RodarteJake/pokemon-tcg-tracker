# Pokémon TCG Collection Tracker

[Live Demo](https://pokemon-tcg-tracker.fly.dev/)

A Pokémon Trading Card Game collection tracker with live pricing, statistics, and a search-driven acquisition flow. Built as a full-stack project to learn SQL, REST APIs, and modern web fundamentals.

Used Claude as a pair-programmer and tutor. I made the architecture and implementation decisions; Claude helped me reason through tradeoffs, catch bugs, and turn my notes into clear issues and documentation.

## Features

- **Live pricing** — fetches current market values from the Pokémon TCG API
- **Collection dashboard** — total value, total spent, gain/loss, and value-by-set breakdown
- **Search & acquire** — search the entire Pokémon TCG catalog with paginated results, click to add cards to your collection
- **Multi-user auth** — register an account, log in with username or email, JWT stored in HttpOnly cookies
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
- Python 3.12
- FastAPI — REST API framework
- SQLite — local database with a versioned migration system
- `bcrypt` + `PyJWT` — password hashing and JWT auth
- `requests` — Pokémon TCG API client

**Frontend**
- Vanilla HTML / CSS / JavaScript (no framework)
- ES modules — `main.js`, `auth.js`, `data-loaders.js`, `edit-collection.js`, `search.js`, `searchable-dropdown.js`
- Inter + JetBrains Mono via Google Fonts
- CSS Grid for responsive layout

**Architecture**
- `db.py` — database access layer
- `auth.py` — password hashing, JWT creation and verification, FastAPI auth dependencies
- `api.py` — Pokémon TCG API client
- `collection.py` — service layer bridging the API and the database
- `web.py` — FastAPI HTTP layer
- `migrations/` — versioned SQL migration files

**Data model**
- `cards` — shared card metadata (name, set, image, market price). Every Pikachu is the same Pikachu regardless of who owns it.
- `owned_cards` — per-user ownership rows (quantity, condition, purchase price, acquired date)
- `users` — accounts with hashed passwords

## Auth

Register an account at the live demo. Login accepts either username or email. JWT issued on login/register, stored in an HttpOnly cookie.

Required env vars:

- `JWT_SECRET` — used to sign JWT tokens. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `COOKIE_SECURE` — set to `true` in production (HTTPS-only cookie). Defaults to `false` for local dev.

## Data sources

Card data and pricing courtesy of the [Pokémon TCG API](https://docs.pokemontcg.io/), with prices from TCGPlayer.

## License

MIT — see LICENSE file

## Credits

Favicon: [Pokemon icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/pokemon)