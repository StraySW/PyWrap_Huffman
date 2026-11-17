# PyWrap: compresión y descompresión sin pérdida mediante el algoritmo de Huffman

> **Documento histórico de una versión anterior.** Las referencias a tres pestañas, módulos de análisis/decodificación, benchmarks, 59 pruebas y sus mediciones no describen la versión simplificada actual. Para ejecutar y presentar esta copia, usa [README](../README.md), [DEMO](DEMO.md) y el [registro actual](../VALIDACION.md). Las capturas de `docs/screenshots/` también pertenecen a la interfaz anterior.

**Informe académico**

| | |
| --- | --- |
| Institución | Corporación Universitaria Minuto de Dios, UNIMINUTO |
| Programa | Ingeniería de Sistemas |
| Asignatura | Diseño de Algoritmos |
| Integrantes | *[completar]* |
| Docente | *[completar]* |
| Fecha de entrega | *[completar]* |

> Todas las cifras de este informe proceden de ejecuciones reales del código entregado. Cuando un resultado no se pudo comprobar, se indica de forma explícita en la sección 14.

---

## 1. Introducción

PyWrap es una aplicación de escritorio, escrita en Python, que comprime y recupera archivos de cualquier tipo mediante el algoritmo de Huffman. La construcción del árbol, la asignación de códigos, el empaquetado de bits, la serialización del árbol y la decodificación se implementan en el propio proyecto. No se usa ninguna biblioteca de compresión (`zlib`, `gzip`, `zipfile`, etc.).

El sistema tiene tres formas de uso:

- una interfaz gráfica Tkinter con tres pestañas: operaciones, análisis visual del algoritmo y estadísticas;
- una interfaz de consola (`cli.py`);
- una API de Python (`pywrap.compress` y `pywrap.decompress`).

El resultado se guarda en un formato propio `.pkz`, con la estructura `NF | TREE | BS | ZIP`. Este formato contiene todo lo necesario para reconstruir el original sin consultar el archivo de partida.

## 2. Planteamiento del problema

Almacenar y transmitir archivos consume espacio y ancho de banda. En un archivo convencional, cada byte ocupa 8 bits aunque algunos valores aparezcan muchas más veces que otros. Esa redundancia se puede aprovechar: si los símbolos frecuentes usan representaciones más cortas, el total de bits disminuye.

El problema es construir, para un archivo concreto, un código binario que cumpla tres condiciones:

1. **Sin pérdida:** el archivo recuperado debe ser idéntico, byte a byte, al original.
2. **Decodificable sin separadores:** los códigos se concatenan, así que ninguno puede confundirse con el comienzo de otro.
3. **Óptimo:** entre todos los códigos que asignan una secuencia de bits a cada byte, debe minimizar el número total de bits.

Además, el archivo comprimido debe ser autosuficiente: tiene que incluir la información necesaria para decodificarlo.

## 3. Objetivos

### 3.1 Objetivo general

Desarrollar una aplicación en Python que comprima y descomprima archivos sin pérdida de información mediante el algoritmo de Huffman, y que haga visible y verificable el funcionamiento interno del algoritmo.

### 3.2 Objetivos específicos

1. Calcular la tabla de frecuencias de los 256 valores de byte posibles en archivos de cualquier tipo y tamaño, leyéndolos por bloques.
2. Construir el árbol de Huffman mediante una cola de prioridad mínima, con un criterio de desempate determinista.
3. Asignar a cada byte un código libre de prefijos a partir de los recorridos del árbol.
4. Definir e implementar el formato `.pkz` (`NF | TREE | BS | ZIP`), que almacena el árbol, los bits codificados y el relleno.
5. Reconstruir el árbol desde el `.pkz` y recuperar el archivo original, validando la estructura del archivo comprimido.
6. Visualizar la tabla de frecuencias, el árbol, los códigos, los bits y las estadísticas en una interfaz gráfica.
7. Verificar la ausencia de pérdida con pruebas automatizadas que comparan byte a byte y por SHA-256.

## 4. Justificación

Huffman es uno de los ejemplos clásicos de **algoritmo voraz** con demostración de optimalidad. Reúne varios temas centrales de la asignatura: colas de prioridad, árboles binarios, recorridos, análisis de complejidad y representación binaria de la información. Además sigue presente en formatos reales: es una de las etapas de DEFLATE (ZIP, PNG, gzip) y de JPEG.

Implementarlo sobre bytes reales, y no sobre un texto de ejemplo, obliga a resolver problemas que la teoría suele omitir:

- el relleno del último byte;
- el archivo vacío;
- el archivo con un único símbolo;
- la serialización del árbol;
- los archivos dañados;
- los archivos grandes que no caben en memoria.

La interfaz educativa permite mostrar cada paso del algoritmo con datos concretos, y las pruebas automatizadas permiten afirmar con evidencia que el proceso no pierde información.

