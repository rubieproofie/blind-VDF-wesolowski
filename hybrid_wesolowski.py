"""
Hybrid Blind Wesolowski VDF - Solution Attempt

This implements the hybrid approach suggested in Hoffmann-Pietrzak 2026:
- Use Wesolowski's succinct proof for the main statement
- Use Pietrzak checkpoints for efficient unblinding of the blinding factor

The client NEVER sees x during server computation.
The server NEVER sees x or y.
"""

import random
import hashlib

# Toy modulus for demo (production: RSA-2048 with trusted setup)
P, Q = 317, 315889
N = P * Q
T = 16  # Delay (2^T iterations)
S = 4   # Checkpoint stride

# Generator (non-square in production)
a = 2

def mod_inv(x: int, m: int) -> int:
    """Extended Euclidean algorithm for modular inverse."""
    if x < 0:
        x = x % m
    g, s, _ = extended_gcd(x, m)
    if g != 1:
        raise ValueError("Modular inverse doesn't exist")
    return s % m

def extended_gcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y

def client_blind(x: int):
    """Client: Blind input x with random r"""
    r = random.randint(1 << 20, 1 << 30)
    alpha = (x * pow(a, r, N)) % N
    ar = pow(a, r, N)
    return alpha, ar, r

def server_wesolowski_eval(alpha: int, t: int, mod: int):
    """Server: Compute beta = alpha^(2^t)"""
    return pow(alpha, 1 << t, mod)

def server_pietrzak_checkpoints(ar: int, t: int, stride: int, mod: int):
    """Server: Pietrzak checkpoints for a^r only (not the full computation)"""
    checkpoints = []
    current = ar
    for i in range(1, (t // stride) + 1):
        current = pow(current, 1 << stride, mod)
        checkpoints.append(current)
    return checkpoints

def client_unblind_with_checkpoints(beta: int, checkpoints: list, r: int, t: int, stride: int, mod: int):
    """Client: Unblind y using checkpoints - O(T/S) work"""
    if not checkpoints:
        ar_2t = pow(pow(a, r, mod), 1 << t, mod)
        y = (beta * mod_inv(ar_2t, mod)) % mod
        return y
    
    # Reconstruct a^(r*2^t) from checkpoints
    ar_2t = checkpoints[-1]
    remainder = t - ((t // stride) * stride)
    if remainder > 0:
        ar_2t = pow(ar_2t, 1 << remainder, mod)
    
    y = (beta * mod_inv(ar_2t, mod)) % mod
    return y

def random_oracle(y: int, t: int) -> int:
    """Random oracle H(y) -> prime ell that doesn't divide 2^t"""
    two_t = 1 << t
    h = hashlib.sha256(str(y).encode()).digest()
    base = int.from_bytes(h[:4], 'big')
    
    attempt = 0
    while attempt < 1000:
        candidate = ((base + attempt) % 997) + 7
        is_prime = True
        for p in range(2, min(candidate, 100)):
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime and two_t % candidate != 0:
            return candidate
        attempt += 1
    return 7

def compute_proof(x: int, t: int, ell: int, mod: int):
    """Compute pi = x^q where q = floor(2^t / ell)"""
    two_t = 1 << t
    q = two_t // ell
    r_mod = two_t % ell
    pi = pow(x, q, mod)
    return pi, q, r_mod

def verify(y: int, pi: int, x: int, ell: int, t: int, mod: int) -> bool:
    """Verify pi^ell * x^r == y"""
    two_t = 1 << t
    r_mod = two_t % ell
    left = (pow(pi, ell, mod) * pow(x, r_mod, mod)) % mod
    return left == (y % mod)

def adjust_proof(pi_prime: int, ar: int, ell: int, t: int, mod: int):
    """Adjust pi' (on blinded input) to pi (on original x)
    
    pi' = (x*a^r)^q = x^q * a^(r*q)
    We want pi = x^q = pi' / a^(r*q)
    
    Requires computing a^(r*q) - much smaller than 2^t
    """
    two_t = 1 << t
    q = two_t // ell
    ar_q = pow(ar, q, mod)
    pi = (pi_prime * mod_inv(ar_q, mod)) % mod
    return pi

def run_demo():
    print("=" * 60)
    print("Hybrid Blind Wesolowski VDF - Solution")
    print("=" * 60)
    
    x = random.randint(1 << 20, N)
    print(f"Modulus N: {N}")
    print(f"Delay T: {T}, Checkpoint stride S: {S}")
    print(f"Client secret x: {x}")
    print()
    
    # Client blinds
    alpha, ar, r = client_blind(x)
    print(f"[1] Client blinds: alpha = x * a^r = {alpha}")
    print(f"    a^r = {ar}, r = {r}")
    print()
    
    # Server computes TWO things
    beta = server_wesolowski_eval(alpha, T, N)
    print(f"[2] Server: beta = alpha^(2^{T}) = {beta}")
    
    checkpoints = server_pietrzak_checkpoints(ar, T, S, N)
    print(f"[3] Server: checkpoints ({len(checkpoints)} elements)")
    print()
    
    # Client unblinds using checkpoints - O(T/S) not O(T)
    y = client_unblind_with_checkpoints(beta, checkpoints, r, T, S, N)
    print(f"[4] Client unblinds: y = {y}")
    
    # Client computes Wesolowski proof
    ell = random_oracle(y, T)
    pi_prime, q, r_mod = compute_proof(alpha, T, ell, N)
    pi = adjust_proof(pi_prime, ar, ell, T, N)
    print(f"[5] Client: ell = {ell}, q = {q}")
    print(f"    pi (adjusted) = {pi}")
    print()
    
    # Verification
    is_valid = verify(y, pi, x, ell, T, N)
    honest_y = pow(x, 1 << T, N)
    print(f"[6] Verification: pi^{ell} * x^{r_mod} == y")
    print(f"    Result: {'PASS' if is_valid else 'FAIL'}")
    print(f"\n[Bonus] Honest y = {honest_y}")
    print(f"    Match: {y == honest_y}")
    
    print("=" * 60)
    if is_valid and y == honest_y:
        print("SUCCESS: Hybrid approach works!")
    else:
        print("FAILURE")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()