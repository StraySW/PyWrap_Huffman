# Cómo explicar PyWrap

## La idea en una frase

Huffman da códigos cortos a los bytes más frecuentes para intentar guardar el mismo contenido con menos bits.

## Qué hace cada archivo

| Archivo | Función |
| --- | --- |
| `main.py` | Abre la aplicación. |
| `pywrap/gui.py` | Permite elegir un archivo y pulsar Comprimir o Descomprimir. |
| `pywrap/huffman.py` | Hace todo el trabajo del algoritmo y los archivos. |
| `cli.py` | Permite hacer lo mismo desde una terminal, si se necesita. |

## Comprimir, en cinco pasos

1. **Contar.** `compress` lee bloques de 64 KiB y `Counter` cuenta cuántas veces aparece cada byte.
2. **Construir el árbol.** `_build_tree` usa `heapq` como cola de prioridad: saca los dos nodos menos frecuentes, los une y repite hasta que queda una raíz.
3. **Asignar códigos.** `_codes` recorre el árbol: izquierda es 0 y derecha es 1. El camino hasta una hoja es el código de su byte.
4. **Guardar el árbol.** `_serialize` escribe los nodos en preorden: primero el nodo, después su hijo izquierdo y luego el derecho.
5. **Escribir los datos.** Se vuelve al inicio del original, se sustituye cada byte por su código y se juntan los bits de ocho en ocho para escribirlos.

Por ejemplo, en `aaaaabbc` las frecuencias son a=5, b=2 y c=1. Se unen c y b, y luego ese grupo con a. En esta implementación los códigos quedan a=`1`, b=`01` y c=`00`: el byte más frecuente tiene el código más corto.

## Descomprimir

`decompress` lee el árbol guardado y lo reconstruye con `_deserialize`. Después sigue los bits: 0 va a la izquierda y 1 a la derecha. Cada vez que llega a una hoja, escribe su byte y vuelve a la raíz. No necesita el archivo original.

## Qué contiene un `.pkz`

`NF | TREE | BS | ZIP`

- **NF:** número de nodos internos del árbol, en 1 byte.
- **TREE:** árbol guardado en preorden; cada nodo ocupa 2 bytes.
- **BS:** cantidad de bits válidos del último byte de datos, en 1 byte.
- **ZIP:** contenido codificado con Huffman; no es el formato ZIP comercial.

Los bits que falten para completar el último byte se rellenan con cero. BS permite ignorar ese relleno. Un archivo vacío se guarda como dos ceros; si solo hay un byte distinto, se usa el código `0`.

## Por qué admite cualquier tipo y archivos grandes

Trabaja con los valores de byte de 0 a 255: no interpreta si el archivo es texto, imagen, video o PDF. Al recuperar escribe exactamente esos bytes. Procesa bloques pequeños y mantiene como máximo 256 símbolos en la tabla de frecuencias. No hay un límite de tamaño fijado por el programa, aunque hacen falta espacio en disco y tiempo.

La ventana usa un hilo para el trabajo y una cola para recibir el resultado. Así sigue respondiendo mientras se procesa un archivo grande. Solo el hilo principal modifica la ventana.

## Qué protecciones se conservan

`_operation` abre el original, prepara un archivo temporal y lo limpia al terminar. `_publish` coloca la salida definitiva después de completar la operación. No se borra antes el destino; reemplazarlo requiere autorización. Se rechazan encabezados, árboles y bits inválidos que el formato permita detectar. El formato no tiene checksum: no detecta todas las alteraciones posibles.

## Demostración rápida

Abre la aplicación, comprime `data/source/anita.txt` y descomprime el `.pkz` generado. Abre el recuperado en `data/unwrp/`: vuelve a contener `anita patina`.

Ese ejemplo ocupa 12 bytes originalmente y 28 comprimido porque guardar el árbol cuesta espacio. Que la recuperación sea exacta no significa que todos los archivos se reduzcan.
