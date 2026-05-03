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
Wesoloswki-Native Blind VDF
Proof-of-Concept Implementation

⚠️  IMPORTANT LIMITATIONS - NOT FOR PRODUCTION USE  ⚠️
==============================================================================

This is an EDUCATIONAL proof-of-concept demonstrating the Wesolowski VDF 
construction. It has several known limitations:

1. TOY MODULUS: Uses small RSA modulus N = P·Q with small primes (10k range).
   - Insecure: can be factored trivially
   - Production needs: proper RSA-2048 or class groups with trusted setup
   
2. RANDOM ORACLE: Simple hash-based ℓ selection, not cryptographically secure.
   - Production needs: VRF or hash-to-prime with proper proofs
   
3. BLINDING ANALYSIS: No formal proof that server learns nothing about x.
   - Relies on hardness of RSA/DLP in unknown-order group
   - Would need formal security reduction in paper

4. TIMING ATTACKS: Implementation uses constant-time ops in concept but
   - Production needs: constant-time arithmetic

Reference: Wesolowski, "Efficient Verifiable Delay Functions" (2018)
==============================================================================
"""

import random
import hashlib
import math

# Toy parameters (change for larger experiments)
P = 10007          # prime
Q = 10009          # prime  
N = P * Q          # modulus ≈ 10^8 (RSA unknown-order simulation)
T = 16             # delay parameter (2^T iterations)
KAPPA = 20         # blinding randomness bits
A = 5              # public fixed non-square (ensures coprime with N)

def mod_inv(a: int, m: int) -> int:
    """Modular inverse using extended Euclidean algorithm."""
    if math.gcd(a, m) != 1:
        raise ValueError(f"Modular inverse does not exist: gcd({a}, {m}) = {math.gcd(a, m)}")
    old_r, r = a, m
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    return old_s % m

def random_oracle(y: int, t: int) -> int:
    """
    Random oracle H(y) -> prime ℓ
    
    CRITICAL REQUIREMENTS:
    1. ℓ must be prime
    2. ℓ must NOT divide 2^t (otherwise r=0 breaks verification)
    3. ℓ should be pseudorandom based on y
    
    Uses rejection sampling to find valid ℓ.
    """
    two_t = 1 << t
    
    # Hash y to get a seed for pseudorandom selection
    h = hashlib.sha256(str(y).encode()).digest()
    base = int.from_bytes(h[:4], 'big')
    
    # Try candidates starting from hash-derived base
    attempt = 0
    candidates_tried = set()
    
    while attempt < 1000:
        # Generate candidate from hash
        candidate = ((base + attempt) % 997) + 7  # Start from small primes
        if candidate in candidates_tried:
            attempt += 1
            continue
        candidates_tried.add(candidate)
        
        # Check if prime (simple trial division)
        is_prime = True
        for p in range(2, min(candidate, 100)):
            if candidate % p == 0:
                is_prime = False
                break
        
        if is_prime and two_t % candidate != 0:
            return candidate
        
        attempt += 1
    
    # Fallback: return a known good prime
    return 7  # 7 doesn't divide any 2^t for t >= 3

def client_blind(x: int, a: int, modulus: int, kappa: int):
    """
    Client: blind secret input x.
    Returns: (blinded alpha, blinding factor r)
    """
    r = random.randint(0, (1 << kappa) - 1)
    alpha = (x * pow(a, r, modulus)) % modulus
    return alpha, r

def server_eval(alpha: int, t: int, modulus: int):
    """
    Server: compute VDF on blinded input.
    Returns: y = alpha^(2^t)
    
    This is the expensive delay function - intentionally sequential.
    """
    y = pow(alpha, 1 << t, modulus)
    return y

def client_unblind(y_blinded: int, r: int, t: int, modulus: int, a: int):
    """
    Client: unblind the VDF output.
    Compute: y = y_blinded * (a^r)^(-2^t) mod N
    
    No checkpoints needed - this is the Wesolowski advantage!
    """
    a_rt = pow(a, r * (1 << t), modulus)
    a_rt_inv = mod_inv(a_rt, modulus)
    y = (y_blinded * a_rt_inv) % modulus
    return y

def compute_wesolowski_proof(x: int, t: int, ell: int, modulus: int):
    """
    Client: compute Wesolowski proof π = x^q where q = floor(2^t / ℓ)
    
    The mathematical identity:
    - Let 2^t = q·ℓ + r where 0 ≤ r < ℓ
    - Then: x^(2^t) = (x^q)^ℓ · x^r
    - So π = x^q satisfies π^ℓ · x^r = y (the verification equation)
    
    This uses the UNBLINDED secret x directly.
    """
    two_t = 1 << t
    q = two_t // ell  # Integer division
    r_mod = two_t % ell  # Remainder
    pi = pow(x, q, modulus)
    return pi, q, r_mod

def wesolowski_verify(y: int, pi: int, x: int, ell: int, t: int, modulus: int) -> bool:
    """
    Public verification: check π^ℓ · x^r == y
    where r = 2^T mod ℓ
    
    This is the succinct verification equation from Wesolowski (2018).
    """
    two_t = 1 << t
    r_mod = two_t % ell
    left = (pow(pi, ell, modulus) * pow(x, r_mod, modulus)) % modulus
    right = y % modulus
    return left == right

def run_demo():
    """End-to-end demonstration."""
    random.seed(42)
    
    # Secret client input
    x = random.randint(1, N - 1)
    
    print("=" * 50)
    print("Wesoloswki-Native Blind VDF Demo")
    print("=" * 50)
    print(f"Modulus N: {N}")
    print(f"Delay T: {T} (2^{T} = {1 << T} iterations)")
    print(f"Client secret x: {x}\n")
    
    # Step 1: Client blinds input
    alpha, r = client_blind(x, A, N, KAPPA)
    print(f"[1] Client blinds: α = x·a^r = {alpha}")
    print(f"    Blinding factor r: {r}")
    
    # Step 2: Server evaluates VDF
    y_blinded = server_eval(alpha, T, N)
    print(f"\n[2] Server evaluates: β = α^(2^{T}) = {y_blinded}")
    
    # Step 3: Client unblinds output
    y = client_unblind(y_blinded, r, T, N, A)
    print(f"\n[3] Client unblinds: y = β·(a^r)^(-2^{T}) mod N = {y}")
    
    # Step 4: Compute proof (Wesoloswki-specific)
    ell = random_oracle(y, T)
    print(f"\n[4] Random oracle: ℓ = H(y) = {ell}")
    print(f"    2^{T} = q·ℓ + r where q = 2^{T} // ℓ, r = 2^{T} % ℓ")
    
    pi, q, r_mod = compute_wesolowski_proof(x, T, ell, N)
    print(f"    Proof π = x^q = x^{q}")
    
    # Step 5: Verification
    verifies = wesolowski_verify(y, pi, x, ell, T, N)
    print(f"\n[5] Verification: π^{ell} · x^(2^{T} mod {ell}) == y")
    print(f"    Result: {'✓ PASS' if verifies else '✗ FAIL'}")
    
    # Comparison with honest computation
    honest_y = pow(x, 1 << T, N)
    print(f"\n[Bonus] Honest y = x^(2^{T}) = {honest_y}")
    print(f"        Match: {y == honest_y}")
    
    if verifies and y == honest_y:
        print("\n" + "=" * 50)
        print("✅ SUCCESS: Wesolowski-native VDF works!")
        print("=" * 50)
    else:
        print("\n❌ FAILURE")

if __name__ == "__main__":
    run_demo()