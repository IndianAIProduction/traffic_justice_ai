from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_access_token_creation():
    token = create_access_token(data={"sub": "user123"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["type"] == "access"


def test_refresh_token_creation():
    token = create_refresh_token(data={"sub": "user456"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user456"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None
