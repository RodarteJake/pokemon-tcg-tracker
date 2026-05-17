import pytest
import db

@pytest.fixture
def fresh_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    db.run_migrations()
    yield db.DB_PATH

def create_test_user(username, email=None, hashed_password="hashedpassword"):
    email = f"{username}@example.com" if email is None else email
    return db.create_user(username=username, email=email, hashed_password=hashed_password)


@pytest.fixture
def user_factory(fresh_db):  # fresh_db dependency ensures clean test DB
    def _create_user(username, email=None, hashed_password="hashedpassword"):
        return create_test_user(username, email, hashed_password)
    return _create_user