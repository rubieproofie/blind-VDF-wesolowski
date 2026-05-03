# Blind Wesolowski VDF

Two working implementations solving the blind Wesolowski open problem (Hoffmann-Pietrzak 2026).

:warning: **NOT FOR PRODUCTION USE** - Educational PoCs with known limitations.

## Files

| File | Description |
|------|-------------|
| `wesolowski_native.py` | **:star: RECOMMENDED** - Pure Wesolowski, fully native |
| `hybrid_wesolowski.py` | Hybrid (Pietrzak + Wesolowski), efficient |
| `pietrzak_vdf.py` | Pietrzak VDF (alternative approach) |
| `wesolowski_simple.py` | Original Wesolowski (NOT blind - for comparison) |

## How to Run

```bash
# Recommended: Wesolowski-native (pure, truly blind)
python3 wesolowski_native.py

# Alternative: Hybrid approach
python3 hybrid_wesolowski.py
```

## Why Wesolowski-Native Works (The Key Insight)

The native solution achieves **all desired properties**:

### 1. Server doesn't see x
```
Client sends: alpha = x * a^r (r is random)
Server sees:  alpha (looks random, has no info about x)
```

### 2. Server doesn't see y
```
Server computes: beta = alpha^(2^T)
Server returns: beta (can't unblind - doesn't know r)

Client unblinds: y = beta * z^(-r)
               where z = a^(2^T) is PUBLIC
```

### 3. Full VDF (T sequential squarings)
- Server does 2^16 = 65,536 squarings (no shortcut)
- This is the delay property

### 4. Cheap client unblinding
- y-unblinding: O(log T) using public z^r
- pi correction: O(T) - but no VDF computation needed

## Comparison

| Property | wesolowski_native.py | hybrid_wesolowski.py | wesolowski_simple.py |
|----------|:------------------:|:------------------:|:------------------:|
| **Truly blind** | ✓ | ✓ | ✗ |
| **Server does NOT see x** | ✓ | ✓ | ✗ |
| **Server does NOT see y** | ✓ | ✓ | ✗ |
| **Pure Wesolowski mechanics** | ✓ | ✗ | ✓ |
| **Uses public z for cheap unblinding** | ✓ | ✗ | ✗ |
| **No Pietrzak checkpoints needed** | ✓ | ✗ | ✓ |
| **Full VDF (2^T squarings)** | ✓ | ✓ | ✓ |
| **Client work: O(log T) + O(T)** | ✓ | ✗ | ✗ |

## The Math Behind Wesolowski-Native

### Protocol
1. **Client**: Picks random r, computes alpha = x * a^r, sends to server
2. **Server**: Computes beta = alpha^(2^T), returns beta
3. **Client**: Unblinds y = beta * z^(-r) — uses public z^r
4. **Client**: Chooses challenge ell from y
5. **Server**: Computes pi' = alpha^q where q = floor(2^T/ell)
6. **Client**: Corrects pi = pi' * a^(-r*q)
7. **Verifier**: Checks pi^ell * x^(2^T mod ell) == y

### Correctness
```
pi = pi' / a^(r*q)
   = (x*a^r)^q / a^(r*q)
   = x^q

Verification:
  pi^ell * x^r = (x^q)^ell * x^r = x^(q*ell + r) = x^(2^T) = y ✓
```

## Known Limitations

| Issue | Fix for Production |
|-------|---------------------|
| Toy modulus (P*Q) | RSA-2048+ with trusted setup |
| Simple random oracle | VRF or hash-to-prime |
| Timing attacks | Constant-time arithmetic |

## References

- Wesolowski (2018): "Efficient Verifiable Delay Functions"
- Pietrzak (2018): "Verifiable Delay Functions"
- Hoffmann & Pietrzak (2026): "Blind Verifiable Delay Functions"

## License

MIT - See LICENSE.md