## 5. Fundamentos del algoritmo de Huffman

### 5.1 Códigos de longitud variable y libres de prefijos

Un código asigna a cada símbolo una cadena de bits. Si las longitudes varían, el decodificador necesita saber dónde termina cada código. Un código es **libre de prefijos** cuando ningún código es el comienzo de otro. Por ejemplo, `{0, 10, 11}` lo es, mientras que `{0, 01, 11}` no lo es, porque `0` es prefijo de `01`. Con un código libre de prefijos, la lectura de izquierda a derecha nunca es ambigua.

Todo código libre de prefijos se puede representar con un **árbol binario**:

- cada símbolo es una hoja;
- el código de un símbolo es el camino desde la raíz hasta su hoja, con 0 para la izquierda y 1 para la derecha;
- como los símbolos están solo en las hojas, ningún camino completo continúa dentro de otro.

### 5.2 Costo de un código

Si el símbolo *i* aparece *fᵢ* veces y su código mide *ℓᵢ* bits, el archivo codificado ocupa:

```text
B = Σ fᵢ · ℓᵢ   bits
```

Huffman encuentra el árbol que minimiza `B`.

### 5.3 Algoritmo

1. Crear una hoja por símbolo, con su frecuencia, e insertarlas en una cola de prioridad mínima.
2. Mientras haya más de un nodo en la cola:
   - extraer los dos nodos de menor frecuencia;
   - crear un nodo interno cuyos hijos sean esos dos y cuya frecuencia sea su suma;
   - insertar el nuevo nodo en la cola.
3. El nodo restante es la raíz.

### 5.4 Por qué es óptimo (esquema de la demostración)

- **Elección voraz:** existe un árbol óptimo en el que los dos símbolos menos frecuentes son hermanos en el nivel más profundo. Si no lo fueran, intercambiarlos con las hojas más profundas no aumenta el costo, porque se mueve un símbolo de menor frecuencia a mayor profundidad.
- **Subestructura óptima:** al unir esos dos símbolos en uno solo de frecuencia *f₁ + f₂*, el costo de cualquier árbol del problema original es el costo del problema reducido más *f₁ + f₂*. Resolver de forma óptima el problema reducido produce entonces una solución óptima del original.

Por inducción sobre el número de símbolos, el árbol de Huffman es óptimo.

### 5.5 Relación con la entropía

La entropía de Shannon `H = −Σ pᵢ · log₂ pᵢ` es el mínimo teórico de bits por símbolo para una fuente sin memoria. Huffman logra una longitud media `L` con `H ≤ L < H + 1`. En el ejemplo `anita patina`, `H = 2,4183` bits/símbolo, de modo que el mínimo teórico son 29,02 bits. Huffman usa 30 bits, es decir, 2,5 bits/símbolo. Una codificación fija de 8 bits por byte usaría 96 bits.

**Observación:** Huffman no aprovecha el orden de los símbolos. Solo usa sus frecuencias, por lo que no reconoce repeticiones de secuencias como lo hacen LZ77 o LZW.

### 5.6 Árboles completos y desigualdad de Kraft

En un árbol de Huffman todo nodo interno tiene exactamente dos hijos. Por eso, para *k* símbolos hay *k* hojas, *k − 1* nodos internos y *2k − 1* nodos en total, y las longitudes cumplen `Σ 2^(−ℓᵢ) = 1`. Las pruebas del proyecto verifican esta igualdad (`tests/test_properties.py`).

## 6. Estructuras de datos utilizadas

Esta sección describe lo que el código usa realmente.

| Estructura | Dónde | Implementación real | Uso |
| --- | --- | --- | --- |
| Tabla de frecuencias | `files._frequencies`, `analysis.analyze_file` | `collections.Counter`, una tabla hash de la biblioteca estándar. Como máximo 256 claves. | Contar cuántas veces aparece cada byte. |
| Cola de prioridad mínima | `huffman._build_tree` | Lista de Python gestionada como **montículo binario** con `heapq.heappush` y `heapq.heappop`, de la biblioteca estándar. | Extraer en cada paso los dos nodos de menor prioridad. |
| Prioridad compuesta | `huffman._build_tree` | Tupla `(frecuencia, byte mínimo del subárbol, contador, nodo)`. | Ordenar y desempatar de forma determinista. |
| Nodo del árbol | `huffman.Node` | `dataclass` con `frequency`, `symbol`, `left`, `right` y `minimum`. Es hoja si `symbol` no es `None`. | Árbol binario enlazado con referencias explícitas. |
| Tabla de códigos | `huffman._codes` | `dict` de `byte → (valor entero, longitud)`. El código se guarda como entero y no como texto. | Codificar cada byte en tiempo constante. |
| Árbol serializado | `huffman._serialize` | `bytearray` en preorden, 2 bytes por nodo. | Campo TREE del `.pkz`. |
| Control de hojas duplicadas | `huffman._deserialize` | `set` de bytes ya vistos. | Validar el árbol leído. |
| Acumulador de bits | `files.compress` | Un entero de Python que crece por la derecha y del que se extraen bytes por la izquierda. | Empaquetar códigos MSB-first. |
| Búferes | `files`, `decoding` | `bytearray` que se vacía al llegar a 256 KiB. Lectura en bloques de 1 MiB. | Memoria acotada con archivos grandes. |
| Autómata de decodificación | `decoding.build_tables` | Lista de nodos internos (recorrido por niveles) y una tabla de `estado × byte → (bytes emitidos, estado siguiente)`. Como máximo 255 × 256 entradas. | Decodificar 8 bits por consulta en ZIP de 128 KiB o más. |
| Comunicación entre hilos | `gui.PyWrapApp` | `queue.Queue`. | Devolver resultados del hilo de trabajo al hilo de la interfaz. |

