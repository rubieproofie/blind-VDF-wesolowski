"""
Wesolowski-Native Blind VDF (Idea 1 - Pure Wesolowski, Interactive)
Proof-of-Concept Implementation

Key insight: Uses public precomputed z = a^(2^T) for cheap y-unblinding.
- Client blinds with a^r
- Server computes full repeated squaring on blinded input
- Client uses public z^r for cheap y-unblinding (O(log T))
- Client sends challenge ell after unblinding y
- Server returns pi' under that ell
- Client corrects pi (O(T) work, but fully native Wesolowski)
"""

import random
import hashlib
from math import gcd

# Toy parameters
P = 10007
Q = 10009
N = P * Q
T = 16
KAPPA = 20
A = 3

def mod_inverse(a: int, m: int) -> int:
    """Extended Euclidean algorithm for modular inverse."""
    if gcd(a, m) != 1:
        raise ValueError("Modular inverse doesn't exist")
    # Extended Euclidean
    old_r, r = a, m
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    return old_s % m

def random_oracle(y: int, modulus: int) -> int:
    """Simple random oracle - outputs a small prime."""
    h = hashlib.sha256(str(y).encode()).digest()
    candidate = int.from_bytes(h[:4], "big") % (1 << 10) + 3
    small_primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    for pr in small_primes:
        if candidate % pr != 0:
            return pr
    return 3

def precompute_public_z(a: int, t: int, modulus: int) -> int:
    """One-time public value z = a^(2^T) (verifiable with its own Wesolowski proof)."""
    return pow(a, 1 << t, modulus)

def client_blind(x: int, a: int, modulus: int, kappa: int):
    r = random.randint(0, (1 << kappa) - 1)
    alpha = (x * pow(a, r, modulus)) % modulus
    return alpha, r

def server_eval(alpha: int, t: int, modulus: int):
    """Full VDF computation: beta = alpha^(2^t)"""
    beta = pow(alpha, 1 << t, modulus)
    return beta

def client_unblind_y(beta: int, r: int, public_z: int, modulus: int):
    """Cheap unblinding of y using public z^r.
    
    y = beta / (a^r)^(2^T) = beta / (a^(2^T))^r = beta / z^r
    """
    c = pow(public_z, r, modulus)
    c_inv = mod_inverse(c, modulus)
    y = (beta * c_inv) % modulus
    return y

def client_get_challenge(y: int, modulus: int):
    """Client chooses challenge ell after seeing y."""
    return random_oracle(y, modulus)

def server_proof(alpha: int, ell: int, t: int, modulus: int):
    """Server computes Wesolowski proof on blinded input."""
    q = (1 << t) // ell
    r_mod = (1 << t) % ell
    pi_prime = pow(alpha, q, modulus)
    return pi_prime, q, r_mod

def client_correct_proof(pi_prime: int, r: int, q: int, modulus: int, a: int):
    """O(T) correction: pi = pi' / a^(r*q)
    
    pi' = (x*a^r)^q = x^q * a^(r*q)
    We want pi = x^q = pi' / a^(r*q)
    """
    d = pow(a, r * q, modulus)
    d_inv = mod_inverse(d, modulus)
    pi = (pi_prime * d_inv) % modulus
    return pi

def wesolowski_verify(y: int, pi: int, x: int, ell: int, r_mod: int, modulus: int) -> bool:
    """Verify pi^ell * x^r_mod == y"""
    left = (pow(pi, ell, modulus) * pow(x, r_mod, modulus)) % modulus
    return left == y

def run_native_demo():
    random.seed(42)
    x = random.randint(1, N - 1)
    print("=== Wesolowski-Native Blind VDF Demo (Idea 1) ===")
    print(f"Modulus N: {N}")
    print(f"Client secret x: {x}\n")
    
    # One-time public value
    public_z = precompute_public_z(A, T, N)
    print(f"Public z = a^{{2^{T}}}: {public_z} (precomputed & verifiable)\n")
    
    # Client blinds
    alpha, r = client_blind(x, A, N, KAPPA)
    print(f"Blinded alpha -> server: {alpha}")
    
    # Server computes full VDF
    beta = server_eval(alpha, T, N)
    print(f"Server beta = alpha^(2^T): {beta}")
    
    # Client unblinds y (cheap using public z)
    y = client_unblind_y(beta, r, public_z, N)
    print(f"Unblinded y (cheap): {y}")
    
    # Client sends challenge
    ell = client_get_challenge(y, N)
    print(f"Client challenge ell -> server: {ell}")
    
    # Server computes proof under challenge
    pi_prime, q, r_mod = server_proof(alpha, ell, T, N)
    print(f"Server pi': {pi_prime}")
    
    # Client corrects proof
    pi = client_correct_proof(pi_prime, r, q, N, A)
    print(f"Corrected proof pi: {pi}")
    
    # Verify
    honest_y = pow(x, 1 << T, N)
    verifies = wesolowski_verify(y, pi, x, ell, r_mod, N)
    
    print(f"\nHonest y: {honest_y}")
    print(f"y matches honest: {y == honest_y}")
    print(f"Public verification succeeds: {verifies}")
    
    if verifies and y == honest_y:
        print("\nSUCCESS: Wesolowski-native blind VDF works!")
    else:
        print("\nFAILURE")

if __name__ == "__main__":
    run_native_demo()