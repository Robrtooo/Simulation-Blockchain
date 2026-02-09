import os
from core.utils import sha256_hex

USE_CRYPTOGRAPHY = False

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    USE_CRYPTOGRAPHY = True
except Exception:
    USE_CRYPTOGRAPHY = False


class Wallet:
    """
    Wallet simple :
    - address = sha256(pubkey)
    - signe des messages (transactions)
    """

    def __init__(self):
        if USE_CRYPTOGRAPHY:
            self._sk = Ed25519PrivateKey.generate()
            self._pk = self._sk.public_key()
        else:
            self._sk = os.urandom(32)
            self._pk = self._sk

    def pubkey_bytes(self) -> bytes:
        if USE_CRYPTOGRAPHY:
            return self._pk.public_bytes(Encoding.Raw, PublicFormat.Raw)
        return self._pk

    def address(self) -> str:
        return sha256_hex(self.pubkey_bytes())

    def sign(self, message: bytes) -> bytes:
        if USE_CRYPTOGRAPHY:
            return self._sk.sign(message)
        # toy signature : sha256(secret + message)
        import hashlib

        return hashlib.sha256(self._sk + message).digest()

    @staticmethod
    def verify(pubkey_bytes: bytes, message: bytes, signature: bytes) -> bool:
        if USE_CRYPTOGRAPHY:
            try:
                pk = Ed25519PublicKey.from_public_bytes(pubkey_bytes)
                pk.verify(signature, message)
                return True
            except Exception:
                return False

        import hashlib

        return hashlib.sha256(pubkey_bytes + message).digest() == signature
