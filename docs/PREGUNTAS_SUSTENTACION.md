# Preguntas probables en la sustentación

Las respuestas describen **lo que hace nuestro código**, con referencias a los archivos donde se puede comprobar. Responde con tus palabras. Si el jurado pide evidencia, abre el archivo indicado.

Abreviaturas: *n* = bytes del archivo; *k* = símbolos distintos (≤ 256).

---

## A. Fundamentos

### 1. ¿Por qué Huffman utiliza un árbol binario?

Porque el código usa dos símbolos, 0 y 1, y cada bit es una decisión entre dos caminos: izquierda o derecha. Si los símbolos se colocan **solo en las hojas**, el camino a una hoja nunca pasa por otra hoja, y eso garantiza que ningún código sea prefijo de otro. Además, el árbol sirve tanto para construir los códigos como para decodificarlos: se sigue el camino bit a bit hasta llegar a una hoja.

### 2. ¿Qué significa que un código esté libre de prefijos?

Que ningún código es el comienzo de otro. En `anita patina`, `n = 00` y `t = 01`: ninguno empieza con el otro. Gracias a eso los bits se pueden concatenar sin separadores, y al leer `00` sabemos con certeza que es una `n`. La prueba `test_prefix_free_codes_for_ties_skew_and_all_bytes` (en `tests/test_properties.py`) lo verifica en alfabetos de hasta 256 símbolos.

### 3. ¿Por qué Huffman es un algoritmo voraz y por qué es óptimo?

Es voraz porque en cada paso une los dos nodos de menor frecuencia y nunca revisa esa decisión. La optimalidad se demuestra con dos propiedades:

- **Elección voraz:** existe un árbol óptimo en el que los dos símbolos menos frecuentes son hermanos en el nivel más profundo. Se prueba intercambiando hojas, y el intercambio no empeora el costo.
- **Subestructura óptima:** al unir esos dos símbolos queda un problema con un símbolo menos, cuyo costo difiere exactamente en *f₁ + f₂*.

Además de la demostración, `test_weighted_path_cost_is_optimal_against_exhaustive_oracle` compara nuestro resultado con un oráculo que prueba **todas** las formas posibles de unir nodos en alfabetos de 2 a 6 símbolos, y siempre coinciden.

### 4. ¿Huffman alcanza el límite teórico de compresión?

Casi. La entropía de Shannon es el mínimo de bits por símbolo, y Huffman cumple `H ≤ L < H + 1`.

| Archivo | Entropía | Huffman | Mínimo teórico |
| --- | --- | --- | --- |
| `anita patina` | 2,418 bits/símbolo | 2,5 bits/símbolo (30 bits) | 29,02 bits |
| Texto de demostración de 7,7 MB | 4,2715 bits/símbolo | 4,3011 bits/símbolo | — |

En el texto de demostración, Huffman queda un 0,7 % por encima del mínimo. No alcanza la entropía exacta porque cada código debe tener un número entero de bits.

## B. Estructuras de datos

### 5. ¿Qué es una cola de prioridad y cuál usamos?

Es una estructura que entrega siempre primero el elemento de mayor prioridad; en nuestro caso, el de **menor frecuencia**. Usamos un **montículo binario mínimo**: una lista de Python organizada con `heapq.heappush` y `heapq.heappop`, de la biblioteca estándar (`pywrap/huffman.py`, `_build_tree`). Insertar y extraer cuestan O(log *k*).

### 6. ¿Implementaron ustedes la cola de prioridad?

**No.** Usamos `heapq`, de la biblioteca estándar. Sí programamos:

- cómo se forma la prioridad;
- el criterio de desempate;
- la construcción del árbol, sus recorridos, la asignación de códigos y el empaquetado de bits;
- la serialización del árbol, la decodificación y el formato.

`heapq` mantiene la propiedad de montículo: cada padre es menor o igual que sus hijos, y el mínimo está en la posición 0. Si la asignatura exigía programar el montículo a mano, sería una mejora pendiente, y podríamos explicar cómo hacerlo con `subir` y `bajar` sobre un arreglo.

### 7. ¿Qué guarda cada elemento de la cola y para qué sirve cada campo?

Una tupla `(frecuencia, byte_mínimo_del_subárbol, contador, nodo)`:

