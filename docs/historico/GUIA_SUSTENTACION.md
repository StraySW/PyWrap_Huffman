# Guía de sustentación de PyWrap (10–15 minutos)

> **Documento histórico de una versión anterior.** Las referencias a tres pestañas, módulos de análisis/decodificación, benchmarks, 59 pruebas y sus mediciones no describen la versión simplificada actual. Para ejecutar y presentar esta copia, usa [README](../README.md), [DEMO](DEMO.md) y el [registro actual](../VALIDACION.md). Las capturas de `docs/screenshots/` también pertenecen a la interfaz anterior.

Esta guía no es un guion para memorizar. Cada bloque tiene:

- la **idea clave** que debes poder decir con tus propias palabras;
- **qué mostrar** en pantalla;
- **cómo comprobar que lo entiendes**: si puedes responder sin mirar, estás listo.

Los pasos técnicos de la demostración están en [DEMO.md](DEMO.md). Las preguntas probables del jurado están en [PREGUNTAS_SUSTENTACION.md](PREGUNTAS_SUSTENTACION.md). El detalle formal está en [INFORME_ACADEMICO.md](INFORME_ACADEMICO.md).

## Mapa de tiempos

| # | Bloque | Tiempo | Acumulado |
| --- | --- | ---: | ---: |
| 1 | Introducción al proyecto | 1:00 | 1:00 |
| 2 | Huffman explicado de forma sencilla | 1:30 | 2:30 |
| 3 | Tabla de frecuencias | 1:00 | 3:30 |
| 4 | Construcción y recorrido del árbol | 2:00 | 5:30 |
| 5 | Codificación y generación de bytes | 1:30 | 7:00 |
| 6 | Encabezado `.pkz` | 1:30 | 8:30 |
| 7 | Descompresión | 1:00 | 9:30 |
| 8 | Demostración práctica | 2:30 | 12:00 |
| 9 | Pruebas y rendimiento | 1:00 | 13:00 |
| 10 | Conclusiones y limitaciones | 1:00 | 14:00 |

Si te quedan menos de 10 minutos, reduce los bloques 6 y 9 a una frase cada uno y conserva la demostración. Si son varios integrantes, una división natural es: bloques 1–3, bloques 4–7 y bloques 8–10.

**Antes de empezar:** ten PyWrap abierto en la pestaña **Análisis de Huffman** y una terminal en la carpeta del proyecto (ver «Preparación» en DEMO.md).

---

## 1. Introducción al proyecto (1:00)

**Idea clave:** PyWrap comprime cualquier archivo sin perder un solo bit, usando Huffman implementado por nosotros, y además muestra paso a paso cómo funciona el algoritmo.

**Qué decir, con tus palabras:**

- Es un proyecto de Diseño de Algoritmos en Python.
- Trabaja con bytes, así que sirve para texto, PDF, imágenes, video o cualquier otro archivo.
- Tiene una interfaz gráfica, una consola y 59 pruebas automatizadas.
- Guarda el resultado en un formato propio `.pkz`.

**Qué mostrar:** la ventana principal y sus tres pestañas.

**Comprueba que lo entiendes:** ¿qué significa «sin pérdida»? Que el archivo recuperado es idéntico byte a byte al original; no se parece, es igual.

## 2. Huffman explicado de forma sencilla (1:30)

**Idea clave:** si un símbolo aparece mucho, conviene darle un código corto; si aparece poco, uno largo. Así el total de bits baja.

**Una analogía útil:** en el código Morse, la E, que es la letra más usada en inglés, es un solo punto. Huffman hace lo mismo, pero calcula la asignación óptima para cada archivo.

**Los tres conceptos que sostienen todo:**

1. **Frecuencia:** cuántas veces aparece cada byte.
2. **Árbol binario:** los símbolos son hojas y el camino desde la raíz es su código, con 0 a la izquierda y 1 a la derecha.
3. **Libre de prefijos:** como los símbolos solo están en las hojas, ningún código es el inicio de otro. Por eso se pueden pegar los bits sin separadores.

**Comprueba que lo entiendes:**

- ¿Por qué no sirve el código {a = 0, b = 01}? Porque al leer `0` no sabes si ya es `a` o si es el comienzo de `b`.
- ¿Por qué Huffman es «voraz»? Porque en cada paso toma la decisión que parece mejor en ese momento (unir los dos nodos menos frecuentes) y nunca la deshace, y aun así se demuestra que el resultado es óptimo.

## 3. Tabla de frecuencias (1:00)

**Qué mostrar:** pulsa **Ejemplo: anita patina**. Se abre la subpestaña **Frecuencias y códigos**.

**Qué señalar:**

