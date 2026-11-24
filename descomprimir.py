import sys
from pathlib import Path


def descomprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    if ruta.suffix.lower() not in (".pkz", ".huf"):
        raise ValueError("Selecciona un archivo .pkz o .huf")
    datos = ruta.read_bytes()
    recuperado = bytearray()
    if datos != b"\x00\x00":
        if not datos:
            raise ValueError("El archivo está vacío")
        fin_arbol = 1 + 2 * (2 * datos[0] + 1)
        if len(datos) < fin_arbol + 2 or not 1 <= datos[fin_arbol] <= 8:
            raise ValueError("El archivo comprimido no es válido")

        # Leer el árbol y recuperar los códigos.
        posicion = 1
        codigos = {}
        def leer_arbol(codigo=""):
            nonlocal posicion
            if posicion >= fin_arbol:
                raise ValueError("El árbol está incompleto")
            tipo, byte = datos[posicion:posicion + 2]
            posicion += 2
            if tipo == 1:
                codigos[codigo or "0"] = byte
            elif (tipo, byte) == (0, 0):
                leer_arbol(codigo + "0")
                leer_arbol(codigo + "1")
            else:
                raise ValueError("El árbol no es válido")
        leer_arbol()
        if posicion != fin_arbol or len(set(codigos.values())) != len(codigos):
            raise ValueError("El árbol no coincide con la cabecera")

        # Cambiar los códigos por sus bytes originales.
        bits = "".join(f"{byte:08b}" for byte in datos[fin_arbol + 1:])
        validos = len(bits) - 8 + datos[fin_arbol]
        if "1" in bits[validos:]:
            raise ValueError("El relleno no es válido")
        codigo = ""
        for bit in bits[:validos]:
            codigo += bit
            if codigo in codigos:
                recuperado.append(codigos[codigo])
                codigo = ""
        if codigo:
            raise ValueError("El archivo termina con un código inválido")

    # Guardar el archivo recuperado.
    if not salida and ruta.stem in ("", ".", ".."):
        raise ValueError("El archivo no tiene un nombre válido")
    destino = Path(salida).expanduser() if salida else ruta.parent / "recuperados" / ruta.stem
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("xb") as f:
        f.write(recuperado)
    print(f"Guardado en: {destino}")
    return destino


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python descomprimir.py archivo.pkz [salida]")
    try:
        descomprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(str(error))
