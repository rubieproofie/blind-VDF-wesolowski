"""
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

==============================================================================
Hybrid Blind Wesolowski VDF with Pietrzak PoE Blinding Correction
Proof-of-Concept Implementation

⚠️  IMPORTANT LIMITATIONS - NOT FOR PRODUCTION USE  ⚠️
==============================================================================

This implementation combines Wesolowski VDF with Pietrzak Proof-of-Exponentiation
for O(T/S) proof computation. See wesolowski_native.py for the simpler approach.

KNOWN ISSUES:
- Toy RSA modulus (small P·Q) - insecure, needs trusted setup
- Simple random oracle for ℓ selection
- No formal blinding security proof

Reference: 
- Wesolowski (2018): Efficient Verifiable Delay Functions
- Pietrzak (2018): Verifiable Delay Functions
==============================================================================
"""

import random
import hashlib
import math

# Toy parameters (change for larger experiments)
P = 10007          # prime
Q = 10009          # prime
N = P * Q          # modulus ≈ 10^8 (unknown order simulation)
T = 16             # delay parameter
S = 4              # Pietrzak space-time parameter → O(T/S) checkpoints
KAPPA = 20         # blinding randomness bits
A = 5              # public fixed non-square element (changed from 3 to ensure coprime with N)

def mod_inv(a: int, m: int) -> int:
    """Modular inverse using extended Euclidean algorithm."""
    if math.gcd(a, m) != 1:
        raise ValueError(f"Modular inverse does not exist: gcd({a}, {m}) = {math.gcd(a, m)}")
    # Extended Euclidean algorithm
    old_r, r = a, m
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    return old_s % m

def random_oracle(y: int, modulus: int) -> int:
    """Toy random oracle → prime ℓ (real use: proper prime sampling)."""
    h = hashlib.sha256(str(y).encode()).digest()
    candidate = int.from_bytes(h[:4], "big") % (1 << 10) + 3
    small_primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    for pr in small_primes:
        if candidate % pr != 0:
            return pr
    return 3

def client_blind(x: int, a: int, modulus: int, kappa: int):
    """Client blinds secret input x."""
    r = random.randint(0, (1 << kappa) - 1)
    alpha = (x * pow(a, r, modulus)) % modulus
    return alpha, r

def server_eval(alpha: int, t: int, s: int, modulus: int):
    """Server: full VDF evaluation + Pietrzak checkpoints on blinded input."""
    beta = pow(alpha, 1 << t, modulus)
    num_checkpoints = (t // s) + 1
    gamma = [0] * num_checkpoints
    current = alpha
    gamma[0] = current
    for k in range(1, num_checkpoints):
        for _ in range(s):
            current = pow(current, 2, modulus)
        gamma[k] = current
    return beta, gamma

def client_unblind(gamma: list, beta: int, r: int, s: int, t: int, modulus: int, a: int):
    """Client: unblind checkpoints + output in O(T/S) time."""
    num_checkpoints = len(gamma)
    delta = [0] * num_checkpoints

    # Precompute a^r mod modulus
    a_r = pow(a, r, modulus)
    a_r_inv = mod_inv(a_r, modulus)

    # Unblind first checkpoint
    delta[0] = (gamma[0] * a_r_inv) % modulus

    # Unblind remaining checkpoints
    for k in range(1, num_checkpoints):
        exp = r * (1 << (k * s))
        a_exp = pow(a, exp, modulus)
        a_exp_inv = mod_inv(a_exp, modulus)
        delta[k] = (gamma[k] * a_exp_inv) % modulus

    # Unblind final output y
    a_rt = pow(a, r * (1 << t), modulus)
    a_rt_inv = mod_inv(a_rt, modulus)
    y = (beta * a_rt_inv) % modulus

    # Verify ladder consistency (simulates Pietrzak PoE verification)
    consistent = True
    for k in range(num_checkpoints - 1):
        if pow(delta[k], 1 << s, modulus) != delta[k + 1]:
            consistent = False
            break

    return y, delta, consistent

def compute_wesolowski_pi(delta: list, t: int, s: int, y: int, modulus: int):
    """Client: compute succinct Wesolowski proof π from unblinded ladder (O(T/S) time)."""
    ell = random_oracle(y, modulus)
    q = (1 << t) // ell
    r_mod = (1 << t) % ell

    # Base-2^S windowed exponentiation on the ladder
    base_b = 1 << s
    pi = 1
    temp_q = q
    k = 0
    while temp_q > 0:
        digit = temp_q % base_b
        contrib = pow(delta[k], digit, modulus)
        pi = (pi * contrib) % modulus
        temp_q //= base_b
        k += 1

    return pi, ell, q, r_mod

def wesolowski_verify(y: int, pi: int, x: int, ell: int, r_mod: int, modulus: int) -> bool:
    """Public verification (standard Wesolowski)."""
    left = (pow(pi, ell, modulus) * pow(x, r_mod, modulus)) % modulus
    return left == y

def run_demo():
    """Run full end-to-end simulation (seeded for reproducibility)."""
    random.seed(42)
    x = random.randint(1, N - 1)

    print("=== Hybrid Blind Wesolowski VDF Demo ===")
    print(f"Modulus N: {N}")
    print(f"Client secret x: {x}\n")

    alpha, r = client_blind(x, A, N, KAPPA)
    print(f"Blinded input α sent to server: {alpha}")

    beta, gamma = server_eval(alpha, T, S, N)
    print(f"Server β: {beta}")
    print(f"Pietrzak checkpoints sent (O(T/S) = {len(gamma)} elements)")

    y, delta, consistent = client_unblind(gamma, beta, r, S, T, N, A)
    print(f"Unblinded y: {y}")
    print(f"Ladder consistent (Pietrzak verification): {consistent}")

    pi, ell, q, r_mod = compute_wesolowski_pi(delta, T, S, y, N)
    print(f"Wesolowski challenge ℓ: {ell}")
    print(f"Proof π: {pi}")

    honest_y = pow(x, 1 << T, N)
    verifies = wesolowski_verify(y, pi, x, ell, r_mod, N)

    print(f"Honest y: {honest_y}")
    print(f"y matches honest computation: {y == honest_y}")
    print(f"Public verification succeeds: {verifies}")

    if verifies and y == honest_y and consistent:
        print("\n✅ SUCCESS: Hybrid blind Wesolowski VDF works perfectly!")
    else:
        print("\n❌ FAILURE (this should never happen)")

if __name__ == "__main__":
    run_demo()