- Son 12 bytes y 6 símbolos. El **espacio** también es un símbolo.
- La `a` aparece 4 veces; `i`, `n` y `t`, 2 veces cada una; el espacio y la `p`, una vez.
- La columna «Bits totales» es frecuencia × longitud del código, y su suma da **30 bits**.

**Cómo se hace en el código:** se lee el archivo en bloques de 1 MiB y se cuenta con un `Counter` (`files._frequencies`). Hay como máximo 256 entradas, una por valor de byte posible.

**Comprueba que lo entiendes:** ¿por qué hablamos de bytes y no de letrasí Porque en UTF-8 una `ñ` ocupa 2 bytes. PyWrap no interpreta texto: cuenta bytes, y por eso sirve para cualquier tipo de archivo.

## 4. Construcción y recorrido del árbol (2:00)

**Qué mostrar:** la subpestaña **Árbol binario**. Haz doble clic en la fila de `p` dentro de la tabla para resaltar su camino.

**Explica la cola de prioridad mientras señalas el árbol:**

1. La cola de prioridad mínima siempre entrega primero el nodo de menor frecuencia. Usamos un montículo binario de `heapq`.
2. Se sacan los dos menores, espacio (1) y `p` (1), y se unen en un nodo de frecuencia 2.
3. Ese nodo se une con `i` (2): resulta un nodo de 4.
4. `n` + `t` dan otro nodo de 4.
5. El subárbol de espacio, `p` e `i` se une con `a`: resulta 8.
6. Por último, 4 + 8 = 12, que es la raíz y coincide con el total de bytes.

**Empates:** cuando dos nodos tienen la misma frecuencia, gana el que contiene el byte de menor valor. El primero que sale de la cola va a la izquierda (0). Por eso el resultado siempre es el mismo.

**Recorrido:** el camino a `p` es derecha, izquierda, izquierda, derecha = `1001`. El de `a` es derecha, derecha = `11`.

**Comprueba que lo entiendes:**

- ¿Cuántos nodos tiene el árbol? Hay 6 hojas y 5 internos: 11 en total. En general, *k* hojas dan *k − 1* internos.
- ¿Por qué `a` tiene el código más corto? Porque es el símbolo más frecuente y se une al final, así que queda cerca de la raíz.
- ¿Qué valor tiene un nodo interno? La suma de las frecuencias de sus hijos.

## 5. Codificación y generación de bytes (1:30)

**Qué mostrar:** la subpestaña **Bits y bytes**.

**Explica la secuencia:**

1. Se reemplaza cada letra por su código: `11 00 101 01 11 1000 1001 11 01 101 00 11`, en total **30 bits**.
2. Se agrupan en bytes de 8 bits: `11001010 | 11110001 | 00111011 | 010011__`.
3. Al último byte le faltan 2 bits y se rellena con ceros: `01001100`.
4. Los valores resultantes son `[202, 241, 59, 76]`: 4 bytes en lugar de 12.

**Cómo se hace en el código:** un acumulador entero recibe cada código por la derecha (`acc = (acc << longitud) | código`). En cuanto tiene 8 bits, saca el byte más significativo (MSB-first).

**Comprueba que lo entiendes:** ¿por qué hace falta relleno? Porque los archivos se guardan en bytes completos y 30 no es múltiplo de 8. ¿Y cómo sabe el descompresor que esos 2 ceros no son datos? Por el campo BS, que es el siguiente bloque.

## 6. Encabezado `.pkz` (1:30)

**Qué mostrar:** la parte inferior de **Bits y bytes** (TREE en hexadecimal) o la salida de la terminal (ver DEMO.md, paso 4).

```text
05 | 00 00 00 00 01 6e 01 74 00 00 00 00 00 00 01 20 01 70 01 69 01 61 | 06 | ca f1 3b 4c
NF |                         TREE (22 bytes)                            | BS |   ZIP
```

**Explica cada campo:**

- **NF = 5:** número de nodos internos. Con este dato se sabe cuántos bytes ocupa el árbol: 2 × (2·5 + 1) = 22.
- **TREE:** el árbol en preorden, es decir, nodo, luego subárbol izquierdo y luego subárbol derecho. `00 00` es un nodo interno; `01 xx` es una hoja con el byte `xx` (`6e` = n, `74` = t…).
- **BS = 6:** cuántos bits del último byte son datos reales.
- **ZIP:** los 4 bytes codificados.

**El dato que sorprende:** el total es 1 + 22 + 1 + 4 = **28 bytes** frente a los 12 originales, un crecimiento del 133 %. Los datos sí se comprimen (de 12 a 4 bytes), pero el árbol es más grande que el ahorro. En archivos grandes ocurre lo contrario (bloque 8).

**Comprueba que lo entiendes:** ¿por qué hay que guardar el árbol? Porque los códigos son distintos para cada archivo y sin el árbol el descompresor no puede interpretar los bits.

