"""Regresiones de integridad, publicación y compatibilidad del formato."""
from pathlib import Path
from collections import Counter
import hashlib
import tempfile
import unittest
from unittest.mock import patch

from pywrap import FormatError, compress, decompress
from pywrap import huffman


class FileTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name).resolve()
        self.source = self.base / 'sample.bin'
        self.source.write_bytes(b'anita patina')

    def test_failed_replacement_preserves_previous_output(self):
        packed = compress(self.source, self.base / 'input')
        for operation, source, folder, destination in (
            (compress, self.source, self.base / 'wrp',
             self.base / 'wrp' / (self.source.name + '.pkz')),
            (decompress, packed.destination, self.base / 'restored',
             self.base / 'restored' / self.source.name),
        ):
            with self.subTest(operation=operation.__name__):
                folder.mkdir(exist_ok=True)
                destination.write_bytes(b'previous output')
                with patch.object(huffman.os, 'replace', side_effect=OSError('disk error')):
                    with self.assertRaises(OSError):
                        operation(source, folder, overwrite=True)
                self.assertEqual(destination.read_bytes(), b'previous output')
                self.assertEqual(set(folder.iterdir()), {destination})

    def test_concurrent_destination_is_not_overwritten(self):
        real_publish = huffman._publish

        def publish_after_race(temporary, destination, *, overwrite):
            destination.write_bytes(b'created by another process')
            real_publish(temporary, destination, overwrite=overwrite)

        packed = compress(self.source, self.base / 'wrp')
        for operation, source, folder in (
            (compress, self.source, self.base / 'race-compress'),
            (decompress, packed.destination, self.base / 'race-decompress'),
        ):
            with self.subTest(operation=operation.__name__):
                with patch.object(huffman, '_publish', side_effect=publish_after_race):
                    with self.assertRaises(FileExistsError):
                        operation(source, folder)
                files = list(folder.iterdir())
                self.assertEqual(len(files), 1)
                self.assertEqual(files[0].read_bytes(), b'created by another process')

    def test_explicit_overwrite_replaces_output(self):
        packed = compress(self.source, self.base / 'wrp')
        self.source.write_bytes(b'a changed original')
        compress(self.source, self.base / 'wrp', overwrite=True)
        restored = decompress(packed.destination, self.base / 'out')
        restored.destination.write_bytes(b'outdated')
        decompress(packed.destination, self.base / 'out', overwrite=True)
        self.assertEqual(restored.destination.read_bytes(), self.source.read_bytes())

    def test_rejects_invalid_bits_without_publishing(self):
        # Árbol de una hoja X: NF=0, TREE=(1, X), BS=1, ZIP.
        for payload in (0x80, 0x01):
            with self.subTest(payload=payload):
                source = self.base / f'corrupt-{payload}.pkz'
                source.write_bytes(bytes((0, 1, ord('X'), 1, payload)))
                out = self.base / f'out-{payload}'
                with self.assertRaises(FormatError):
                    decompress(source, out)
                self.assertEqual(list(out.iterdir()), [])

    def test_invalid_input_preserves_existing_output(self):
        source = self.base / 'broken.pkz'
        source.write_bytes(bytes((0, 1, ord('X'), 1, 0x80)))
        out = self.base / 'out'
        out.mkdir()
        destination = out / 'broken'
        destination.write_bytes(b'keep me')
        with self.assertRaises(FormatError):
            decompress(source, out, overwrite=True)
        self.assertEqual(destination.read_bytes(), b'keep me')
        self.assertEqual(list(out.iterdir()), [destination])

    def test_fixed_fixtures_roundtrip_with_identical_pkz_bytes(self):
        fixtures = Path(__file__).parent / 'fixtures'
        cases = {'anita.txt': b'anita patina', 'empty.bin': b'',
                 'single.bin': b'X' * 17, 'all-bytes.bin': bytes(range(256))}
        for name, expected in cases.items():
            with self.subTest(name=name):
                fixture = fixtures / (name + '.pkz')
                restored = decompress(fixture, self.base / 'out')
                self.assertEqual(restored.destination.read_bytes(), expected)
                packed = compress(restored.destination, self.base / 'wrp')
                self.assertEqual(packed.destination.read_bytes(), fixture.read_bytes())

    def test_rejects_invalid_original_names(self):
        for name in ('.pkz', '..pkz', '...pkz'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    huffman.output_path(self.base / name, self.base / 'out', 'decompress')

    def test_large_binary_uses_bounded_reads_and_writes(self):
        block = bytes(range(256)) * 256
        with self.source.open('wb') as stream:
            for _ in range(128):
                stream.write(block)
        self.assertEqual(self.source.stat().st_size, 8 * 1024 * 1024)
        reads, writes = [], []
        real_open = Path.open
        real_temporary = huffman.tempfile.NamedTemporaryFile
        test = self

        class BoundedStream:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.stream, name)

            def read(self, size=-1):
                test.assertGreater(size, 0, 'No se permite cargar el archivo completo.')
                test.assertLessEqual(size, huffman.CHUNK_SIZE)
                reads.append(size)
                return self.stream.read(size)

            def write(self, data):
                # Un código Huffman puede tener hasta 255 bits por símbolo.
                test.assertLessEqual(len(data), huffman.CHUNK_SIZE * 32)
                writes.append(len(data))
                return self.stream.write(data)

        def open_stream(path, *args, **kwargs):
            return BoundedStream(real_open(path, *args, **kwargs))

        def temporary_stream(*args, **kwargs):
            return BoundedStream(real_temporary(*args, **kwargs))

        with patch.object(Path, 'open', open_stream), \
                patch.object(huffman.tempfile, 'NamedTemporaryFile', temporary_stream):
            packed = compress(self.source, self.base / 'wrp')
            # La recuperación solo depende del .pkz, no del original.
            self.source.unlink()
            restored = decompress(packed.destination, self.base / 'out')

        expected = hashlib.sha256()
        actual = hashlib.sha256()
        for _ in range(128):
            expected.update(block)
        with restored.destination.open('rb') as stream:
            while chunk := stream.read(huffman.CHUNK_SIZE):
                actual.update(chunk)
        self.assertEqual(actual.digest(), expected.digest())
        self.assertEqual(restored.output_bytes, 8 * 1024 * 1024)
        self.assertGreater(len(reads), 256)
        self.assertGreater(len(writes), 128)
        self.assertEqual(list(self.base.rglob('.pywrap-*.tmp')), [])

    def test_long_variable_codes_cross_block_boundaries(self):
        block = b''.join(bytes((symbol,)) * 2 ** symbol for symbol in range(12))
        data = block * 49 + b'\x00'
        codes = huffman._codes(huffman._build_tree(Counter(data)))
        self.assertGreater(max(length for _, length in codes.values()), 8)
        self.assertGreater(len(data), huffman.CHUNK_SIZE * 3)
        self.source.write_bytes(data)
        packed = compress(self.source, self.base / 'wrp')
        restored = decompress(packed.destination, self.base / 'out')
        self.assertEqual(restored.destination.read_bytes(), data)