> **Importante para la evaluación:** la cola de prioridad **no** está implementada desde cero. Se usa el montículo binario de `heapq`, que es parte de la biblioteca estándar de Python, sobre una lista. La tabla de frecuencias usa `Counter`. Lo que sí se implementa en el proyecto es la construcción del árbol, los recorridos, la asignación de códigos, el empaquetado de bits, la serialización y reconstrucción del árbol, la decodificación y el formato de archivo.

### 6.1 Criterio de desempate

Cuando dos nodos tienen la misma frecuencia, decide el **byte mínimo de su subárbol**. Los nodos que están a la vez en la cola tienen hojas disjuntas, así que esos mínimos son siempre distintos. Por eso el contador de la tupla nunca llega a decidir. Solo existe para que Python no tenga que comparar dos objetos `Node`. El primer nodo extraído queda como hijo izquierdo (bit 0) y el segundo como hijo derecho (bit 1). Gracias a esto, el mismo archivo produce siempre el mismo `.pkz`. Una prueba lo comprueba con las 720 permutaciones del orden de inserción de un conjunto de frecuencias empatadas.

## 7. Funcionamiento de la compresión

Código: `compress` en [`pywrap/files.py`](../pywrap/files.py), que usa las funciones de [`pywrap/huffman.py`](../pywrap/huffman.py).

1. **Validación de rutas.** Se resuelve el archivo de entrada y se calcula el destino `<carpeta>/<nombre>.pkz`. Si el destino existe y no se autorizó el reemplazo, la operación se detiene antes de leer nada.
2. **Primera lectura: frecuencias.** Se lee el archivo en bloques de 1 MiB. Cada bloque actualiza el `Counter` y un SHA-256 de control.
3. **Construcción del árbol.** `_build_tree` inserta una hoja por byte distinto, en orden de byte, y combina nodos hasta obtener la raíz. Un archivo vacío no genera árbol.
4. **Tabla de códigos.** `_codes` recorre el árbol en profundidad: añade un 0 al ir a la izquierda y un 1 al ir a la derecha. Si el árbol tiene una sola hoja, se le asigna el código convencional `0` de 1 bit.
5. **Encabezado.** En un archivo temporal de la carpeta de destino se escriben `NF`, `TREE` y un byte reservado para `BS`.
6. **Segunda lectura: codificación.** Para cada byte se obtiene `(código, longitud)` y se acumula: `acc = (acc << longitud) | código`. Mientras haya 8 bits o más, se extrae el byte más significativo. Así los bits quedan ordenados MSB-first.
7. **Relleno y BS.** Si al final quedan *r* bits pendientes (1 ≤ *r* ≤ 7), se completan con ceros y `BS = r`. Si no queda ninguno, `BS = 8`. Después se vuelve a la posición reservada y se escribe `BS`.
8. **Control de cambios.** Se compara el SHA-256 de la primera lectura con el de la segunda. Si el original cambió durante el proceso, se aborta. Este hash **no** se guarda en el `.pkz`.
9. **Publicación segura.** El temporal se publica como destino final:
   - con `os.link` (enlace duro atómico que no reemplaza);
   - si el sistema de archivos no admite enlaces, como exFAT o FAT32, con una copia en modo de creación exclusiva (`'xb'`);
   - con `os.replace` si el usuario autorizó el reemplazo.

   El temporal se elimina siempre en un bloque `finally`.

## 8. Funcionamiento de la descompresión

Código: `decompress` en [`pywrap/files.py`](../pywrap/files.py) y [`pywrap/decoding.py`](../pywrap/decoding.py).

