"""Uso: python3 descomprimir.py archivo.pkz [salida]. No necesita el original."""
import sys
from pathlib import Path


def descomprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser().resolve()
    if ruta.suffix.lower() not in ('.pkz', '.huf'):
        raise ValueError('Selecciona un archivo .pkz o .huf de Huffman.')
    nombre = ruta.name[:-4]
    if nombre in ('', '.', '..'):
        raise ValueError('El archivo no tiene un nombre original válido.')
    datos = ruta.read_bytes()
    if len(datos) < 2:
        raise ValueError('Archivo incompleto: faltan NF y BS.')

    recuperado = bytearray()
    if datos != b'\x00\x00':  # Dos ceros representan el archivo vacío.
        nf = datos[0]
        fin_arbol = 1 + 2 * (2 * nf + 1)
        if len(datos) <= fin_arbol + 1:
            raise ValueError('Archivo incompleto: falta el árbol, BS o ZIP.')
        posicion = 1
        internos = 0
        simbolos = set()

        # 1. Reconstruir el árbol guardado en preorden.
        def leer_arbol():
            nonlocal posicion, internos
            if posicion + 2 > fin_arbol:
                raise ValueError('El árbol está incompleto.')
            tipo, valor = datos[posicion:posicion + 2]
            posicion += 2
            if tipo == 1:
                if valor in simbolos:
                    raise ValueError('El árbol repite un símbolo.')
                simbolos.add(valor)
                return valor
            if tipo != 0 or valor != 0:
                raise ValueError('El árbol contiene una etiqueta inválida.')
            internos += 1
            if internos > nf:
                raise ValueError('El árbol no coincide con NF.')
            return (leer_arbol(), leer_arbol())

        raiz = leer_arbol()
        if posicion != fin_arbol or internos != nf or len(simbolos) != nf + 1:
            raise ValueError('El árbol no coincide con NF.')
        bs = datos[fin_arbol]
        if not 1 <= bs <= 8:
            raise ValueError('BS debe estar entre 1 y 8.')
        zip_bytes = datos[fin_arbol + 1:]
        if zip_bytes[-1] & ((1 << (8 - bs)) - 1):
            raise ValueError('Los bits de relleno deben ser cero.')

        # 2. Seguir los bits: izquierda=0, derecha=1. Una hoja emite un byte.
        if isinstance(raiz, int):
            if any(zip_bytes):
                raise ValueError('Un símbolo único debe usar el código 0.')
            recuperado.extend(bytes((raiz,)) * ((len(zip_bytes) - 1) * 8 + bs))
        else:
            nodo = raiz
            for indice, byte in enumerate(zip_bytes):
                validos = bs if indice == len(zip_bytes) - 1 else 8
                for bit in format(byte, '08b')[:validos]:
                    nodo = nodo[int(bit)]
                    if isinstance(nodo, int):
                        recuperado.append(nodo)
                        nodo = raiz
            if nodo is not raiz:
                raise ValueError('ZIP termina en medio de un código.')

    # 3. Crear la salida solo después de validar y decodificar el archivo.
    destino = (Path(salida).expanduser() if salida else
               ruta.parent / 'recuperados' / nombre)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open('xb') as archivo_salida:
        archivo_salida.write(recuperado)
    print(f'Recuperado: {len(recuperado)} bytes')
    print(f'Guardado en: {destino}')
    return destino


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        sys.exit('Uso: python3 descomprimir.py archivo.pkz [salida]')
    try:
        descomprimir(*sys.argv[1:])
    except FileExistsError:
        sys.exit('Error: la salida ya existe. Elige otro nombre; no se reemplazó.')
    except (OSError, ValueError) as error:
        sys.exit(f'No se pudo descomprimir: {error}')
