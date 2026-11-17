"""Pruebas automatizadas usando solo la libreria estandar."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
import tempfile
import unittest

from pywrap.huffman import FormatError, compress, decompress


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HuffmanTests(unittest.TestCase):
    def roundtrip(self, filename: str, data: bytes):
        with tempfile.TemporaryDirectory() as base:
            path = Path(base) / 'source' / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            pack = compress(path, Path(base) / 'wrp')
            self.assertEqual(pack.destination.suffix, '.pkz')
            self.assertEqual(pack.input_bytes, len(data))
            restored = decompress(pack.destination, Path(base) / 'unwrp')
            self.assertEqual(restored.destination.name, filename)
            self.assertEqual(restored.destination.read_bytes(), data)
            self.assertEqual(digest(path), digest(restored.destination))
            return pack, restored

    def test_example_teacher(self):
        pack, _ = self.roundtrip('anm.txt', b'anita patina')
        self.assertEqual(pack.internal_nodes, 5)
        self.assertEqual(pack.tree_bytes, 22)
        self.assertEqual(pack.payload_bytes, 4)
        self.assertEqual(pack.final_bits, 6)
        self.assertEqual(pack.output_bytes, 28)

    def test_empty(self):
        pack, _ = self.roundtrip('vacio.txt', b'')
        self.assertEqual(pack.output_bytes, 2)

    def test_one_symbol(self):
        pack, _ = self.roundtrip('repetido.bin', b'X' * 1007)
        self.assertEqual(pack.internal_nodes, 0)
        self.assertEqual(pack.tree_bytes, 2)

    def test_all_256_symbols(self):
        pack, _ = self.roundtrip('todos.bin', bytes(range(256)) * 8)
        self.assertEqual(pack.internal_nodes, 255)
        self.assertEqual(pack.tree_bytes, 1022)

    def test_random_binary(self):
        rnd = random.Random(12345)
        self.roundtrip('video.mp4', rnd.randbytes(80_000))

    def test_spanish_utf8(self):
        self.roundtrip('español.txt', ('¡Piñata! Árbol Ñandú 😊\n' * 100).encode())

    def test_truncated_tree(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'roto.pkz'
            path.write_bytes(bytes([5, 0, 0, 0, 0, 1]))
            with self.assertRaises(FormatError):
                decompress(path, Path(folder) / 'out')
            self.assertFalse((Path(folder) / 'out' / 'roto').exists())

    def test_no_pkz(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'archivo.bin'
            path.write_bytes(b'basura')
            with self.assertRaises(ValueError):
                decompress(path, Path(folder) / 'out')


if __name__ == '__main__':
    unittest.main()
