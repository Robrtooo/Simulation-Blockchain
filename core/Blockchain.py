import json
import time
from typing import Dict, List, Optional, Tuple

from core.merkle import Merkle
from core.models import Block, Transaction, COINBASE
from core.utils import b64d, b64e
from core.wallet import Wallet


class Blockchain:
    def __init__(self, difficulty: int = 4, reward: int = 25):
        self.difficulty = difficulty
        self.reward = reward

        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []

        self.balances: Dict[str, int] = {}
        self.next_nonce: Dict[str, int] = {}

    # ----------------- state helpers -----------------

    def balance(self, addr: str) -> int:
        return self.balances.get(addr, 0)

    def expected_nonce(self, addr: str) -> int:
        return self.next_nonce.get(addr, 0)

    def expected_nonce_with_mempool(self, addr: str) -> int:
        n = self.expected_nonce(addr)
        pending_nonces = {tx.nonce for tx in self.mempool if tx.sender == addr}
        while n in pending_nonces:
            n += 1
        return n

    def _pow_ok(self, h: str, difficulty: int) -> bool:
        return h.startswith("0" * difficulty)

    def _apply_tx(self, tx: Transaction, balances: Dict[str, int], nonces: Dict[str, int]) -> bool:
        if tx.amount <= 0:
            return False

        if tx.sender == COINBASE:
            balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
            return True

        exp = nonces.get(tx.sender, 0)
        if tx.nonce != exp:
            return False

        sender_bal = balances.get(tx.sender, 0)
        if sender_bal < tx.amount:
            return False

        balances[tx.sender] = sender_bal - tx.amount
        balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
        nonces[tx.sender] = exp + 1
        return True

    # ----------------- tx signing / verify -----------------

    def create_transaction(self, wallet: Wallet, recipient: str, amount: int) -> Transaction:
        sender = wallet.address()
        nonce = self.expected_nonce_with_mempool(sender)

        tx = Transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
            nonce=nonce,
            timestamp=time.time(),
            pubkey_b64=b64e(wallet.pubkey_bytes()),
            sig_b64="",
        )
        sig = wallet.sign(tx.message_bytes())
        tx.sig_b64 = b64e(sig)
        return tx

    def verify_transaction(self, tx: Transaction) -> bool:
        if tx.amount <= 0:
            return False

        if tx.sender == COINBASE:
            return True 

        if not tx.pubkey_b64 or not tx.sig_b64:
            return False

        try:
            pub = b64d(tx.pubkey_b64)
            sig = b64d(tx.sig_b64)
        except Exception:
            return False

        if Wallet is None:
            return False

        if Wallet.verify is None:
            return False

        from core.utils import sha256_hex

        if sha256_hex(pub) != tx.sender:
            return False

        return Wallet.verify(pub, tx.message_bytes(), sig)

    def add_to_mempool(self, tx: Transaction) -> bool:
        if not self.verify_transaction(tx):
            return False

        if any(p.txid() == tx.txid() for p in self.mempool):
            return False

        tmp_bal = dict(self.balances)
        tmp_nonce = dict(self.next_nonce)

        if tx.sender == COINBASE:
            return False

        for p in self.mempool:
            if not self._apply_tx(p, tmp_bal, tmp_nonce):
                return False
        if not self._apply_tx(tx, tmp_bal, tmp_nonce):
            return False

        self.mempool.append(tx)
        return True

    # ----------------- blocks / mining -----------------

    def _make_block(self, txs: List[Transaction], miner_addr: str) -> Block:
        height = len(self.chain)
        prev_hash = self.chain[-1].block_hash() if self.chain else "0" * 64
        ts = time.time()

        if height > 0:
            coinbase = Transaction(
                sender=COINBASE,
                recipient=miner_addr,
                amount=self.reward,
                nonce=0,
                timestamp=ts,
            )
            txs = [coinbase] + txs

        merkle_root = Merkle.root([t.txid() for t in txs])
        return Block(
            height=height,
            prev_hash=prev_hash,
            timestamp=ts,
            nonce=0,
            difficulty=self.difficulty,
            merkle_root=merkle_root,
            transactions=txs,
        )

    def mine_pending(self, miner_addr: str, max_txs: int = 100) -> Optional[Block]:
        txs = self.mempool[:max_txs]
        block = self._make_block(txs, miner_addr)

        nonce = 0
        while True:
            block.nonce = nonce
            h = block.block_hash()
            if self._pow_ok(h, block.difficulty):
                break
            nonce += 1

        if not self.add_block(block):
            return None

        mined = set(t.txid() for t in txs)
        self.mempool = [t for t in self.mempool if t.txid() not in mined]
        return block

    def verify_block(self, block: Block) -> bool:
        if block.height != len(self.chain):
            return False

        expected_prev = self.chain[-1].block_hash() if self.chain else "0" * 64
        if block.prev_hash != expected_prev:
            return False

        calc_root = Merkle.root([t.txid() for t in block.transactions])
        if calc_root != block.merkle_root:
            return False

        if not self._pow_ok(block.block_hash(), block.difficulty):
            return False

        if block.height == 0:
            if any(tx.sender != COINBASE for tx in block.transactions):
                return False
        else:
            if len(block.transactions) == 0:
                return False
            if block.transactions[0].sender != COINBASE:
                return False
            if block.transactions[0].amount != self.reward:
                return False
            if any(tx.sender == COINBASE for tx in block.transactions[1:]):
                return False

        for tx in block.transactions:
            if not self.verify_transaction(tx):
                return False

        tmp_bal = dict(self.balances)
        tmp_nonce = dict(self.next_nonce)

        for tx in block.transactions:
            if not self._apply_tx(tx, tmp_bal, tmp_nonce):
                return False

        return True

    def add_block(self, block: Block) -> bool:
        if not self.verify_block(block):
            return False

        for tx in block.transactions:
            ok = self._apply_tx(tx, self.balances, self.next_nonce)
            if not ok:
                return False

        self.chain.append(block)
        return True


    def is_valid(self) -> bool:
        tmp_bal: Dict[str, int] = {}
        tmp_nonce: Dict[str, int] = {}

        for i, block in enumerate(self.chain):
            prev = self.chain[i - 1].block_hash() if i > 0 else "0" * 64
            if block.prev_hash != prev:
                return False

            if not self._pow_ok(block.block_hash(), block.difficulty):
                return False

            if Merkle.root([t.txid() for t in block.transactions]) != block.merkle_root:
                return False

            if i == 0:
                if any(tx.sender != COINBASE for tx in block.transactions):
                    return False
            else:
                if len(block.transactions) == 0:
                    return False
                if block.transactions[0].sender != COINBASE:
                    return False
                if block.transactions[0].amount != self.reward:
                    return False
                if any(tx.sender == COINBASE for tx in block.transactions[1:]):
                    return False

            # tx signatures + state replay
            for tx in block.transactions:
                if not self.verify_transaction(tx):
                    return False
                if not self._apply_tx(tx, tmp_bal, tmp_nonce):
                    return False

        return True


    def tx_proof(self, block_height: int, txid: str) -> Optional[List[Tuple[str, str]]]:
        if block_height < 0 or block_height >= len(self.chain):
            return None
        block = self.chain[block_height]
        hashes = [t.txid() for t in block.transactions]
        return Merkle.proof(hashes, txid)

    def save(self, path: str = "chain.json") -> None:
        data = [b.to_dict() for b in self.chain]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str = "chain.json") -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            return False

        chain = [Block.from_dict(b) for b in raw]

        tmp_bal: Dict[str, int] = {}
        tmp_nonce: Dict[str, int] = {}

        for i, block in enumerate(chain):
            prev = chain[i - 1].block_hash() if i > 0 else "0" * 64
            if block.prev_hash != prev:
                return False
            if not self._pow_ok(block.block_hash(), block.difficulty):
                return False
            if Merkle.root([t.txid() for t in block.transactions]) != block.merkle_root:
                return False
            for tx in block.transactions:
                if not self.verify_transaction(tx):
                    return False
                if not self._apply_tx(tx, tmp_bal, tmp_nonce):
                    return False

        self.chain = chain
        self.mempool = []
        self.balances = tmp_bal
        self.next_nonce = tmp_nonce
        return True


    def create_and_add_genesis(self, allocations: Dict[str, int]) -> Block:
        txs = []
        now = time.time()
        for addr, amt in allocations.items():
            txs.append(Transaction(sender=COINBASE, recipient=addr, amount=int(amt), nonce=0, timestamp=now))

        block = Block(
            height=0,
            prev_hash="0" * 64,
            timestamp=now,
            nonce=0,
            difficulty=self.difficulty,
            merkle_root=Merkle.root([t.txid() for t in txs]),
            transactions=txs,
        )

        nonce = 0
        while True:
            block.nonce = nonce
            if self._pow_ok(block.block_hash(), block.difficulty):
                break
            nonce += 1

        ok = self.add_block(block)
        if not ok:
            raise RuntimeError("Genesis invalide (bizarre).")
        return block
