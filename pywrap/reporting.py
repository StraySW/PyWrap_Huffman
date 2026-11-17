"""Estadísticas compartidas entre la interfaz y la consola."""
from .huffman import Result


def describe_result(result: Result) -> str:
    r = result
    if r.original_bytes:
        percentage = r.savings_percentage
        change = (f'Reducción: {percentage:.2f}%' if percentage >= 0 else
                  f'Crecimiento: {-percentage:.2f}% (incluye la cabecera)')
    else:
        change = 'Porcentaje: no aplica a un original vacío (cabecera de 2 bytes).'
    lines = [
        f'Entrada: {r.source}',
        f'Guardado en: {r.destination}',
        f'Tamaño original: {r.original_bytes:,} bytes',
        f'Tamaño comprimido: {r.compressed_bytes:,} bytes',
        change,
        f'Símbolos distintos: {r.symbol_count}',
        f'Nodos del árbol: {r.node_count} (NF: {r.internal_nodes} internos)',
        f'TREE: {r.tree_bytes} bytes',
        f'BS: {r.final_bits} bits válidos en el último byte',
        f'ZIP: {r.payload_bytes} bytes',
    ]
    if r.original_bytes and r.savings_percentage < 0:
        lines.append('El árbol añade espacio; JPG, MP4 y ZIP pueden crecer.')
    if r.action == 'decompress':
        lines.append('Decodificación completada. Compara SHA-256 con el original para verificar integridad.')
    return '\n'.join(lines)