- **Frecuencia:** el criterio principal.
- **Byte mínimo:** desempata. Dos nodos de la cola nunca comparten hojas, así que su byte mínimo siempre es distinto y el desempate es total.
- **Contador:** en la práctica nunca llega a decidir. Evita que Python tenga que comparar dos objetos `Node`, cosa que no sabe hacer.

El primer nodo extraído pasa a ser el hijo izquierdo (0) y el segundo el derecho (1).

### 8. ¿Cómo representan el árbol en memoria?

Con objetos `Node` (`pywrap/huffman.py`), que tienen `frequency`, `symbol`, `left`, `right` y `minimum`. Un nodo es hoja si `symbol` no es `None`. Los nodos internos siempre tienen dos hijos. Para *k* símbolos hay *k* hojas, *k − 1* internos y *2k − 1* nodos en total.

### 9. ¿Cómo se guardan los códigos?

En un diccionario `byte → (valor entero, longitud)` que construye `_codes` con un recorrido en profundidad. Se guardan como enteros y no como texto `"1001"`, porque así se pueden insertar con desplazamientos de bits (`<<`, `|`). Solo la interfaz los convierte a texto para mostrarlos.

## C. Construcción y codificación

### 10. ¿Cómo se construye el árbol?

1. Se crea una hoja por cada byte que aparece, con su frecuencia, y se inserta en la cola.
2. Mientras haya más de un nodo: se extraen los dos menores, se crea un nodo padre con la suma de sus frecuencias y se vuelve a insertar.
3. El último nodo es la raíz.

En `anita patina` las uniones son: espacio + p = 2; ese nodo + i = 4; n + t = 4; el subárbol de espacio, p e i + a = 8; y 4 + 8 = 12.

### 11. ¿Por qué se necesitan los bits de relleno?

Porque el disco guarda bytes completos y la cantidad de bits codificados casi nunca es múltiplo de 8. En `anita patina` hay 30 bits, así que el cuarto byte lleva 2 ceros de relleno. Para que el descompresor no los tome como datos, el campo **BS** indica cuántos bits del último byte son válidos (6 en el ejemplo). Al descomprimir se verifica que el relleno sea cero; si no lo es, el archivo se rechaza.

### 12. ¿Por qué BS va de 1 a 8 y no de 0 a 7?

Porque en un archivo no vacío el último byte siempre tiene al menos un bit válido. Si los bits terminan justo en un límite de byte, `BS = 8` significa «todo el último byte es válido». `BS = 0` está reservado para el archivo vacío.

### 13. ¿Qué pasa con un archivo vacío y con uno de un solo símbolo?

- **Vacío:** no hay árbol. El `.pkz` tiene exactamente 2 bytes: `00 00`, es decir, NF = 0 y BS = 0.
- **Un solo símbolo** (por ejemplo, 17 veces `X`): el árbol es una sola hoja sin camino. Por convención se le da el código `0` de 1 bit, así que cada repetición ocupa un bit. El `.pkz` resultante mide 7 bytes, lo que se comprueba en `tests/fixtures/`.

## D. Formato `.pkz`

### 14. ¿Qué información se almacena en el `.pkz`?

`NF | TREE | BS | ZIP`:

| Campo | Tamaño | Contenido |
| --- | --- | --- |
| NF | 1 byte | Número de nodos internos (0–255). |
| TREE | 2 × (2·NF + 1) bytes | Árbol en preorden: `00 00` es un nodo interno y `01 xx` una hoja con el byte `xx`. |
| BS | 1 byte | Bits válidos del último byte. |
| ZIP | resto del archivo | Los códigos empaquetados. |

**No** se guardan el nombre (se conserva en el nombre externo: `foto.jpg.pkz → foto.jpg`), la longitud original ni un checksum.

### 15. ¿Por qué NF cuenta nodos internos y no hojas?

Porque cabe en un byte. Con 256 valores de byte posibles hay como máximo 256 hojas, que **no** caben en un byte (0–255), pero sí 255 nodos internos. A partir de NF se calcula exactamente cuántos bytes ocupa TREE.

> Esta convención es nuestra. Hay que confirmar con el docente si coincide con la del enunciado.

### 16. ¿Cómo se recupera el árbol?

`_deserialize` (`pywrap/huffman.py`) lee el TREE en el mismo preorden en que se escribió. Si encuentra `01 xx`, crea una hoja. Si encuentra `00 00`, crea un nodo interno y lee de forma recursiva primero el subárbol izquierdo y luego el derecho. El preorden basta porque cada nodo interno tiene exactamente dos hijos. Además valida que:

