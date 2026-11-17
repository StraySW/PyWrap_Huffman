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
from contextlib import contextmanager
from dataclasses import dataclass
from heapq import heappop, heappush
import os
from pathlib import Path
import tempfile


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

    def __str__(self) -> str:
        return (f'Guardado en: {self.destination}\n'
                f'Entrada: {self.input_bytes:,} bytes\n'
                f'Salida: {self.output_bytes:,} bytes')


def _build_tree(freq: Counter[int]) -> Node | None:
    """Construye el árbol de Huffman con cola de prioridad mínima."""
    heap: list[tuple[int, int, Node]] = []
    for symbol in sorted(freq):
        node = Node(frequency=freq[symbol], symbol=symbol, minimum=symbol)
        heappush(heap, (node.frequency, node.minimum, node))
    if not heap:
        return None
    while len(heap) > 1:
        _, _, left = heappop(heap)
        _, _, right = heappop(heap)
        parent = Node(
            frequency=left.frequency + right.frequency,
            left=left,
            right=right,
            minimum=min(left.minimum, right.minimum),
        )
        # Los subárboles no comparten símbolos: sus mínimos son distintos.
        heappush(heap, (parent.frequency, parent.minimum, parent))
    return heap[0][2]


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
        if name in ('', '.', '..'):
            raise ValueError('El archivo .pkz no tiene un nombre original válido.')
    dest = folder / name
    if dest.resolve() == input_file.resolve():
        raise ValueError('El archivo de salida no puede ser el mismo archivo de entrada.')
    return dest


def _publish(temporary: Path, destination: Path, *, overwrite: bool) -> None:
    """Publica sin borrar antes el destino ni reemplazarlo sin autorización."""
    if overwrite:
        os.replace(temporary, destination)
    elif os.name == 'nt':
        # En Windows rename falla si otro proceso ya creó el destino.
        os.rename(temporary, destination)
    else:
        # En POSIX rename sí reemplaza: un enlace reserva el nombre sin pisarlo.
        os.link(temporary, destination)
        temporary.unlink()


@contextmanager
def _operation(input_file, output_folder, action, overwrite):
    """Comparte apertura, destino seguro y limpieza entre ambas operaciones."""
    source = Path(input_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f'No se encuentra el archivo de entrada: {source}')
    folder = Path(output_folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    destination = output_path(source, folder, action)
    if destination.exists() and not overwrite:
        raise FileExistsError(f'El archivo ya existe: {destination}.')

    temporary = None
    try:
        with source.open('rb') as inp, tempfile.NamedTemporaryFile(
                mode='wb', prefix='.pywrap-', suffix='.tmp', dir=folder,
                delete=False) as out:
            temporary = Path(out.name)
            yield source, destination, inp, out
        _publish(temporary, destination, overwrite=overwrite)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def compress(input_file: str | Path, output_folder: str | Path, *,
             overwrite: bool = False) -> Result:
    """Comprime cualquier archivo por bloques, sin cargarlo completo en memoria."""
    with _operation(input_file, output_folder, 'compress', overwrite) as files:
        source, destination, inp, out = files
        # 1. Contar los bytes leyendo bloques pequeños.
        freq: Counter[int] = Counter()
        input_size = 0
        while chunk := inp.read(CHUNK_SIZE):
            freq.update(chunk)
            input_size += len(chunk)

        # 2. Construir el árbol, los códigos y el encabezado.
        root = _build_tree(freq)
        tree_blob, nf = _serialize(root) if root else (b'', 0)
        codes = _codes(root) if root else {}
        bit_count = sum(freq[symbol] * length for symbol, (_, length) in codes.items())
        bs = (bit_count - 1) % 8 + 1 if bit_count else 0
        out.write(bytes((nf,)) + tree_blob + bytes((bs,)))

        # 3. Volver a leer y guardar los códigos en grupos de ocho bits.
        inp.seek(0)
        acc = remaining = 0
        buf = bytearray()
        while chunk := inp.read(CHUNK_SIZE):
            for symbol in chunk:
                code, length = codes[symbol]
                acc = (acc << length) | code
                remaining += length
                while remaining >= 8:
                    remaining -= 8
                    buf.append((acc >> remaining) & 0xFF)
                    acc &= (1 << remaining) - 1
            out.write(buf)
            buf.clear()
        if remaining:
            out.write(bytes((acc << (8 - remaining),)))
        output_size = out.tell()

    return Result(source, destination, input_size, output_size)


def decompress(input_file: str | Path, output_folder: str | Path, *,
               overwrite: bool = False) -> Result:
    """Recupera los bytes originales leyendo y escribiendo por bloques."""
    with _operation(input_file, output_folder, 'decompress', overwrite) as files:
        source, destination, inp, out = files
        source_size = os.fstat(inp.fileno()).st_size
        if source_size < 2:
            raise FormatError('El archivo es demasiado pequeño para ser un .pkz válido.')
        # 1. Leer el encabezado y reconstruir el árbol guardado.
        nf = inp.read(1)[0]

        if source_size == 2 and nf == 0:
            if inp.read(1) != b'\x00':
                raise FormatError('Un archivo vacío debe tener BS=0.')
        else:
            tree_len = 2 * (2 * nf + 1)
            tree_blob = inp.read(tree_len)
            if len(tree_blob) != tree_len:
                raise FormatError('Árbol Huffman truncado en el archivo.')
            tree = _deserialize(tree_blob, nf)
            header_bs = inp.read(1)
            if not header_bs or not 1 <= header_bs[0] <= 8:
                raise FormatError('El byte BS debe estar entre 1 y 8.')
            bs = header_bs[0]
            payload_size = source_size - inp.tell()
            if payload_size <= 0:
                raise FormatError('No se encontraron datos codificados.')

            # 2. Seguir los bits hasta una hoja y escribir su byte.
            current = tree
            buf = bytearray()
            bytes_left = payload_size
            while bytes_left:
                block = inp.read(min(CHUNK_SIZE, bytes_left))
                if not block:
                    raise FormatError('Datos ZIP truncados inesperadamente.')
                bytes_left -= len(block)
                for idx, value in enumerate(block):
                    last = bytes_left == 0 and idx == len(block) - 1
                    valid_bits = bs if last else 8
                    if last and value & ((1 << (8 - valid_bits)) - 1):
                        raise FormatError('Los bits de relleno deben ser cero.')
                    if tree.is_leaf:
                        if value:
                            raise FormatError('El código de un símbolo único debe ser 0.')
                        buf.extend(bytes((tree.symbol,)) * valid_bits)
                    else:
                        for shift in range(7, 7 - valid_bits, -1):
                            current = current.right if (value >> shift) & 1 else current.left
                            if current.is_leaf:
                                buf.append(current.symbol)
                                current = tree
                    if len(buf) >= CHUNK_SIZE:
                        out.write(buf)
                        buf.clear()
            if current is not tree:
                raise FormatError('Los datos terminan en un código incompleto.')
            out.write(buf)
        output_size = out.tell()

    return Result(source, destination, source_size, output_size)
