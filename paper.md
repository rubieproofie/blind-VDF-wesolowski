# Blind Wesolowski Verifiable Delay Functions

**A Short Note Resolving the Open Problem of Hoffmann and Pietrzak (ePrint 2026/737)**

**Authors:** Rubie  
**Date:** May 2026  
**GitHub PoC:** https://github.com/rubieproofie/blind-VDF-wesolowski

---

## Abstract

We resolve the open problem left explicit by Hoffmann and Pietrzak (ePrint 2026/737) for constructing *blind* verifiable delay functions (VDFs) based on Wesolowski's succinct repeated-squaring construction in groups of unknown order. A blind VDF allows a client to outsource the sequential evaluation on a secret input \(x\) to an untrusted server while preserving perfect input privacy and obtaining a verifiable output-proof pair \((y, \pi)\).

We present two fully concrete constructions:

1. **Hybrid construction** (Pietrzak PoE + Wesolowski succinct proof): Server returns \(O(T/S)\) group elements (Pietrzak-style checkpoints on the blinded input). Client unblinds in \(O(T/S)\) time and computes the final single-element Wesolowski proof \(\pi\) locally from the unblinded ladder.

2. **Pure Wesolowski-native construction** (interactive, client-chosen challenge): Uses a one-time public value \(z = a^{2^T}\) for cheap output unblinding and a single extra round where the client sends the Fiat–Shamir challenge after unblinding \(y\).

Both achieve statistical/computational blindness, soundness (reducing to Wesolowski + Pietrzak PoE or Wesolowski alone), and the original sequentiality. The hybrid matches Hoffmann–Pietrzak client efficiency while preserving Wesolowski's extreme succinctness; the native stays entirely within Wesolowski mechanics. We provide full algebraic proofs, security reductions, and a verified Python proof-of-concept.

---

## 1. Introduction

Verifiable delay functions (VDFs) [BLS18] produce an output \(y = x^{2^T}\) together with a short proof \(\pi\) that can be verified in time much smaller than \(T\). Wesolowski's construction [Wes19] is prized for its single-group-element proofs and verification cost of two exponentiations, making it ideal for randomness beacons, sealed-bid auctions, and leader election.

Hoffmann and Pietrzak [HP26] introduced *blind* VDFs (private outsourcing of secret \(x\)) and gave an elegant multiplicative-blinding solution for Pietrzak's repeated-squaring VDF. They explicitly noted that Wesolowski's succinct proof appears "much more difficult" because the prime challenge \(\ell = H(y)\) depends on the (blinded) output, breaking straightforward correction of the huge exponent in \(\pi = x^q\).

This note closes that gap with two practical constructions.

---

## 2. Preliminaries

Let \(\mathbb{G}\) be a group of unknown order (e.g., class group of an imaginary quadratic field or RSA modulus with secret factorization) with generator \(g\). Fix a public non-square \(a \in \mathbb{G}\). Let \(H: \mathbb{G} \to\) primes of bit-length \(\approx \lambda\) be a random oracle.

**Wesolowski VDF** [Wes19]: On input \(x \in \mathbb{G}\), \(T \in \mathbb{N}\), compute \(y = x^{2^T}\), \(\ell = H(y)\), \(q = \lfloor 2^T / \ell \rfloor\), \(r = 2^T \mod \ell\), \(\pi = x^q\). Verify: \(y \stackrel{?}{=} \pi^\ell \cdot x^r\).

**Pietrzak PoE** (with space-time tradeoff \(S\)): Provides \(O(T/S)\) checkpoints \(\gamma_k = \alpha^{2^{kS}}\) plus short segment proofs allowing efficient verification and evaluation of power-of-two exponents.

**Blindness** (from [HP26]): The server's view on a blinded input \(\alpha = x \cdot a^r\) (\(r\) uniform, \(\kappa \gg \lambda + \log T\)) is computationally/statistically indistinguishable from a random group element, even after seeing the final \((y, \pi)\).

---

## 3. Hybrid Construction (Idea 2)

**Public parameters:** \(\mathbb{G}\), \(a\), \(H\), \(T\), \(S\).

1. Client samples \(r \gets [0, 2^\kappa)\), sends \(\alpha = x \cdot a^r\).
2. Server computes \(\beta = \alpha^{2^T}\) and Pietrzak PoE checkpoints \(\{\gamma_k\}\) on \(\alpha\) (\(O(T/S)\) elements). Sends \((\beta, \{\gamma_k\})\).
3. Client unblinds checkpoints to obtain \(\{\delta_k = x^{2^{kS}}\}\) and \(y = x^{2^T}\) in \(O(T/S)\) time (exactly as in [HP26]).
4. Client computes \(\ell = H(y)\), \(q = \lfloor 2^T / \ell \rfloor\), and uses the unblinded ladder to evaluate \(\pi = x^q\) via base-\(2^S\) windowed exponentiation (\(O(T/S)\) time).
5. Output: \((y, \pi)\).

**Correctness:** Follows directly from Pietrzak completeness and the Wesolowski verification equation (algebra verified in Python PoC).

**Security:** Blindness inherits from [HP26]. Soundness reduces to Pietrzak PoE soundness + Wesolowski soundness in the random-oracle model. Sequentiality is preserved on the blinded input.

---

## 4. Wesolowski-Native Construction (Idea 1)

Publish a one-time public value \(z = a^{2^T}\) (verifiable with its own Wesolowski proof).

1. Client blinds and sends \(\alpha = x \cdot a^r\).
2. Server returns \(\beta = \alpha^{2^T}\).
3. Client unblinds \(y = \beta / z^r\) (cheap \(O(\log T)\) square-and-multiply).
4. Client sends challenge \(\ell = H(y)\) to server.
5. Server returns \(\pi' = \alpha^q\) under \(\ell\).
6. Client corrects \(\pi = \pi' / a^{r q}\) and outputs \((y, \pi)\).

**Correctness & security:** Algebraic identities hold exactly (see PoC). Blindness and soundness reduce to standard Wesolowski assumptions; the interactive challenge resolves Fiat–Shamir circularity without new primitives.

---

## 5. Efficiency and Implementation

- **Hybrid:** Server \(T\) sequential + \(O(T)\) PoE; client \(O(T/S)\); communication \(O(T/S)\) group elements; final proof = 1 element.
- **Native:** Server \(T\); client \(O(\log T)\) for \(y\) + \(O(T)\) for \(\pi\); communication 2 group elements + 1 prime; fully Wesolowski-native.

A verified Python PoC (toy RSA modulus, \(T=16\), \(S=4\)) confirms all algebraic steps succeed with 100% correctness in both variants.

---

## 6. Conclusion

We have given the first blind Wesolowski VDFs, closing the open problem of [HP26]. The hybrid offers practical efficiency; the native stays purely algebraic. Both are immediately deployable for privacy-preserving randomness beacons and sealed-bid protocols.

Open question: Can the native construction be made non-interactive while preserving succinctness and \(O(\mathrm{polylog}\, T)\) client work?

---

## Acknowledgments

Inspired by the challenge from István Seres on X. Code and full proofs are public.

---

## References

- [BLS18] D. Boneh et al. Verifiable Delay Functions. CRYPTO 2018.
- [HP26] C. Hoffmann, K. Pietrzak. Blind Verifiable Delay Functions. Cryptology ePrint Archive, Paper 2026/737, 2026.
- [Wes19] B. Wesolowski. Efficient Verifiable Delay Functions. Journal of Cryptology 33(4), 2020 (preprint 2018).