- no haya etiquetas inválidas;
- no haya hojas repetidas;
- no haya más nodos internos de los que declara NF;
- se consuman exactamente los bytes de TREE.

### 17. ¿Por qué el árbol ocupa 2 bytes por nodo?

Porque es una representación simple y fácil de verificar: un byte de etiqueta y un byte de valor. Existen representaciones más compactas, por ejemplo un bit por nodo interno o códigos canónicos, pero cambiarían el formato. El costo máximo es de 1022 bytes, lo que solo pesa en archivos pequeños.

## E. Descompresión e integridad

### 18. ¿Cómo funciona la descompresión?

Se reconstruye el árbol y se recorre ZIP desde la raíz: con 0 se va a la izquierda y con 1 a la derecha. Al llegar a una hoja se escribe su byte y se vuelve a la raíz. En el último byte solo se leen BS bits. Si la lectura termina a mitad de un código, el archivo se rechaza. Para ZIP de 128 KiB o más se usa una **tabla precalculada** (`pywrap/decoding.py`) que, para cada nodo interno y cada valor de byte, indica qué bytes se emiten y en qué nodo se continúa. Así se procesan 8 bits por consulta.

### 19. ¿Cómo comprobamos que no hay pérdida de información?

De tres formas:

1. **Pruebas automatizadas:** comprimen, descomprimen y comparan **byte a byte y con SHA-256**. Se usan texto, binarios, los 256 valores, archivos vacíos, archivos de un símbolo y archivos de varios MiB.
2. **Archivos reales:** TXT, PDF, JPG, PNG, MP4, un ejecutable y 64 MiB. **Se borró el original antes de descomprimir** y todos se recuperaron idénticos.
3. **En vivo:** `shasum -a 256` y `cmp` sobre el original y el recuperado.

Si los hashes coinciden, la probabilidad de que los archivos sean distintos es despreciable.

### 20. ¿Detecta PyWrap un archivo `.pkz` dañado?

En parte. Detecta encabezados incompletos, árboles inválidos, BS fuera de rango, relleno distinto de cero y códigos incompletos, y en esos casos no crea ningún archivo. Pero **no puede detectar todos los daños**: cambiar un bit de ZIP o truncar el archivo justo en un límite válido produce otro contenido que también es decodificable, porque el formato no guarda un checksum ni la longitud original. Una prueba documenta este límite (`test_payload_corruption_can_be_undetectable_in_this_format`). Al comprimir sí se calcula un SHA-256, pero solo para comprobar que el original no cambió entre las dos lecturas; no se guarda en el `.pkz`.

### 21. ¿Qué pasa si el archivo cambia mientras se comprime?

La compresión lee el archivo dos veces: la primera para contar frecuencias y la segunda para codificar. En ambas calcula un SHA-256. Si los hashes no coinciden, o aparece un byte que no estaba en el árbol, la operación se cancela y no se publica ningún `.pkz`.

## F. Complejidad

### 22. ¿Cuál es la complejidad del algoritmo?

**Compresión, por fases:**

| Fase | Complejidad |
| --- | --- |
| Contar frecuencias | O(*n*) |
| Construir el árbol | O(*k* log *k*): *k − 1* iteraciones, cada una con 2 extracciones y 1 inserción en el montículo |
| Asignar códigos | O(*k*) |
| Serializar el árbol | O(*k*) |
| Codificar | O(*n*) |

**Total:** O(*n* + *k* log *k*), que es O(*n*) porque *k* ≤ 256.

**Descompresión:** reconstruir el árbol cuesta O(*k*), preparar la tabla como máximo 255 × 256 × 8 pasos (una constante) y decodificar O(*n*).

**Espacio:** O(*k*) más búferes fijos de 1 MiB y 256 KiB. **No** depende del tamaño del archivo, porque se procesa por bloques.

### 23. Si las dos rutas de descompresión son O(*n*), ¿por qué una es 16 veces más rápida?

Porque la notación O oculta las constantes. La ruta bit a bit ejecuta en Python unas 8 iteraciones por cada byte de ZIP; la ruta por tabla ejecuta una sola consulta. Las dos son lineales, pero la constante cambia mucho. Medido con 64 MiB: 58,6 s frente a 3,6 s.

### 24. ¿Cuál es la longitud máxima de un código?

