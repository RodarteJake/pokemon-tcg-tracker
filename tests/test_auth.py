import pytest  
import auth

def test_hash_password_verifies():
    """Tests that the password hashing function correctly hashes a password."""
    password = "testpassword"
    hashed = auth.hash_password(password)
    assert hashed != password  # Ensure it's actually hashed
    assert auth.verify_password(password, hashed)  # Should verify correctly

def test_verify_rejects_wrong_password():
    """Tests that the password verification function rejects a wrong password."""
    password = "testpassword"
    hashed = auth.hash_password(password)
    assert not auth.verify_password("wrongpassword", hashed)  # Should reject wrong password

def test_hash_salting():
    """Tests that hashing the same password twice produces different hashes due to salting. 

        Both hashes should still verify correctly."""
    password = "testpassword"
    hashed1 = auth.hash_password(password)
    hashed2 = auth.hash_password(password)
    assert hashed1 != hashed2  # Should produce different hashes due to salting
    assert auth.verify_password(password, hashed1)  # Both should verify correctly
    assert auth.verify_password(password, hashed2)

def test_token_round_trip():
    """Tests that creating an access token and then decoding it returns the original user ID."""
    user_id = 67
    token = auth.create_access_token(user_id)
    decoded_user_id = auth.decode_access_token(token)
    assert decoded_user_id == user_id  # Should decode back to original user ID

def test_malformed_token():
    """Tests that decoding a malformed token returns None."""
    malformed_token = "not.a.valid.token"
    assert auth.decode_access_token(malformed_token) is None  # Should return None for malformed

def test_tampered_token():
    """Tests that decoding a tampered token returns None."""
    user_id = 67
    token = auth.create_access_token(user_id)
    # Tamper with the token by changing a character
    tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert auth.decode_access_token(tampered_token) is None  # Should return None for tampered token

def test_expired_token(monkeypatch):
    monkeypatch.setattr(auth, "JWT_EXPIRY_MINUTES", -1)
    token = auth.create_access_token(123)
    assert auth.decode_access_token(token) is None

def test_get_current_user_no_token():
    """Tests that get_current_user raises an HTTPException when no token is provided."""
    with pytest.raises(auth.HTTPException) as exc_info:
        auth.get_current_user(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"

def test_get_current_user_invalid_token():
    """Tests that get_current_user raises an HTTPException when an invalid token is provided."""
    with pytest.raises(auth.HTTPException) as exc_info:
        auth.get_current_user("invalid.token.here")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"

def test_get_current_user_valid_token(user_factory):
    user_id = user_factory("testuser")
    token = auth.create_access_token(user_id)
    assert auth.get_current_user(token) == user_id

def test_get_current_user_deleted_user(fresh_db):
    """Tests that get_current_user raises an HTTPException when the token is valid but the user does not exist."""
    token = auth.create_access_token(999)
    with pytest.raises(auth.HTTPException) as exc_info:
        auth.get_current_user(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"

def test_get_optional_user_no_token():
    """Tests that get_optional_user returns None when no token is provided."""
    assert auth.get_optional_user(None) is None

def test_get_optional_user_invalid_token():
    """Tests that get_optional_user returns None when an invalid token is provided."""
    assert auth.get_optional_user("invalid.token.here") is None

def test_get_optional_user_valid_token(user_factory):
    """Tests that get_optional_user returns the correct user ID when a valid token is provided."""
    user_id = user_factory("testuser")
    token = auth.create_access_token(user_id)
    assert auth.get_optional_user(token) == user_id

def test_get_optional_user_deleted_user(fresh_db):
    """Tests that get_optional_user returns None when the token is valid but the user does not exist."""
    token = auth.create_access_token(999)
    assert auth.get_optional_user(token) is None
