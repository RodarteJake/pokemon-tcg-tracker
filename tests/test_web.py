from fastapi.testclient import TestClient
import db
from web import app

client = TestClient(app)

def test_filter_sets_endpoint_returns_cached_data(fresh_db):
    db.set_filter_cache("sets", [{"id": "test1", "name": "Test Set"}])
    
    response = client.get("/api/filters/sets")
    
    assert response.status_code == 200
    assert response.json() == [{"id": "test1", "name": "Test Set"}]

def test_filter_endpoint_returns_empty_when_cache_missing(fresh_db):
    response = client.get("/api/filters/sets")
    assert response.status_code == 200
    assert response.json() == []