1. **Nombre de salida.** El archivo debe terminar en `.pkz`, y el nombre recuperado es el mismo sin esa extensión (`foto.jpg.pkz → foto.jpg`).
2. **Caso vacío.** Si el archivo mide exactamente 2 bytes y `NF = 0`, `BS` debe ser 0 y se recupera un archivo vacío.
3. **Lectura del árbol.** Se leen exactamente `2 × (2·NF + 1)` bytes y `_deserialize` reconstruye el árbol en preorden. Durante la lectura se valida que:
   - cada nodo sea `00 00` (interno) o `01 xx` (hoja);
   - no haya hojas repetidas;
   - no haya más nodos internos de los declarados;
   - se consuman exactamente los bytes de TREE;
   - el número de hojas sea `NF + 1`.
4. **Lectura de BS.** Debe estar entre 1 y 8, y tiene que existir al menos un byte de ZIP.
5. **Decodificación.** Partiendo de la raíz, cada bit 1 lleva a la derecha y cada bit 0 a la izquierda. Al llegar a una hoja se emite su byte y se vuelve a la raíz. Hay dos implementaciones con el mismo resultado:
   - **Bit a bit** (`_decode_bitwise`), para ZIP de menos de 128 KiB y para árboles de una sola hoja. En este último caso, cada bit 0 produce una repetición del símbolo.
   - **Por tabla** (`decoding.decode_table`), para ZIP de 128 KiB o más. Se precalcula, para cada nodo interno y cada uno de los 256 valores de byte, qué bytes se emiten al consumir esos 8 bits y en qué nodo continúa la lectura. Esto reemplaza ocho pasos por una sola consulta. El último byte se procesa siempre bit a bit para respetar `BS`.
6. **Validación final.** Los bits de relleno deben ser cero y la lectura debe terminar en la raíz. Si termina a mitad de un código, el archivo se rechaza.
7. **Publicación.** Igual que en la compresión. Si hay un error de formato, no se crea ni se reemplaza el destino.

En todo este proceso **no se consulta el archivo original**: el `.pkz` es autosuficiente. Durante la auditoría se comprobó borrando el original antes de descomprimir.

## 9. Ejemplo completo: `anita patina`

Archivo `data/source/anita.txt`: 12 bytes, con espacio y sin salto de línea.

### 9.1 Tabla de frecuencias

| Símbolo | Byte | Frecuencia |
| --- | ---: | ---: |
| espacio | 32 | 1 |
| a | 97 | 4 |
| i | 105 | 2 |
| n | 110 | 2 |
| p | 112 | 1 |
| t | 116 | 2 |
| **Total** | | **12** |

### 9.2 Evolución de la cola de prioridad

Cada elemento se muestra como `(frecuencia, byte mínimo)`.

| Paso | Cola antes de extraer (en orden de prioridad) | Extraídos (izquierda + derecha) | Nuevo nodo |
| --- | --- | --- | --- |
| 1 | ␣(1,32), p(1,112), i(2,105), n(2,110), t(2,116), a(4,97) | ␣ + p | A(2,32) |
| 2 | A(2,32), i(2,105), n(2,110), t(2,116), a(4,97) | A + i | B(4,32) |
| 3 | n(2,110), t(2,116), B(4,32), a(4,97) | n + t | C(4,110) |
| 4 | B(4,32), a(4,97), C(4,110) | B + a | D(8,32) |
| 5 | C(4,110), D(8,32) | C + D | raíz(12,32) |

En el paso 2, `A` e `i` empatan con frecuencia 2 junto con `n` y `t`. Gana `A` porque su byte mínimo, 32, es el menor.

### 9.3 Árbol y códigos

```text
raíz (12)
├── 0: C (4)
│   ├── 0: n (2)          → 00
│   └── 1: t (2)          → 01
└── 1: D (8)
    ├── 0: B (4)
    │   ├── 0: A (2)
    │   │   ├── 0: ␣ (1)  → 1000
    │   │   └── 1: p (1)  → 1001
    │   └── 1: i (2)      → 101
    └── 1: a (4)          → 11
```

| Símbolo | Frecuencia | Código | Bits aportados |
| --- | ---: | --- | ---: |
| ␣ | 1 | 1000 | 4 |
| a | 4 | 11 | 8 |
| i | 2 | 101 | 6 |
| n | 2 | 00 | 4 |
| p | 1 | 1001 | 4 |
| t | 2 | 01 | 4 |
| **Total** | **12** | | **30** |

### 9.4 Codificación y bytes

```text
a  n  i   t  a  ␣    p    a  t  i   n  a
11 00 101 01 11 1000 1001 11 01 101 00 11
```

Secuencia de 30 bits: `110010101111000100111011010011`. Se agrupa en bytes de izquierda a derecha y se rellena con dos ceros:

| Grupo | Binario | Decimal | Hex |
| --- | --- | ---: | --- |
| 1 | 11001010 | 202 | CA |
| 2 | 11110001 | 241 | F1 |
| 3 | 00111011 | 59 | 3B |
| 4 | 010011**00** | 76 | 4C |

