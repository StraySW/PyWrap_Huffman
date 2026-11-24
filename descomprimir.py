"""Descomprime Huffman .pkz/.huf. Uso: python descomprimir.py archivo.pkz [salida]"""
import sys
from pathlib import Path


def descomprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    if ruta.suffix.lower() not in (".pkz", ".huf"):
        raise ValueError("Selecciona un archivo .pkz o .huf")
    datos = ruta.read_bytes()

    recuperado = bytearray()
    if datos != b"\x00\x00":  # Dos ceros representan un archivo vacío.
        # 1. NF indica los nodos internos. El árbol tiene 2 * NF + 1 nodos.
        if not datos:
            raise ValueError("Falta la cabecera del archivo comprimido")
        nf = datos[0]
        fin_arbol = 1 + 2 * (2 * nf + 1)
        if len(datos) < fin_arbol + 2:
            raise ValueError("Faltan datos de TREE, BS o ZIP")

        # 2. Leer TREE en preorden. Cada nodo ocupa dos bytes.
        posicion = 1
        simbolos = set()

        def leer_arbol():
            nonlocal posicion
            if posicion == fin_arbol:
                raise ValueError("Árbol incompleto")
            tipo, valor = datos[posicion:posicion + 2]
            posicion += 2
            if tipo == 1:                 # Hoja (símbolo).
                if valor in simbolos:
                    raise ValueError("Símbolo repetido en TREE")
                simbolos.add(valor)
                return valor
            if (tipo, valor) != (0, 0):   # Nodo interno.
                raise ValueError("Nodo inválido en TREE")
            return (leer_arbol(), leer_arbol())

        raiz = leer_arbol()
        if posicion != fin_arbol:
            raise ValueError("TREE no coincide con NF")

        # 3. Leer los bits de ZIP. Del último byte solo valen los primeros BS bits.
        bs = datos[fin_arbol]
        zip_bytes = datos[fin_arbol + 1:]
        if not 1 <= bs <= 8:
            raise ValueError("BS debe estar entre 1 y 8")
        if "1" in f"{zip_bytes[-1]:08b}"[bs:]:  # Lo que sigue a BS es relleno.
            raise ValueError("Los bits de relleno no son cero")

        # 4. Decodificar: recorrer el árbol desde la raíz con cada bit válido.
        if isinstance(raiz, int):        # Un solo símbolo: cada bit válido es una copia.
            if any(zip_bytes):
                raise ValueError("El símbolo único debe tener código 0")
            cantidad = (len(zip_bytes) - 1) * 8 + bs
            recuperado = bytes([raiz]) * cantidad
        else:
            nodo = raiz
            for indice, byte in enumerate(zip_bytes, start=1):
                validos = bs if indice == len(zip_bytes) else 8
                for bit in f"{byte:08b}"[:validos]:
                    nodo = nodo[int(bit)]  # 0=izquierda, 1=derecha.
                    if isinstance(nodo, int):
                        recuperado.append(nodo)
                        nodo = raiz
            if nodo is not raiz:
                raise ValueError("ZIP termina a mitad de un código")

    # 5. Guardar el contenido recuperado sin sobrescribir archivos.
    nombre = ruta.name[:-4]
    if not salida and nombre in ("", ".", ".."):
        raise ValueError("El archivo no tiene un nombre original válido")
    destino = Path(salida).expanduser() if salida else ruta.parent / "recuperados" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("xb") as archivo_salida:
        archivo_salida.write(recuperado)

    print(f"Recuperado: {len(recuperado)} bytes")
    print(f"Guardado en: {destino}")
    return destino


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python descomprimir.py archivo.pkz [salida]")
    try:
        descomprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(f"No se pudo descomprimir: {error}")
