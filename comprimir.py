"""Comprime un archivo con Huffman. Uso: python comprimir.py archivo [salida.pkz]"""
import sys
from collections import Counter
from pathlib import Path


def comprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    datos = ruta.read_bytes()
    frecuencias = Counter(datos)

    # 1. Construir el árbol uniendo los dos nodos menos frecuentes.
    #    Cada nodo es (frecuencia, byte mínimo, árbol). El árbol de una hoja es
    #    su byte; el de un nodo interno es la tupla (izquierda, derecha).
    nodos = [(frecuencia, byte, byte) for byte, frecuencia in frecuencias.items()]
    while len(nodos) > 1:
        nodos.sort()  # Por frecuencia; en empate, por byte mínimo (nunca se repite).
        peso_izq, minimo_izq, izquierda = nodos.pop(0)
        peso_der, minimo_der, derecha = nodos.pop(0)
        minimo = min(minimo_izq, minimo_der)
        nodos.append((peso_izq + peso_der, minimo, (izquierda, derecha)))

    # 2. Crear códigos y guardar TREE en preorden (raíz, izquierda, derecha).
    codigos = {}
    arbol = bytearray()

    def recorrer(nodo, codigo=""):
        if isinstance(nodo, int):
            codigos[nodo] = codigo or "0"  # Árbol de una sola hoja: código 0.
            arbol.extend((1, nodo))       # Hoja: 01 + símbolo
        else:
            arbol.extend((0, 0))          # Nodo interno: 00 00
            recorrer(nodo[0], codigo + "0")
            recorrer(nodo[1], codigo + "1")

    if nodos:                 # Un archivo vacío no tiene árbol.
        recorrer(nodos[0][2])

    # 3. Empaquetar los bits y registrar cuántos son válidos en el último byte.
    bits = "".join(codigos[byte] for byte in datos)
    bs = 0
    zip_bytes = b""
    if bits:
        bs = len(bits) % 8 or 8
        bits += "0" * (8 - bs)
        zip_bytes = int(bits, 2).to_bytes(len(bits) // 8, "big")

    # 4. Guardar NF | TREE | BS | ZIP sin sobrescribir archivos.
    nf = max(0, len(frecuencias) - 1)
    contenido = bytes([nf]) + arbol + bytes([bs]) + zip_bytes

    destino = Path(salida).expanduser() if salida else ruta.with_name(ruta.name + ".pkz")
    with destino.open("xb") as archivo_salida:
        archivo_salida.write(contenido)

    print(f"Original: {len(datos)} bytes | Comprimido: {len(contenido)} bytes")
    print(f"Guardado en: {destino}")
    return destino


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python comprimir.py archivo [salida.pkz]")
    try:
        comprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(f"No se pudo comprimir: {error}")