El último byte tiene 6 bits válidos, así que `BS = 6`.

### 9.5 Archivo `.pkz` resultante

Salida real de `data/wrp/anita.txt.pkz` (28 bytes):

```text
05 | 00 00 00 00 01 6e 01 74 00 00 00 00 00 00 01 20 01 70 01 69 01 61 | 06 | ca f1 3b 4c
NF | TREE (11 nodos × 2 bytes = 22 bytes, preorden)                    | BS | ZIP
```

El TREE se lee en preorden: raíz, C, n, t, D, B, A, ␣, p, i, a. Los nodos `00 00` son internos y los `01 xx` son hojas (`6e`=n, `74`=t, `20`=␣, `70`=p, `69`=i, `61`=a).

Tamaño total: **1 + 22 + 1 + 4 = 28 bytes**, frente a 12 del original: un **crecimiento del 133,33 %**. Los datos sí se reducen de 12 a 4 bytes, pero el encabezado (24 bytes) pesa más que el ahorro. Con archivos pequeños, el costo de guardar el árbol domina.

### 9.6 Decodificación

Se empieza en la raíz. Los bits `1`, `1` llevan a `a`; se emite `a` y se vuelve a la raíz. Luego `0`, `0` llevan a `n`, y así sucesivamente. Tras el bit 30 la lectura está en la raíz y se ignoran los 2 bits de relleno. El resultado es `anita patina`, con el mismo SHA-256 que el original: `6e07e9bb…14d440`.

## 10. Formato `.pkz`

| Campo | Tamaño | Contenido |
| --- | --- | --- |
| NF | 1 byte | Número de nodos internos, de 0 a 255. |
| TREE | `2 × (2·NF + 1)` bytes | Árbol en preorden. `00 00` es un nodo interno; `01 xx` es una hoja con el byte `xx`. |
| BS | 1 byte | Bits válidos del último byte de ZIP, de 1 a 8. |
| ZIP | resto del archivo | Códigos concatenados MSB-first, con relleno de ceros en los bits menos significativos del último byte. |

Casos especiales:

| Caso | Representación |
| --- | --- |
| Archivo vacío | Exactamente `00 00` (NF = 0, BS = 0), sin TREE ni ZIP. |
| Un solo símbolo | NF = 0, TREE = `01 xx`, un bit `0` por cada repetición. |
| Los 256 valores | NF = 255, TREE = 1022 bytes, 511 nodos. |

- **Tamaño de un archivo no vacío:** `1 + 2·(2·NF + 1) + 1 + ⌈B / 8⌉` bytes.
- **Por qué NF cabe en un byte:** con 256 símbolos posibles hay como máximo 255 nodos internos, así que NF siempre cabe en un byte sin signo. El número de hojas (hasta 256) no cabría.
- **Lo que el formato no guarda:** el nombre original, que se conserva en el nombre externo del archivo; la longitud original; un checksum; una firma o versión; permisos y fechas.

**Decisiones propias:** el preorden, los dos bytes por nodo, el desempate, el orden MSB-first y los casos especiales son decisiones de esta implementación. **No se ha verificado la compatibilidad con WinWrap ni con la convención exacta presentada en clase.**

## 11. Complejidad temporal y espacial

Notación:

- *n*: bytes del archivo original;
- *k*: símbolos distintos (1 ≤ *k* ≤ 256);
- *B*: bits codificados (`Σ fᵢ·ℓᵢ`);
- *P*: bytes de ZIP (`⌈B/8⌉`);
- *h*: altura del árbol.

Dos cotas que se usan en el análisis:

- Como Huffman cumple `L < H + 1` y `H ≤ log₂ 256 = 8`, la longitud media es menor que 9 bits, así que `B < 9n` y *P* = O(*n*).
- La altura es `h ≤ k − 1 ≤ 255`. En la práctica, un código de longitud *d* exige frecuencias que crecen como la sucesión de Fibonacci. Por ejemplo, 40 símbolos con frecuencias de Fibonacci producen un código de 39 bits y requieren un archivo de 267.914.295 bytes.

### 11.1 Compresión

| Fase | Función | Tiempo | Espacio adicional |
| --- | --- | --- | --- |
| Frecuencias + SHA-256 | `_frequencies` | O(*n*) | O(*k*) + bloque de 1 MiB |
| Ordenar símbolos | `sorted(freq)` | O(*k* log *k*) | O(*k*) |
| Construir árbol | `_build_tree`: *k* inserciones y *k−1* iteraciones con 2 extracciones y 1 inserción | O(*k* log *k*) | O(*k*): *2k−1* nodos |
| Tabla de códigos | `_codes`, recorrido en profundidad | O(*k*) | O(*k*) + pila de recursión O(*h*) |
| Serializar árbol | `_serialize`, preorden | O(*k*) | *4k − 2* bytes |
| Codificar + SHA-256 | Segunda lectura en `compress` | O(*n* + *P*) = O(*n*) | Bloque de 1 MiB + búfer de 256 KiB + acumulador de O(*h*) bits |
| **Total** | | **O(*n* + *k* log *k*)**, es decir, O(*n*) porque *k* ≤ 256 | **O(*k*)**, independiente de *n* |

