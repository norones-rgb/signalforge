from cryptography.fernet import Fernet

from app.core import security


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key().decode("utf-8")
    security.settings.fernet_key = key

    token = "secret-token-123"
    encrypted = security.encrypt_token(token)
    assert encrypted and encrypted != token
    decrypted = security.decrypt_token(encrypted)
    assert decrypted == token