En teoría *k − 1* = 255 bits, con un árbol en forma de cadena. En la práctica, para que un código mida *d* bits las frecuencias deben crecer como la sucesión de Fibonacci. Por ejemplo, un código de 39 bits requiere un archivo de unos 268 millones de bytes. El decodificador acepta árboles de profundidad 255, y se probó durante la auditoría.

## G. Resultados y decisiones

### 25. ¿Por qué algunos archivos crecen?

Por dos razones:

1. **El encabezado:** el árbol ocupa hasta 1024 bytes. En `anita patina` los datos bajan de 12 a 4 bytes, pero el total sube a 28.
2. **Datos sin redundancia:** si todos los bytes aparecen con frecuencias parecidas, todos reciben códigos de unos 8 bits y no hay ahorro; el encabezado se suma.

Por eso PyWrap muestra «Crecimiento» en color ámbar en lugar de un porcentaje negativo.

### 26. ¿Qué sucede con archivos PDF, imágenes y videos?

Se procesan como cualquier otro archivo, porque PyWrap trabaja con bytes y no le importa la extensión. Pero JPG, PNG, MP4 y la mayoría de los PDF **ya están comprimidos**, así que sus bytes son casi uniformes. Resultados medidos:

| Formato | Variación |
| --- | ---: |
| PDF | +1,36 % |
| PNG | +0,29 % |
| MP4 | +0,00 % |
| JPG | −0,83 % |

En todos los casos la recuperación fue exacta. En cambio, el texto se redujo un 46 % y un ejecutable un 59 %.

### 27. ¿Por qué se utiliza Python?

- Es legible, lo que ayuda a explicar el algoritmo.
- Su biblioteca estándar trae todo lo necesario (`heapq`, `hashlib`, `tkinter`, `unittest`), así que no hay que instalar nada.
- Funciona en macOS, Windows y Linux.
- Sus enteros de tamaño arbitrario simplifican el acumulador de bits.

La desventaja es la velocidad: el bucle por byte en Python limita la compresión a unos 6 MB/s en nuestra máquina. Por eso optimizamos la descompresión con una tabla.

### 28. ¿Por qué la interfaz no se congela con archivos grandes?

Porque la compresión, la descompresión y el análisis se ejecutan en un **hilo** aparte. El hilo de trabajo envía el resultado a una `queue.Queue`, y el hilo principal la revisa cada 120 ms y es el único que modifica la interfaz, como exige Tkinter. Mientras tanto se desactivan los botones de operación.

### 29. ¿Cómo evitan sobrescribir archivos por accidente?

- La interfaz pide confirmación y la consola exige `--overwrite`.
- Se escribe primero un temporal y solo se publica al terminar sin errores.
- Sin autorización se publica con `os.link`, que falla si el destino ya existe. En exFAT y FAT32 se usa en su lugar una copia con creación exclusiva (`'xb'`).
- Si hay un error, nunca se reemplaza el archivo anterior.

### 30. ¿Qué limitaciones tiene nuestra implementación?

| Limitación | Detalle |
| --- | --- |
| Método | Solo aprovecha frecuencias de bytes sueltos, no secuencias repetidas. No reduce archivos que ya están comprimidos. |
| Formato | No guarda checksum, longitud, firma ni nombre interno, así que no se detectan todos los daños. |
| Estructuras | El montículo y el contador vienen de la biblioteca estándar. |
| Uso | No hay barra de porcentaje ni cancelación. La compresión de archivos muy grandes tarda minutos. |
| exFAT / FAT32 | La publicación por copia no es atómica: un fallo puede dejar un destino parcial, que se avisa. |
| Sin comprobar | Windows, una memoria USB física y la compatibilidad con WinWrap en Java. |

### 31. ¿Es compatible con el WinWrap de Java visto en clase?

No lo sabemos, y no lo afirmamos. Mantenemos la estructura `NF | TREE | BS | ZIP`, pero el preorden, los 2 bytes por nodo, el desempate y el orden de bits son decisiones nuestras. Para comprobarlo necesitaríamos archivos `.pkz` generados por WinWrap.

### 32. Si tuvieran más tiempo, ¿qué mejorarían?

- Añadir al formato una firma, una versión, la longitud original y un checksum.
- Implementar un montículo propio si la asignatura lo exige.
- Añadir progreso y cancelación a la interfaz.
- Acelerar la compresión.
- Probar en Windows.
