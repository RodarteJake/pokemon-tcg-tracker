import db
import pytest

def test_get_filter_cache_returns_none_when_key_missing(fresh_db):
    assert db.get_filter_cache("nonexistent_key") is None

def test_filter_cache_round_trip(fresh_db):
    key = "test_key"
    value = [{"id": "a", "name": "foo", "set": "a"}]
    db.set_filter_cache(key, value)
    cached_value = db.get_filter_cache(key)
    assert cached_value == value

def test_set_filter_cache_updates_existing_row(fresh_db):
    key = "test_key"
    initial_value = [{"id": "a", "name": "foo", "set": "a"}]
    updated_value = [{"id": "b", "name": "foo", "set": "b"}]
    db.set_filter_cache(key, initial_value) 
    db.set_filter_cache(key, updated_value)
    cached_value = db.get_filter_cache(key)
    assert cached_value == updated_value    