El archivo original se lee **dos veces**. Las fases que dependen de *k* son despreciables frente a las que dependen de *n*, porque *k* está acotado por 256.

### 11.2 Descompresión

| Fase | Función | Tiempo | Espacio adicional |
| --- | --- | --- | --- |
| Encabezado y árbol | `_deserialize`, preorden recursivo | O(*k*) | O(*k*) + pila O(*h*) |
| Ruta bit a bit (ZIP < 128 KiB o una hoja) | `_decode_bitwise` | O(*B*) = O(8*P*) pasos | Búfer de 256 KiB |
| Preparar el autómata (ZIP ≥ 128 KiB) | `build_tables` | O(256 · 8 · (*k*−1)), como máximo unos 522.000 pasos, constante respecto a *n* | O(256 · *k*) entradas. Medido: 4,76 MB de pico con *k* = 256 |
| Ruta por tabla | `decode_table` | O(*P* + *n*): una consulta por byte de ZIP más la escritura de *n* bytes | Bloque + búfer |
| **Total** | | **O(*n* + *k*)**, es decir, O(*n*) | **O(*k*)**, independiente de *n* |

Las dos rutas tienen la misma complejidad asintótica, O(*n*). La diferencia está en la constante: la ruta bit a bit ejecuta en Python unas 8 iteraciones por byte de ZIP, y la ruta por tabla ejecuta una. Esa diferencia explica la aceleración medida de 15 a 16 veces (sección 13).

### 11.3 Análisis visual

`analyze_file` lee el archivo una vez, en O(*n*), y usa las mismas funciones `_build_tree`, `_codes` y `_serialize`. `tree_layout` coloca los *2k−1* nodos en O(*k*). La explicación binaria solo procesa los primeros 64 bytes.

## 12. Arquitectura del software

```text
            main.py (GUI)          cli.py (consola)
                 │                        │
            pywrap/gui.py ──────── pywrap/reporting.py
           ╱      │       ╲
education.py  analysis.py  pywrap/__init__.py  (API pública)
                  │                 │
                  │          pywrap/files.py ──── pywrap/decoding.py
                  │          (E/S, formato,       (autómata de
                  │           publicación)         decodificación)
                  └──────────────┬──┘
                          pywrap/huffman.py
                 (Node, heap, códigos, serialización, FormatError)
```

| Módulo | Responsabilidad |
| --- | --- |
| `huffman.py` | Núcleo del algoritmo sin acceso a disco: `Node`, `_build_tree`, `_codes`, `_serialize`, `_deserialize`, `Result` y `FormatError`. Conserva `compress` y `decompress` como API, que delegan en `files.py`. |
| `files.py` | Lectura por bloques, escritura de `NF | TREE | BS | ZIP`, validación del formato, decodificación bit a bit y publicación segura (enlace duro, copia exclusiva o reemplazo). |
| `decoding.py` | Autómata de decodificación por byte para ZIP grandes. |
| `analysis.py` | Modelo de solo lectura para la interfaz: frecuencias, códigos, estadísticas, explicación binaria y posiciones del árbol. Reutiliza las funciones del compresor, así que no hay una segunda implementación de Huffman. |
| `education.py` | Vistas Tkinter: tabla, árbol en `Canvas`, bits y bytes, y gráfica de tamaños. |
| `gui.py` | Ventana principal. Las operaciones y los análisis se ejecutan en un hilo; los resultados llegan por `queue.Queue` y solo el hilo principal modifica los widgets. |
| `reporting.py` | Texto de estadísticas, compartido por la interfaz gráfica y la consola. |
| `cli.py` / `main.py` | Puntos de entrada. `main.py` detecta antes de abrir la ventana si falta Tkinter o si macOS tiene Tk 8.5. |

Decisiones de diseño:

- El algoritmo está separado de la E/S.
- La interfaz no implementa lógica de compresión.
- No hay dependencias externas: solo la biblioteca estándar.
- Por defecto nunca se sobrescribe. La interfaz pide confirmación y la consola exige `--overwrite`.

## 13. Pruebas y resultados

### 13.1 Suite automatizada

Comando: `python3 -m unittest discover -s tests -v`.

