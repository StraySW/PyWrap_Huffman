"""Uso: python3 comprimir.py archivo [salida.pkz]. Solo biblioteca estándar."""
import heapq
import sys
from collections import Counter
from pathlib import Path


def comprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser().resolve()
    datos = ruta.read_bytes()
    frecuencias = Counter(datos)

    # 1. Unir los dos elementos menos frecuentes hasta tener un árbol.
    # Una hoja es un byte (entero); un nodo interno es (izquierda, derecha).
    cola = [(frecuencia, byte, byte) for byte, frecuencia in frecuencias.items()]
    heapq.heapify(cola)
    while len(cola) > 1:
        peso_izq, minimo_izq, izquierda = heapq.heappop(cola)
        peso_der, minimo_der, derecha = heapq.heappop(cola)
        heapq.heappush(cola, (peso_izq + peso_der, min(minimo_izq, minimo_der),
                              (izquierda, derecha)))

    # 2. Crear códigos y guardar el árbol en preorden: 00 00 o 01 byte.
    codigos = {}
    arbol = bytearray()

    def recorrer(nodo, camino=''):
        if isinstance(nodo, int):
            codigos[nodo] = camino or '0'
            arbol.extend((1, nodo))
        else:
            arbol.extend((0, 0))
            recorrer(nodo[0], camino + '0')
            recorrer(nodo[1], camino + '1')

    if cola:
        recorrer(cola[0][2])

    # 3. Cambiar los bytes por sus códigos y agrupar los bits en bytes.
    bits = ''.join(codigos[byte] for byte in datos)
    cantidad_bits = len(bits)
    bs = (cantidad_bits - 1) % 8 + 1 if bits else 0
    bits += '0' * (-cantidad_bits % 8)
    zip_bytes = int(bits, 2).to_bytes(len(bits) // 8, 'big') if bits else b''
    nf = max(0, len(frecuencias) - 1)
    contenido = bytes((nf,)) + arbol + bytes((bs,)) + zip_bytes

    # 4. Guardar NF | TREE | BS | ZIP, sin reemplazar un archivo existente.
    destino = Path(salida).expanduser() if salida else ruta.with_name(ruta.name + '.pkz')
    with destino.open('xb') as archivo_salida:
        archivo_salida.write(contenido)

    print(f'Original: {len(datos)} bytes | Comprimido: {len(contenido)} bytes')
    print(f'Símbolos: {len(frecuencias)} | NF: {nf} | TREE: {len(arbol)} bytes')
    print(f'Bits: {cantidad_bits} | BS: {bs} | ZIP: {len(zip_bytes)} bytes')
    if datos:
        cambio = (1 - len(contenido) / len(datos)) * 100
        print(f'{"Reducción" if cambio >= 0 else "Crecimiento"}: {abs(cambio):.2f}%')
    print(f'Guardado en: {destino}')
    return destino


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        sys.exit('Uso: python3 comprimir.py archivo [salida.pkz]')
    try:
        comprimir(*sys.argv[1:])
    except FileExistsError:
        sys.exit('Error: la salida ya existe. Elige otro nombre; no se reemplazó.')
    except (OSError, ValueError) as error:
        sys.exit(f'No se pudo comprimir: {error}')
