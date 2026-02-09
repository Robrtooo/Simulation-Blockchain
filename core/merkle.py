from typing import List, Optional, Tuple
from core.utils import sha256_hex


class Merkle:
    @staticmethod
    def _hash_pair(a: str, b: str) -> str:
        return sha256_hex((a + b).encode("utf-8"))

    @staticmethod
    def root(hashes: List[str]) -> str:
        if not hashes:
            return sha256_hex(b"")

        level = hashes[:]
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1]) 

            nxt = []
            for i in range(0, len(level), 2):
                nxt.append(Merkle._hash_pair(level[i], level[i + 1]))
            level = nxt
        return level[0]

    @staticmethod
    def proof(hashes: List[str], target: str) -> Optional[List[Tuple[str, str]]]:
        """
        Preuve d'inclusion : liste de (sibling_hash, 'L'/'R')
        L = sibling à gauche, R = sibling à droite
        """
        if target not in hashes:
            return None

        idx = hashes.index(target)
        level = hashes[:]
        path: List[Tuple[str, str]] = []

        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])

            sib_idx = idx ^ 1
            side = "L" if sib_idx < idx else "R"
            path.append((level[sib_idx], side))

            nxt = []
            for i in range(0, len(level), 2):
                nxt.append(Merkle._hash_pair(level[i], level[i + 1]))

            level = nxt
            idx //= 2

        return path

    @staticmethod
    def verify_proof(target: str, proof_path: List[Tuple[str, str]], root: str) -> bool:
        cur = target
        for sibling, side in proof_path:
            if side == "L":
                cur = Merkle._hash_pair(sibling, cur)
            else:
                cur = Merkle._hash_pair(cur, sibling)
        return cur == root
