import sys
from collections import Counter
from pathlib import Path


def comprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    datos = ruta.read_bytes()
    frecuencias = Counter(datos)

    # Armar el árbol con los bytes menos frecuentes.
    nodos = [(peso, byte) for byte, peso in frecuencias.items()]
    while len(nodos) > 1:
        nodos.sort(key=lambda nodo: nodo[0])
        peso_a, a = nodos.pop(0)
        peso_b, b = nodos.pop(0)
        nodos.append((peso_a + peso_b, (a, b)))

    # Crear los códigos y guardar el árbol.
    codigos = {}
    arbol = bytearray()
    def recorrer(nodo, codigo=""):
        if isinstance(nodo, int):
            codigos[nodo] = codigo or "0"
            arbol.extend((1, nodo))
        else:
            arbol.extend((0, 0))
            recorrer(nodo[0], codigo + "0")
            recorrer(nodo[1], codigo + "1")
    if nodos:
        recorrer(nodos[0][1])

    # Pasar los bits a bytes y guardar el archivo.
    bits = "".join(codigos[byte] for byte in datos)
    bs = 0
    if bits:
        bs = len(bits) % 8 or 8
        bits += "0" * (8 - bs)
    comprimido = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    contenido = bytes([max(0, len(frecuencias) - 1)]) + arbol + bytes([bs]) + comprimido
    destino = Path(salida).expanduser() if salida else ruta.with_name(ruta.name + ".pkz")
    with destino.open("xb") as f:
        f.write(contenido)
    print(f"Original: {len(datos)} bytes | Comprimido: {len(contenido)} bytes")
    print(f"Guardado en: {destino}")
    return destino


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python comprimir.py archivo [salida.pkz]")
    try:
        comprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(str(error))
