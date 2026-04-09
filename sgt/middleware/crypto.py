import os
import base64
import hashlib
import hmac
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from setup import AES_KEY, HMAC_KEY


def encrypt(data: str) -> str:
    aesgcm = AESGCM(AES_KEY)
    nonce = os.urandom(12)

    ciphertext = aesgcm.encrypt(nonce, data.encode(), None)

    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(enc_data: str) -> str:
    raw = base64.b64decode(enc_data)

    nonce = raw[:12]
    ciphertext = raw[12:]

    aesgcm = AESGCM(AES_KEY)
    data = aesgcm.decrypt(nonce, ciphertext, None)

    return data.decode()


def _build_message(data: str, timestamp: int, nonce: str, endpoint: str) -> str:
    return f"{endpoint}:{timestamp}:{nonce}:{data}"


def sign(data: str, timestamp: int, nonce: str, endpoint: str) -> str:
    message = _build_message(data, timestamp, nonce, endpoint)
    return hmac.new(HMAC_KEY, message.encode(), hashlib.sha256).hexdigest()


def verify(
    data: str, timestamp: int, nonce: str, endpoint: str, signature: str
) -> bool:
    expected = sign(data, timestamp, nonce, endpoint)
    return hmac.compare_digest(expected, signature)


def validate_request(payload: dict, endpoint: str, used_nonce_store) -> str:
    required_fields = ["data", "timestamp", "nonce", "signature"]

    for field in required_fields:
        if field not in payload:
            raise Exception(f"Missing field: {field}")

    data = payload["data"]
    timestamp = payload["timestamp"]
    nonce = payload["nonce"]
    signature = payload["signature"]

    now = int(time.time())
    if abs(now - int(timestamp)) > 30:
        raise Exception("Request expired")

    if nonce in used_nonce_store:
        raise Exception("Replay attack detected")

    used_nonce_store.add(nonce)

    if not verify(data, timestamp, nonce, endpoint, signature):
        raise Exception("Invalid signature")

    return decrypt(data)


def build_response(data: str, endpoint: str) -> dict:
    encrypted = encrypt(data)

    timestamp = int(time.time())
    nonce = os.urandom(8).hex()

    signature = sign(encrypted, timestamp, nonce, endpoint)

    return {
        "data": encrypted,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature,
    }
