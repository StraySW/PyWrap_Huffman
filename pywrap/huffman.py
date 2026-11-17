"""Compresor y descompresor Huffman (ASCII / Binario) sin dependencias externas.

Formato estándar .pkz:
  NF   : 1 byte con el número de nodos internos (0..255).
  TREE : 2 * (2 * NF + 1) bytes con el árbol en preorden:
         (0, 0) = nodo interno; (1, símbolo) = hoja.
  BS   : 1 byte con los bits válidos del último byte de ZIP (1..8).
  ZIP  : Flujo de bits empaquetado MSB-first.

Caso especial archivo vacío: exactamente 2 bytes (NF=0, BS=0).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
import os
from pathlib import Path
import tempfile
from typing import BinaryIO


CHUNK_SIZE = 64 * 1024


class FormatError(ValueError):
    """Excepción para archivos .pkz inválidos o dañados."""


@dataclass
class Node:
    frequency: int = 0
    symbol: int | None = None
    left: Node | None = None
    right: Node | None = None
    minimum: int = 0

    @property
    def is_leaf(self) -> bool:
        return self.symbol is not None


@dataclass(frozen=True)
class Result:
    source: Path
    destination: Path
    input_bytes: int
    output_bytes: int
    internal_nodes: int
    tree_bytes: int
    payload_bytes: int
    final_bits: int
    action: str

    @property
    def symbol_count(self) -> int:
        return self.internal_nodes + 1 if self.tree_bytes else 0

    @property
    def node_count(self) -> int:
        return 2 * self.internal_nodes + 1 if self.tree_bytes else 0

    @property
    def original_bytes(self) -> int:
        return self.input_bytes if self.action == 'compress' else self.output_bytes

    @property
    def compressed_bytes(self) -> int:
        return self.output_bytes if self.action == 'compress' else self.input_bytes

    @property
    def savings_percentage(self) -> float:
        if not self.original_bytes:
            return 0.0
        return (1.0 - self.compressed_bytes / self.original_bytes) * 100.0


def _build_tree(freq: Counter[int]) -> Node | None:
    """Construye el árbol de Huffman con cola de prioridad mínima."""
    heap: list[tuple[int, int, int, Node]] = []
    counter = count()
    for symbol in sorted(freq):
        node = Node(frequency=freq[symbol], symbol=symbol, minimum=symbol)
        heappush(heap, (node.frequency, node.minimum, next(counter), node))
    if not heap:
        return None
    while len(heap) > 1:
        _, _, _, left = heappop(heap)
        _, _, _, right = heappop(heap)
        parent = Node(
            frequency=left.frequency + right.frequency,
            left=left,
            right=right,
            minimum=min(left.minimum, right.minimum),
        )
        heappush(heap, (parent.frequency, parent.minimum, next(counter), parent))
    return heap[0][3]


def _codes(root: Node) -> dict[int, tuple[int, int]]:
    """Genera la tabla de códigos prefijo (valor_binario, longitud_bits)."""
    codes: dict[int, tuple[int, int]] = {}

    def walk(node: Node, value: int, depth: int) -> None:
        if node.is_leaf:
            codes[node.symbol] = (value, max(depth, 1))
            return
        assert node.left is not None and node.right is not None
        walk(node.left, value << 1, depth + 1)
        walk(node.right, (value << 1) | 1, depth + 1)

    walk(root, 0, 0)
    return codes


def _serialize(root: Node) -> tuple[bytes, int]:
    """Serializa el árbol en preorden: (0,0) interno, (1, símbolo) hoja."""
    blob = bytearray()
    internals = 0

    def visit(node: Node) -> None:
        nonlocal internals
        if node.is_leaf:
            blob.extend((1, node.symbol))
        else:
            internals += 1
            blob.extend((0, 0))
            assert node.left is not None and node.right is not None
            visit(node.left)
            visit(node.right)

    visit(root)
    return bytes(blob), internals


def _deserialize(blob: bytes, internal_count: int) -> Node:
    """Reconstruye el árbol desde su representación preorden."""
    offset = 0
    internals = 0
    leaves = 0
    symbols: set[int] = set()

    def visit() -> Node:
        nonlocal offset, internals, leaves
        if offset + 2 > len(blob):
            raise FormatError('El árbol Huffman está incompleto.')
        flag, value = blob[offset], blob[offset + 1]
        offset += 2
        if flag == 1:
            leaves += 1
            if value in symbols:
                raise FormatError('El árbol contiene una hoja duplicada.')
            symbols.add(value)
            return Node(symbol=value, minimum=value)
        if flag != 0 or value != 0:
            raise FormatError('Etiqueta de nodo inválida en el árbol.')
        internals += 1
        if internals > internal_count:
            raise FormatError('El árbol contiene más nodos internos de los declarados.')
        left = visit()
        right = visit()
        return Node(left=left, right=right)

    root = visit()
    if offset != len(blob) or internals != internal_count or leaves != internal_count + 1:
        raise FormatError('El árbol no coincide con el encabezado NF.')
    return root


def output_path(input_file: Path, folder: Path, action: str) -> Path:
    """Calcula la ruta de salida conservando el nombre original."""
    if action == 'compress':
        name = input_file.name + '.pkz'
    else:
        if input_file.suffix.lower() != '.pkz':
            raise ValueError('Selecciona un archivo con extensión .pkz para descomprimir.')
        name = input_file.name[:-4]
        if not name:
            raise ValueError('El archivo .pkz no tiene un nombre original válido.')
    dest = folder / name
    if dest.resolve() == input_file.resolve():
        raise ValueError('El archivo de salida no puede ser el mismo archivo de entrada.')
    return dest


def compress(input_file: str | Path, output_folder: str | Path, *,
             overwrite: bool = False) -> Result:
    """Comprime un archivo usando el algoritmo Huffman."""
    source = Path(input_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f'No se encuentra el archivo de entrada: {source}')

    out_dir = Path(output_folder).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = output_path(source, out_dir, 'compress')

    if destination.exists() and not overwrite:
        raise FileExistsError(f'El archivo ya existe: {destination}.')

    input_size = source.stat().st_size
    freq: Counter[int] = Counter()
    with source.open('rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            freq.update(chunk)

    root = _build_tree(freq)
    tree_blob, nf = _serialize(root) if root else (b'', 0)
    tree_len = len(tree_blob)

    with tempfile.NamedTemporaryFile(prefix='pkz_', dir=out_dir, delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with tmp_path.open('wb') as out:
            # 1. NF (1 byte)
            out.write(bytes((nf,)))
            # 2. TREE
            out.write(tree_blob)
            # 3. Posición para BS
            bs_pos = out.tell()
            out.write(b'\x00')

            payload_bytes = 0
            bs = 0

            if root is not None:
                code_map = _codes(root)
                acc = 0
                remaining = 0
                buf = bytearray()

                with source.open('rb') as f:
                    while chunk := f.read(CHUNK_SIZE):
                        for symbol in chunk:
                            code, length = code_map[symbol]
                            acc = (acc << length) | code
                            remaining += length
                            while remaining >= 8:
                                remaining -= 8
                                buf.append((acc >> remaining) & 0xFF)
                                acc &= (1 << remaining) - 1
                        if len(buf) >= CHUNK_SIZE:
                            out.write(buf)
                            payload_bytes += len(buf)
                            buf.clear()

                if remaining > 0:
                    buf.append((acc << (8 - remaining)) & 0xFF)
                    bs = remaining
                else:
                    bs = 8 if payload_bytes or buf else 0

                if buf:
                    out.write(buf)
                    payload_bytes += len(buf)

                # Actualizar BS
                out.seek(bs_pos)
                out.write(bytes((bs,)))
            else:
                # Archivo vacío: BS=0
                out.seek(bs_pos)
                out.write(b'\x00')

        # Reemplazo seguro
        if destination.exists() and overwrite:
            destination.unlink()
        os.replace(tmp_path, destination)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    output_size = destination.stat().st_size
    return Result(
        source=source,
        destination=destination,
        input_bytes=input_size,
        output_bytes=output_size,
        internal_nodes=nf,
        tree_bytes=tree_len,
        payload_bytes=payload_bytes,
        final_bits=bs,
        action='compress',
    )


def decompress(input_file: str | Path, output_folder: str | Path, *,
               overwrite: bool = False) -> Result:
    """Descomprime un archivo .pkz recuperando los datos originales."""
    source = Path(input_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f'No se encuentra el archivo de entrada: {source}')

    out_dir = Path(output_folder).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = output_path(source, out_dir, 'decompress')

    if destination.exists() and not overwrite:
        raise FileExistsError(f'El archivo ya existe: {destination}.')

    source_size = source.stat().st_size
    if source_size < 2:
        raise FormatError('El archivo es demasiado pequeño para ser un archivo .pkz válido.')

    with tempfile.NamedTemporaryFile(prefix='unpkz_', dir=out_dir, delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with source.open('rb') as inp, tmp_path.open('wb') as out:
            header_nf = inp.read(1)
            if not header_nf:
                raise FormatError('Encabezado incompleto.')
            nf = header_nf[0]

            # Caso especial vacío: 2 bytes (NF=0, BS=0)
            if source_size == 2 and nf == 0:
                bs = inp.read(1)[0]
                if bs != 0:
                    raise FormatError('Formato inválido: archivo vacío debe tener BS=0.')
                tree_len = 0
                payload_size = 0
            else:
                tree_len = 2 * (2 * nf + 1)
                tree_blob = inp.read(tree_len)
                if len(tree_blob) != tree_len:
                    raise FormatError('Árbol Huffman truncado en el archivo.')
                tree = _deserialize(tree_blob, nf)

                header_bs = inp.read(1)
                if not header_bs:
                    raise FormatError('Falta el byte BS en el archivo.')
                bs = header_bs[0]
                if not (1 <= bs <= 8):
                    raise FormatError('El byte BS está fuera del rango válido (1..8).')

                payload_size = source_size - inp.tell()
                if payload_size <= 0:
                    raise FormatError('No se encontraron datos codificados en el archivo.')

                # Decodificación bit a bit
                current = tree
                buf = bytearray()
                bytes_left = payload_size

                while bytes_left > 0:
                    block = inp.read(min(CHUNK_SIZE, bytes_left))
                    if not block:
                        raise FormatError('Datos ZIP truncados inesperadamente.')
                    bytes_left -= len(block)

                    for idx, byte_val in enumerate(block):
                        is_last = (bytes_left == 0 and idx == len(block) - 1)
                        valid_bits = bs if is_last else 8

                        for shift in range(7, 7 - valid_bits, -1):
                            bit = (byte_val >> shift) & 1
                            if tree.is_leaf:
                                buf.append(tree.symbol)
                            else:
                                current = current.right if bit else current.left
                                if current is None:
                                    raise FormatError('Ruta inválida en el árbol Huffman.')
                                if current.is_leaf:
                                    buf.append(current.symbol)
                                    current = tree

                            if len(buf) >= CHUNK_SIZE:
                                out.write(buf)
                                buf.clear()

                if current is not tree:
                    raise FormatError('Los datos codificados terminan en un nodo intermedio.')
                if buf:
                    out.write(buf)

        if destination.exists() and overwrite:
            destination.unlink()
        os.replace(tmp_path, destination)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    output_size = destination.stat().st_size
    return Result(
        source=source,
        destination=destination,
        input_bytes=source_size,
        output_bytes=output_size,
        internal_nodes=nf,
        tree_bytes=tree_len,
        payload_bytes=payload_size,
        final_bits=bs,
        action='decompress',
    )
