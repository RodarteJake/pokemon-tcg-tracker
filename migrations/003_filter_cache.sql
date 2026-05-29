-- Local cache for /api/filters/* dropdown data from pokemontcg.io.
-- Refreshed manually via scripts/refresh_filter_cache.py; not auto-refreshed.
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS filter_cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
