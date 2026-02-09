from dataclasses import dataclass
from typing import Dict, List, Any
from core.utils import canon_json, sha256_hex


COINBASE = "COINBASE"


@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: int
    nonce: int
    timestamp: float
    pubkey_b64: str = ""
    sig_b64: str = ""

    def message_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "pubkey_b64": self.pubkey_b64,
        }

    def message_bytes(self) -> bytes:
        return canon_json(self.message_dict()).encode("utf-8")

    def txid(self) -> str:
        payload = {
            **self.message_dict(),
            "sig_b64": self.sig_b64,
        }
        return sha256_hex(canon_json(payload).encode("utf-8"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "pubkey_b64": self.pubkey_b64,
            "sig_b64": self.sig_b64,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Transaction":
        return Transaction(**d)


@dataclass
class Block:
    height: int
    prev_hash: str
    timestamp: float
    nonce: int
    difficulty: int
    merkle_root: str
    transactions: List[Transaction]

    def header_dict(self) -> Dict[str, Any]:
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root,
        }

    def block_hash(self) -> str:
        return sha256_hex(canon_json(self.header_dict()).encode("utf-8"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "height": self.height,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Block":
        txs = [Transaction.from_dict(x) for x in d["transactions"]]
        return Block(
            height=d["height"],
            prev_hash=d["prev_hash"],
            timestamp=d["timestamp"],
            nonce=d["nonce"],
            difficulty=d["difficulty"],
            merkle_root=d["merkle_root"],
            transactions=txs,
        )
