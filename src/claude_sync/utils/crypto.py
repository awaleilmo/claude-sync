"""Crypto utilities for AES-256-GCM encryption.

Fondasi enkripsi untuk Phase 6+.
Belum diaktifkan pada export/import.

Standar:
    - KDF: PBKDF2HMAC + SHA256
    - Encryption: AES-256-GCM
    - Salt: 16 byte random
    - Nonce: 12 byte random
    - Payload format: MAGIC + VERSION + SALT + NONCE + CIPHERTEXT
"""

from __future__ import annotations

import os
from struct import pack, unpack

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"CSYN"
VERSION = 1
SALT_LEN = 16
NONCE_LEN = 12
KDF_LEN = 32
KDF_ITER = 480_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KDF_LEN,
        salt=salt,
        iterations=KDF_ITER,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(data: bytes, password: str) -> bytes:
    """Encrypt *data* with *password*, returning a self-contained payload.

    Payload layout::

        MAGIC (4) + VERSION (1) + SALT (16) + NONCE (12) + CIPHERTEXT
    """
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    return b"".join([
        MAGIC,
        pack("!B", VERSION),
        salt,
        nonce,
        ciphertext,
    ])


def decrypt_bytes(payload: bytes, password: str) -> bytes:
    """Decrypt *payload* produced by :func:`encrypt_bytes` using *password*.

    Raises ``ValueError`` on corrupt / tampered payloads or wrong password.
    """
    if len(payload) < 4 + 1 + SALT_LEN + NONCE_LEN:
        raise ValueError("Payload too short to be valid")

    magic, = unpack("!4s", payload[0:4])
    if magic != MAGIC:
        raise ValueError("Invalid payload magic")

    version, = unpack("!B", payload[4:5])
    if version != VERSION:
        raise ValueError(f"Unsupported version: {version}")

    salt = payload[5:5 + SALT_LEN]
    nonce = payload[5 + SALT_LEN:5 + SALT_LEN + NONCE_LEN]
    ciphertext = payload[5 + SALT_LEN + NONCE_LEN:]

    key = derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)