| Archivo | Pruebas | Qué verifica |
| --- | ---: | --- |
| `test_huffman.py` | 8 | Ejemplo de clase, vacío, un símbolo, 256 símbolos, binario, UTF-8 y errores básicos. |
| `test_files.py` | 14 | Varios bloques, ciclos repetidos, límites de BS, protección contra sobrescritura, cambios del original, estructuras inválidas, truncados y CLI. |
| `test_properties.py` | 4 | Optimalidad frente a un oráculo exhaustivo, ausencia de prefijos y Kraft, independencia del orden con empates, y 60 archivos con semilla. |
| `test_decoding.py` | 7 | Ruta por tabla frente a la ruta bit a bit en ZIP arbitrarios, códigos largos que cruzan bytes y bloques, archivos mutados y truncados. |
| `test_publish.py` | 11 | Sistemas sin enlaces duros simulados, errores de permisos y espacio, carreras, enlaces simbólicos y limpieza de temporales. |
| `test_analysis.py` | 10 | Tabla, códigos, estadísticas, muestra de bits y compatibilidad con los cuatro `.pkz` de referencia. |
| `test_gui.py` | 5 | Integración con Tk real: pestañas, árbol, hilo de análisis y operaciones. |
| **Total** | **59** | |

Resultados de la revisión final (14/11/2026):

- Python 3.15.2 con Tk 9.0.5 en macOS: **59 aprobadas, 0 fallos, 0 omitidas** (≈ 5,7 s).
- Python 3.9.6 de Apple: **59 ejecutadas, 0 fallos, 5 omitidas**. Las omitidas son las de GUI, porque ese Python trae Tk 8.5.

### 13.2 Archivos reales (ida y vuelta)

En cada caso se comprimió, **se eliminó el original**, se descomprimió y se comparó byte a byte y por SHA-256 con una copia de referencia. Los archivos provienen del sistema operativo o se generaron con semilla; no se usaron archivos personales. Python 3.15.2, macOS ARM64.

| Tipo | Original | `.pkz` | Variación | Comprimir | Descomprimir | ¿Idéntico? |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TXT UTF-8 | 3.169.842 B | 1.707.828 B | −46,12 % | 0,5 s | 0,1 s | Sí |
| PDF | 68.521 B | 69.450 B | +1,36 % | <0,1 s | 0,1 s | Sí |
| JPG | 5.617.703 B | 5.570.864 B | −0,83 % | 1,0 s | 0,4 s | Sí |
| PNG | 351.198 B | 352.222 B | +0,29 % | 0,1 s | 0,1 s | Sí |
| MP4 | 12.130.124 B | 12.130.304 B | +0,00 % | 2,1 s | 0,8 s | Sí |
| Ejecutable | 154.624 B | 64.011 B | −58,60 % | <0,1 s | 0,1 s | Sí |
| Los 256 valores (1 MiB) | 1.048.576 B | 1.049.600 B | +0,10 % | 0,2 s | 0,1 s | Sí |
| Aleatorio | 5.242.880 B | 5.243.904 B | +0,02 % | 0,9 s | 0,3 s | Sí |
| Binario de 64 MiB | 67.108.864 B | 67.109.888 B | +0,00 % | 10,9 s | 3,6 s | Sí |

Interpretación:

- El texto y los ejecutables tienen distribuciones de bytes muy desiguales, y Huffman reduce su tamaño.
- PDF, JPG, PNG y MP4 ya están comprimidos internamente: sus bytes son casi uniformes y Huffman no puede mejorarlos. Incluso crecen ligeramente por el encabezado de hasta 1024 bytes.

### 13.3 Archivo de demostración reproducible

El archivo `data/source/demo_grande.txt` se genera con semilla, según `docs/DEMO.md`: 7.723.775 bytes y 25 símbolos.

| Python | Comprimir | Descomprimir | Resultado |
| --- | ---: | ---: | --- |
| 3.15.2 | 1,13 s | 0,28 s | 4.152.648 B (−46,24 %), SHA-256 idéntico |
| 3.9.6 | 2,33 s | 0,53 s | Mismo `.pkz`, SHA-256 idéntico |

En este archivo la entropía es de 4,2715 bits/símbolo y Huffman logra 4,3011, solo un 0,7 % por encima del mínimo teórico.

### 13.4 Rendimiento de la descompresión antes y después del autómata

Medianas de tres repeticiones, según [`benchmarks/README.md`](../benchmarks/README.md):

| Caso | Bit a bit | Por tabla | Factor |
| --- | ---: | ---: | ---: |
| Uniforme, 64 MiB | 58,59 s | 3,56 s | 16,44× |
| Texto UTF-8, 8 MiB | 4,14 s | 0,27 s | 15,09× |
| Un símbolo, 8 MiB | 0,77 s | 0,76 s | Sin cambio: misma ruta bit a bit |

Ahora la fase más lenta es la compresión, de unos 6 MB/s en esta máquina, porque procesa cada byte en Python.

