"""
samples/sealed_eval/merkle_tree.py

Domain: Cryptography & Blockchain
Builds cryptographic Merkle Trees and verifies inclusion proofs.
"""

import hashlib
from typing import List, Dict, Optional


def hash_data(data: str) -> str:
    """Computes SHA-256 hash digest of a UTF-8 string."""
    if not isinstance(data, str):
        raise TypeError("Input data must be a string.")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_pair(left: str, right: str) -> str:
    """Combines and hashes two child nodes deterministically."""
    combined = left + right
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def build_merkle_root(leaves: List[str]) -> str:
    """
    Computes root hash of a Merkle tree from an ordered list of leaf items.
    If number of leaves is odd at any layer, the last leaf is duplicated.
    """
    if not leaves:
        return ""

    current_layer = [hash_data(leaf) for leaf in leaves]

    while len(current_layer) > 1:
        next_layer: List[str] = []
        if len(current_layer) % 2 != 0:
            current_layer.append(current_layer[-1])

        for i in range(0, len(current_layer), 2):
            next_layer.append(hash_pair(current_layer[i], current_layer[i + 1]))

        current_layer = next_layer

    return current_layer[0]


def generate_merkle_proof(leaves: List[str], target_index: int) -> List[Dict[str, str]]:
    """
    Generates an audit path proof of siblings for verifying inclusion of leaf at target_index.
    """
    if not leaves or target_index < 0 or target_index >= len(leaves):
        return []

    proof: List[Dict[str, str]] = []
    current_layer = [hash_data(leaf) for leaf in leaves]
    idx = target_index

    while len(current_layer) > 1:
        if len(current_layer) % 2 != 0:
            current_layer.append(current_layer[-1])

        if idx % 2 == 0:
            sibling_idx = idx + 1
            proof.append({"position": "right", "hash": current_layer[sibling_idx]})
        else:
            sibling_idx = idx - 1
            proof.append({"position": "left", "hash": current_layer[sibling_idx]})

        next_layer: List[str] = []
        for i in range(0, len(current_layer), 2):
            next_layer.append(hash_pair(current_layer[i], current_layer[i + 1]))

        current_layer = next_layer
        idx = idx // 2

    return proof


def verify_merkle_proof(leaf: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
    """Verifies that leaf is a member of the Merkle tree with expected_root."""
    if not leaf or not expected_root:
        return False

    current_hash = hash_data(leaf)

    for item in proof:
        sibling = item.get("hash", "")
        pos = item.get("position", "")

        if pos == "left":
            current_hash = hash_pair(sibling, current_hash)
        elif pos == "right":
            current_hash = hash_pair(current_hash, sibling)
        else:
            return False

    return current_hash == expected_root
