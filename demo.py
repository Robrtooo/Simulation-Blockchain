from core.Blockchain import Blockchain
from core.wallet import Wallet, USE_CRYPTOGRAPHY
from core.merkle import Merkle


def short(a: str) -> str:
    return a[:10] + "..."


if __name__ == "__main__":
    print("Sign backend:", "Ed25519" if USE_CRYPTOGRAPHY else "TOY (pas secure)")

    bc = Blockchain(difficulty=4, reward=25)

    alice = Wallet()
    bob = Wallet()
    miner = Wallet()

    print("\nAlice:", short(alice.address()))
    print("Bob  :", short(bob.address()))
    print("Miner:", short(miner.address()))

    print("\n--- Genesis ---")
    bc.create_and_add_genesis({
        alice.address(): 200,
        bob.address(): 150,
    })

    print("Balances:")
    print(" Alice:", bc.balance(alice.address()))
    print(" Bob  :", bc.balance(bob.address()))
    print(" Miner:", bc.balance(miner.address()))

    print("\n--- TX Alice -> Bob (60) ---")
    tx1 = bc.create_transaction(alice, bob.address(), 60)
    ok = bc.add_to_mempool(tx1)
    print("Mempool add:", ok)

    print("\n--- Mining ---")
    b1 = bc.mine_pending(miner.address())
    print("Block mined:", b1.height, b1.block_hash()[:16], "...")

    print("\nBalances:")
    print(" Alice:", bc.balance(alice.address()))
    print(" Bob  :", bc.balance(bob.address()))
    print(" Miner:", bc.balance(miner.address()))

    print("\n--- Merkle proof ---")
    txid = tx1.txid()
    proof = bc.tx_proof(1, txid)
    print("Proof exists:", proof is not None)
    if proof is not None:
        root = bc.chain[1].merkle_root
        print("Verify proof:", Merkle.verify_proof(txid, proof, root))

    print("\nChain valid:", bc.is_valid())

    print("\n--- Save / Load ---")
    bc.save("chain.json")
    bc2 = Blockchain(difficulty=4, reward=25)
    print("Load:", bc2.load("chain.json"))
    print("Chain2 valid:", bc2.is_valid())
