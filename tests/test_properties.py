"""Propiedades independientes del árbol y corpus binario aleatorio reproducible."""
from collections import Counter
from functools import lru_cache
from itertools import permutations, product
import hashlib
from pathlib import Path
import random
import tempfile
import unittest

from pywrap import compress, decompress
from pywrap.huffman import _build_tree, _codes, _serialize


@lru_cache(maxsize=None)
def minimum_merge_cost(weights):
    """Oráculo exhaustivo: prueba TODAS las parejas, no usa heap ni Huffman.

    Cada unión añade su peso al costo de caminos externos. El mínimo entre
    todas las secuencias posibles es el costo óptimo para alfabetos pequeños.
    """
    if len(weights) <= 1:
        return 0
    alternatives = []
    for left in range(len(weights)):
        for right in range(left + 1, len(weights)):
            merged = weights[left] + weights[right]
            remaining = [w for i, w in enumerate(weights) if i not in (left, right)]
            alternatives.append(merged + minimum_merge_cost(tuple(sorted(remaining + [merged]))))
    return min(alternatives)


class PropertyTests(unittest.TestCase):
    def test_weighted_path_cost_is_optimal_against_exhaustive_oracle(self):
        for symbols in range(2, 7):
            for weights in product((1, 2, 3), repeat=symbols):
                # Las permutaciones equivalentes ya tienen el mismo óptimo.
                if weights != tuple(sorted(weights)):
                    continue
                with self.subTest(weights=weights):
                    frequencies = Counter(dict(enumerate(weights)))
                    codes = _codes(_build_tree(frequencies))
                    actual = sum(frequencies[s] * length for s, (_, length) in codes.items())
                    self.assertEqual(actual, minimum_merge_cost(weights))

    def test_prefix_free_codes_for_ties_skew_and_all_bytes(self):
        cases = [Counter({i: 1 for i in range(256)}),
                 Counter({i: 2 ** i for i in range(24)}),
                 Counter(b'anita patina'), Counter(b'X' * 101)]
        for frequencies in cases:
            values = [format(value, f'0{length}b') for value, length
                      in _codes(_build_tree(frequencies)).values()]
            for i, code in enumerate(values):
                for j, other in enumerate(values):
                    if i != j:
                        self.assertFalse(other.startswith(code), (code, other))
            if len(values) > 1:
                self.assertAlmostEqual(sum(2 ** -len(code) for code in values), 1.0)

    def test_ties_are_independent_of_counter_insertion_order(self):
        symbols = (32, 97, 105, 110, 112, 116)
        frequencies = {32: 1, 97: 4, 105: 2, 110: 2, 112: 1, 116: 2}
        expected = _build_tree(Counter(frequencies))
        for order in permutations(symbols):
            root = _build_tree(Counter({s: frequencies[s] for s in order}))
            self.assertEqual(_codes(root), _codes(expected))
            self.assertEqual(_serialize(root), _serialize(expected))

    def test_seeded_binary_corpus_roundtrips_byte_for_byte_and_sha256(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for seed in range(12):
                rng = random.Random(seed)
                # Incluye alfabetos pequeños, empates, bytes arbitrarios y BS variados.
                for alphabet in (1, 2, 3, 17, 256):
                    length = rng.randrange(0, 14000)
                    data = bytes(rng.randrange(alphabet) for _ in range(length))
                    source = base / f'{seed}-{alphabet}.bin'
                    source.write_bytes(data)
                    packed = compress(source, base / 'wrp')
                    restored = decompress(packed.destination, base / 'out')
                    actual = restored.destination.read_bytes()
                    self.assertEqual(actual, data)
                    self.assertEqual(hashlib.sha256(actual).digest(), hashlib.sha256(data).digest())
                    self.assertEqual(list(base.rglob('.pywrap-*.tmp')), [])