### 13.5 Sistemas de archivos de memorias USB

Con imágenes de disco exFAT y FAT32 montadas en macOS, `os.link` falla con el error 45 (*Operation not supported*). PyWrap usa entonces la copia exclusiva. Con un archivo de 262.412 bytes, la recuperación fue exacta, se rechazó la sobrescritura y no quedaron temporales ([`filesystem-validation.json`](filesystem-validation.json)).

### 13.6 Robustez del decodificador

Durante la auditoría se descomprimieron 6000 archivos `.pkz` mutados al azar:

- todos terminaron en `FormatError` o en una descompresión válida;
- ninguno produjo otro tipo de excepción;
- ninguno dejó temporales.

## 14. Limitaciones

### 14.1 Del método

- Huffman solo aprovecha frecuencias de bytes individuales, no repeticiones de secuencias. No reduce archivos que ya están comprimidos (JPG, MP4, PDF, ZIP).
- El árbol ocupa hasta 1024 bytes, así que los archivos pequeños crecen. `anita patina` pasa de 12 a 28 bytes.

### 14.2 Del formato

- No guarda checksum, longitud original, firma ni versión. Algunos daños no se detectan: un bit cambiado en ZIP, ciertos truncados o ceros añadidos al final pueden producir otro contenido aceptado. La única verificación fiable es comparar el SHA-256 con el del original.
- El nombre original depende del nombre externo del `.pkz`: si se renombra el `.pkz`, cambia el nombre recuperado.

### 14.3 De la implementación

- La cola de prioridad y la tabla de frecuencias usan `heapq` y `Counter` de la biblioteca estándar, no estructuras propias.
- No se puede cancelar una operación en curso, y la interfaz no muestra un porcentaje de avance.
- La compresión lee el archivo dos veces y avanza a unos 6 MB/s en Python puro. Un video de 1 GB tardaría varios minutos.
- En exFAT y FAT32 la publicación se hace por copia. El nombre se reserva de forma atómica, pero la copia no es atómica: si falla a mitad, puede quedar un destino parcial, que PyWrap avisa y no borra.

### 14.4 Estado de las comprobaciones

| Aspecto | Estado |
| --- | --- |
| Algoritmo, formato e igualdad byte a byte | **Comprobado:** 59 pruebas y archivos reales. |
| Interfaz gráfica en macOS (Python 3.15, Tk 9.0.5) | **Comprobado:** pruebas con Tk real y revisión visual. |
| Núcleo y consola con Python 3.9 | **Comprobado.** La GUI no funciona con el Tk 8.5 de Apple. |
| exFAT / FAT32 | **Comprobado** con imágenes de disco. **Pendiente:** memoria USB física. |
| Windows | **Pendiente.** Solo se usan bibliotecas multiplataforma, pero no se ejecutó en Windows. |
| Compatibilidad con WinWrap / Java | **Pendiente:** no hubo archivos de referencia. |
| Convención exacta de NF y TREE del enunciado | **Por confirmar** con el docente. |

## 15. Conclusiones

1. El algoritmo de Huffman implementado produce códigos óptimos y libres de prefijos. Se comprobó frente a un oráculo exhaustivo en alfabetos pequeños y con la igualdad de Kraft en alfabetos de hasta 256 símbolos.
2. La compresión es sin pérdida: todos los archivos probados, incluidos texto, PDF, imágenes, video, ejecutables y 64 MiB de datos, se recuperaron idénticos byte a byte y por SHA-256, sin consultar el original.
3. El rendimiento depende tanto de la complejidad asintótica como de la constante. Las dos rutas de decodificación son O(*n*), pero cambiar 8 pasos por bit por una consulta por byte aceleró la descompresión unas 16 veces.
4. El tamaño final depende del tipo de archivo: Huffman reduce texto y ejecutables a la mitad, pero no mejora formatos que ya están comprimidos, y en archivos muy pequeños el encabezado domina.
5. Separar el algoritmo, la E/S y la interfaz permitió probar cada parte por separado y reutilizar exactamente el mismo código en la vista educativa.
6. Como trabajo futuro: incluir longitud y checksum en el formato, implementar una cola de prioridad propia si se requiere y añadir progreso y cancelación a la interfaz.

## Referencias

- Huffman, D. A. (1952). A Method for the Construction of Minimum-Redundancy Codes. *Proceedings of the IRE*, 40(9), 1098–1101.
- Shannon, C. E. (1948). A Mathematical Theory of Communication. *Bell System Technical Journal*, 27, 379–423, 623–656.
- Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. *Introduction to Algorithms*. MIT Press. Capítulo sobre algoritmos voraces: códigos de Huffman.
- Documentación oficial de Python: módulos `heapq`, `collections`, `hashlib` y `tkinter`.
