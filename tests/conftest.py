import pytest
import db

@pytest.fixture
def fresh_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    db.init_db()
    yield db.DB_PATH