## 7. Descompresión (1:00)

**Idea clave:** el árbol funciona como un mapa. Se lee bit a bit desde la raíz: con 0 se va a la izquierda y con 1 a la derecha. Al llegar a una hoja se escribe su byte y se vuelve a la raíz.

**Qué decir:**

1. Se lee NF y se reconstruye el árbol desde TREE, validando su estructura.
2. Se lee BS.
3. Se recorre ZIP. En el último byte solo se usan BS bits.
4. Si el archivo está dañado (árbol inválido, relleno distinto de cero, código cortado), se rechaza y no se crea ningún archivo.

**Mejora de rendimiento:** en archivos grandes se usa una tabla precalculada que procesa 8 bits de una vez. El resultado es el mismo y es unas 16 veces más rápido.

**Comprueba que lo entiendes:** ¿necesita el descompresor el archivo original? No. Todo lo necesario está en el `.pkz`. Lo comprobamos borrando el original antes de descomprimir.

## 8. Demostración práctica (2:30)

Sigue los pasos 4 a 7 de [DEMO.md](DEMO.md):

1. Comprimir `data/source/anita.txt` desde la pestaña **Comprimir / Descomprimir**. Señala en las tarjetas: 12 B, 28 B y el crecimiento en ámbar.
2. Descomprimir `data/wrp/anita.txt.pkz`.
3. En la terminal, comparar con `shasum -a 256` y `cmp`: los hashes coinciden.
4. Archivo grande (7,7 MB de texto generado): se reduce un **46 %** y se recupera idéntico en menos de 1 segundo.

**Qué decir mientras se ejecuta:** «el mismo algoritmo que crece con 12 bytes reduce casi a la mitad un texto grande, porque el árbol cuesta lo mismo y el ahorro crece con el archivo».

## 9. Pruebas y rendimiento (1:00)

**Datos que debes conocer:**

- **59 pruebas automatizadas** aprobadas. Comprueban:
  - igualdad byte a byte y SHA-256;
  - optimalidad frente a un oráculo que prueba todas las combinaciones posibles en alfabetos pequeños;
  - que ningún código sea prefijo de otro;
  - archivos dañados;
  - casos límite: archivo vacío, un solo símbolo y los 256 valores;
  - la interfaz real.
- **Archivos reales:** TXT, PDF, JPG, PNG, MP4, ejecutable y 64 MiB, todos recuperados de forma idéntica.
- **Rendimiento:** descomprimir 64 MiB pasó de 58,6 s a 3,6 s (16,4×).
- **Memorias USB:** exFAT y FAT32 funcionan; se comprobó con imágenes de disco.

**Comprueba que lo entiendes:** ¿por qué un MP4 casi no cambia de tamaño? Porque ya viene comprimido: sus bytes están repartidos de forma casi uniforme y no hay símbolos frecuentes que aprovechar.

## 10. Conclusiones y limitaciones (1:00)

**Tres conclusiones:**

1. Huffman es un algoritmo voraz que produce el código libre de prefijos óptimo, y lo comprobamos con pruebas.
2. La compresión es sin pérdida en todos los tipos de archivo probados.
3. El resultado depende de los datos: con texto se ahorra mucho; con archivos ya comprimidos o muy pequeños, nada o incluso se crece.

**Limitaciones, dichas con honestidad (esto suma puntos):**

- La cola de prioridad usa `heapq` de la biblioteca estándar y no está programada desde cero.
- El formato no guarda un checksum: no detecta todos los daños, y la integridad se verifica con SHA-256 aparte.
- Windows, una memoria USB física y la compatibilidad con WinWrap en Java no se han probado.
- No hay barra de porcentaje ni botón para cancelar una operación.

**Cierre sugerido:** «PyWrap demuestra que un algoritmo de 1952 sigue siendo óptimo para lo que promete, y también deja ver con datos reales dónde están sus límites».

---

## Autoevaluación antes de presentar

Explica cada punto en voz alta, en menos de 30 segundos y sin mirar:

- [ ] Por qué un código libre de prefijos no necesita separadores.
- [ ] Los 5 pasos de unión del ejemplo `anita patina`.
- [ ] Por qué `anita patina` crece y el texto grande se reduce.
- [ ] Qué contienen NF, TREE, BS y ZIP, y por qué cada uno es necesario.
- [ ] Qué pasa con un archivo vacío y con uno que tiene un solo símbolo repetido.
- [ ] La complejidad: O(*n*) para comprimir y descomprimir y O(*k* log *k*) para construir el árbol, con *k* ≤ 256.
- [ ] Cómo demostramos que no hay pérdida de información.
- [ ] Qué partes son de la biblioteca estándar y cuáles programamos nosotros.
