---
titulo: Huffman desde cero
subtitulo: Guía de estudio para entender y defender | comprimir.py y descomprimir.py
lema: Del concepto al código real, paso a paso, | con AAAAABBC como ejemplo de principio a fin.
fecha: 24 de noviembre de 2026
commit: 6dd8539
comprimir: 67 líneas
descomprimir: 91 líneas
---

<!--
Fuente editable de la guía de estudio. Para generar el PDF, desde la carpeta del proyecto:
    python output/guia_estudio/generar_guia_estudio.py
El encabezado de ese archivo explica las extensiones de Markdown que se usan aquí.
-->

# Cómo usar esta guía {-}

Esta guía es para estudiar el proyecto por tu cuenta. Empieza por la idea, sin código; después aprende las piezas de Python que se usan y, por último, recorre los dos programas reales bloque a bloque. Al terminar deberías poder explicar ante tu profesor **cómo** funciona cada parte y **por qué** está escrita así, no solo qué hace.

## Qué vas a poder hacer

- Construir a mano el árbol de Huffman de un mensaje y obtener sus códigos.
- Calcular, sin computador, los bytes exactos de un archivo `.pkz`.
- Leer `comprimir.py` y `descomprimir.py` línea por línea y decir qué valor tiene cada variable.
- Explicar las llamadas recursivas, las validaciones y los casos especiales.
- Responder las preguntas típicas de una exposición.

## El ejemplo central: AAAAABBC

Todo el documento usa el mismo mensaje de 8 letras: **AAAAABBC**. Es pequeño, pero tiene todo lo necesario: tres símbolos con frecuencias distintas (5, 2 y 1), un árbol de dos niveles y un archivo comprimido de solo 14 bytes que se puede analizar byte a byte.

```calculo
Mensaje original:   AAAAABBC                                    (8 bytes)
Archivo .pkz:       02 00 00 00 00 01 43 01 42 01 41 03 FA 80   (14 bytes)
Recuperado:         AAAAABBC                                    (idéntico)
```
<!-- comprobar: hexa(T.pkz) == "02 00 00 00 00 01 43 01 42 01 41 03 FA 80" and T.recuperado == b"AAAAABBC" -->

Al terminar la guía sabrás de dónde sale cada uno de esos 14 números.

## Cómo está organizada cada explicación

Cada tema recorre la misma ruta. Las etiquetas de color te indican en qué paso estás:

<!-- anchos: 28, 72 -->
| Paso | Qué encontrarás |
|---|---|
| **Concepto** | La idea, explicada antes de ver código. |
| **En palabras sencillas** | La misma idea con una comparación o un ejemplo cotidiano. |
| **Código real** | Las líneas exactas de los programas definitivos, con su número de línea. |
| **Ejecución con AAAAABBC** | Qué pasa por dentro: los valores de las variables, paso a paso. |
| **Resultado** | Lo que queda al terminar ese bloque. |
| **Conclusión** | La idea que debes recordar para la exposición. |

También verás recuadros: **Idea** (un dato que aclara), **Punto clave** (algo que el profesor puede preguntar), **Atención** (un error frecuente), **Ejercicio** y **Solución**.

## Ruta de estudio sugerida

<!-- anchos: 12, 18, 70 -->
| Sesión | Capítulos | Objetivo |
|---|---|---|
| 1 | 1, 2 y 3 | Entender la idea y resolver AAAAABBC a mano, sin código. |
| 2 | 4 y 5 | Aprender el Python necesario y seguir `comprimir.py`. |
| 3 | 6 y 7 | Seguir `descomprimir.py` y sus validaciones. |
| 4 | 8, 9 y 10 | Practicar con ejercicios y preparar la exposición. |

## Convenciones

- Los números de línea corresponden a la versión definitiva: `comprimir.py` (67 líneas) y `descomprimir.py` (91 líneas), del commit 6dd8539.
- Los bytes se escriben en hexadecimal con dos cifras: `41` es 65 en decimal, la letra A.
- Los bits se escriben como texto de ceros y unos, igual que en el código: `"11111010"`.
- Las ventanas oscuras de terminal muestran la salida real de los programas en Windows.

> [!NOTA] Todo está comprobado
> Esta guía se generó ejecutando los dos programas. Si el código cambiara, el generador detectaría qué explicación dejó de coincidir.

# La idea de Huffman

Antes de mirar código conviene entender qué problema se resuelve y por qué la solución de Huffman funciona. Este capítulo no exige saber programar.

## Un archivo es una fila de bytes

### Concepto

Todo archivo —un texto, una foto, un PDF o un video— es una secuencia de **bytes**. Un byte tiene 8 **bits** (ceros o unos) y puede valer cualquier número entero de 0 a 255. Las letras también se guardan como números: en el texto AAAAABBC, la A es el byte 65, la B el 66 y la C el 67.

### En palabras sencillas

Imagina el archivo como una fila de casillas numeradas, con un número entre 0 y 255 en cada una. El compresor no sabe si esos números son letras, píxeles o sonido: solo ve números. Por eso sirve para cualquier tipo de archivo.

### Código real

Python muestra esa fila de números si conviertes los bytes en una lista:

```python ejecutar
datos = b"AAAAABBC"
print(len(datos))
print(list(datos))
print(datos[0], format(datos[0], "08b"))
```
```salida
8
[65, 65, 65, 65, 65, 66, 66, 67]
65 01000001
```

### Ejecución con AAAAABBC

Debajo de cada letra aparece su byte en decimal y en binario (8 bits):

```diagrama mensaje
A        A        A        A        A        B        B        C
65       65       65       65       65       66       66       67
01000001 01000001 01000001 01000001 01000001 01000010 01000010 01000011
```

### Resultado

```calculo
8 bytes × 8 bits por byte = 64 bits
```

Guardar AAAAABBC tal cual cuesta 64 bits, porque cada letra ocupa siempre 8 bits, aunque se repita.

### Conclusión

Comprimir sin pérdida significa guardar **la misma fila de bytes** usando menos bits, y poder recuperarla **exactamente igual**.

## Códigos cortos para lo que más se repite

### Concepto

En AAAAABBC la A aparece 5 veces, la B 2 veces y la C 1 vez. Si en lugar de 8 bits por letra se usan códigos de **longitud variable** —cortos para las letras frecuentes y más largos para las raras—, el total baja mucho.

### En palabras sencillas

Es lo que hace el código Morse: la E, la letra más común en inglés, es una sola señal corta, mientras que letras raras como la Q necesitan cuatro señales. Lo frecuente se escribe corto.

### Ejecución con AAAAABBC

Supón estos códigos (en el capítulo 2 verás de dónde salen): A = `1`, B = `01`, C = `00`.

```calculo
Código fijo:      8 letras × 8 bits                        = 64 bits
Código variable:  5 × 1 (A)  +  2 × 2 (B)  +  1 × 2 (C)
                = 5          +  4          +  2             = 11 bits
```
<!-- comprobar: len(T.bits_datos) == 5 * 1 + 2 * 2 + 1 * 2 == 11 -->

### Conclusión

El ahorro viene de dar **pocos bits a lo frecuente**. Huffman encuentra la mejor asignación posible de este tipo.

## Sin separadores: los códigos prefijo

### Concepto

Si los códigos tienen distinta longitud, ¿cómo sabe el descompresor dónde termina uno y empieza el siguiente? La solución es que **ningún código sea el comienzo de otro**. A esto se le llama **código prefijo** (o libre de prefijos).

### En palabras sencillas

Mira lo que pasa con un código mal elegido: A = `0`, B = `1`, C = `01`. La secuencia `01` podría ser «A y luego B» o solo «C»: es ambigua. En cambio, con A = `1`, B = `01` y C = `00` no hay dudas: si lees `1`, ya terminaste (es A); si lees `0`, todavía falta un bit para saber si es B o C.

### Ejecución con AAAAABBC

Lee `10100` de izquierda a derecha con A = `1`, B = `01` y C = `00`:

```calculo
1      → completa A            quedan 0100
0 1    → completa B            quedan 00
0 0    → completa C            no queda nada
!Resultado: A B C
```
<!-- comprobar: descomprimir_bytes(bytes.fromhex("0200000000014301420141" + "05A0")) == b"ABC" -->

### Conclusión

Con un código prefijo no hacen falta separadores. El árbol de Huffman garantiza esta propiedad de forma automática, como verás enseguida.

## El árbol binario: un mapa de caminos

### Concepto

Un **árbol binario** empieza en la **raíz**, y cada **nodo interno** tiene exactamente dos hijos: izquierdo y derecho. Los nodos sin hijos son **hojas**, y en ellas están los símbolos. En este proyecto, ir a la izquierda significa escribir `0` e ir a la derecha, `1`. El **código** de un símbolo es el camino desde la raíz hasta su hoja.

### En palabras sencillas

Es como dar indicaciones en un camino con bifurcaciones: «izquierda, izquierda» te lleva a la C (`00`); «derecha» te lleva directo a la A (`1`). Como las letras solo están en los extremos (las hojas), ningún camino completo puede ser el comienzo de otro: por eso los códigos son prefijo.

### Ejecución con AAAAABBC

```diagrama arbol-codigos
              8
          0 /   \ 1
           3     A·5
       0 /   \ 1
       C·1   B·2
```

Los números de los nodos internos son la suma de las frecuencias que cuelgan de ellos: 3 = 1 + 2 y 8 = 3 + 5.
<!-- comprobar: peso(T.raiz, T.frecuencias) == 8 and peso(T.raiz[0], T.frecuencias) == 3 -->

### Conclusión

El árbol es la llave de la compresión: sin él no se pueden interpretar los bits. Por eso el archivo comprimido lo guarda (campo TREE).

## El algoritmo en cuatro pasos

### Concepto

Huffman construye el árbol de abajo hacia arriba:

1. **Contar** cuántas veces aparece cada byte.
2. **Crear** una hoja por cada byte distinto, con su frecuencia.
3. **Repetir** mientras quede más de un nodo: tomar los dos de **menor frecuencia**, unirlos en un nodo nuevo cuyo peso es la suma y devolverlo al grupo. El primero que se toma va a la **izquierda (0)**; el segundo, a la **derecha (1)**.
4. **Leer** los códigos recorriendo el árbol desde la raíz.

### En palabras sencillas

Es un torneo al revés: en cada ronda se juntan los dos menos frecuentes. Los que se unen pronto quedan más abajo (códigos largos); el más frecuente se une al final y queda cerca de la raíz (código corto).

> [!CLAVE] Regla de desempate de este proyecto
> Si dos nodos tienen la misma frecuencia, va primero el que contiene el **byte más pequeño**. Así el mismo archivo produce siempre el mismo `.pkz`. En el capítulo 8 hay un ejercicio resuelto con empate.

> [!IDEA] ¿Por qué se dice que es voraz?
> En cada paso toma la mejor decisión local (unir los dos menores) y nunca la deshace. Se puede demostrar que en algún árbol óptimo los dos símbolos menos frecuentes son hermanos en el nivel más profundo; por eso unirlos primero nunca empeora el resultado.

### Conclusión

Con solo cuatro pasos se obtiene el código prefijo más corto posible para esas frecuencias.

# AAAAABBC, resuelto a mano

Este capítulo aplica los cuatro pasos al ejemplo central con lápiz y papel. Todos los valores coinciden con los que producen los programas reales, como comprobarás en los capítulos 5 y 6.

## Paso 1: contar las frecuencias

### Concepto

Se cuenta cuántas veces aparece cada byte distinto. Estas cantidades son las **frecuencias**, y su suma es la longitud del mensaje.

### Ejecución con AAAAABBC

<!-- tabla: frecuencias -->
| Carácter | Byte (decimal) | Frecuencia |
|---|---|---|
| A | 65 | 5 |
| B | 66 | 2 |
| C | 67 | 1 |

```calculo
5 + 2 + 1 = 8 bytes en total
3 bytes distintos  → el árbol tendrá 3 hojas y 3 - 1 = 2 nodos internos
```

### Conclusión

Hay **3 símbolos distintos**. En el capítulo 3 verás que ese 2 (los nodos internos) es el primer byte del archivo comprimido.

## Paso 2: construir el árbol

### Concepto

Se ordenan los nodos de menor a mayor frecuencia y se unen los dos primeros. El nodo nuevo pesa la suma y vuelve al grupo. Se repite hasta que queda uno solo: la raíz.

### Ejecución con AAAAABBC

```calculo
Inicio:    C·1   B·2   A·5          (ordenados de menor a mayor)

Vuelta 1:  los dos menores son C·1 y B·2
           peso nuevo = 1 + 2 = 3
           C a la izquierda (0), B a la derecha (1)
           quedan:  [3: C B]   A·5

Vuelta 2:  los dos menores son [3] y A·5
           peso nuevo = 3 + 5 = 8
           [3] a la izquierda (0), A a la derecha (1)
           queda un solo nodo: la raíz, de peso 8
```
<!-- comprobar: [v["nuevo"][0] for v in T.vueltas] == [3, 8] -->

En el diagrama, el nodo naranja es el que se acaba de crear en cada vuelta:

```diagrama construccion
inicio: C·1 B·2 A·5  |  vuelta 1: [3: C B] A·5  |  vuelta 2: [8: [3: C B] A]
```

### Resultado

El árbol final tiene la raíz (8), un nodo interno (3) y tres hojas: C·1, B·2 y A·5.

### Conclusión

Las letras raras (C y B) se unieron primero y quedaron más abajo; la A, la más frecuente, quedó junto a la raíz.

## Paso 3: leer los códigos

### Concepto

El código de cada letra es el camino desde la raíz: `0` por cada paso a la izquierda y `1` por cada paso a la derecha.

### Ejecución con AAAAABBC

<!-- tabla: codigos -->
| Símbolo | Camino desde la raíz | Código | Veces que aparece | Bits que aporta |
|---|---|---|---|---|
| C | izquierda, izquierda | `00` | 1 | 1 × 2 = 2 |
| B | izquierda, derecha | `01` | 2 | 2 × 2 = 4 |
| A | derecha | `1` | 5 | 5 × 1 = 5 |

La tabla sigue el orden en que el programa guarda los códigos (C, B y A): es el orden en que recorre el árbol, como verás en el capítulo 5.

### Conclusión

A = `1`, B = `01`, C = `00`. El símbolo más frecuente tiene el código más corto.

## Paso 4: codificar el mensaje

### Concepto

Se reemplaza cada letra por su código, en el mismo orden del mensaje, y se pegan los resultados.

### Ejecución con AAAAABBC

```calculo
Mensaje:   A  A  A  A  A  B   B   C
Códigos:   1  1  1  1  1  01  01  00
Pegados:   11111010100
Longitud:  5 × 1 + 2 × 2 + 1 × 2 = 5 + 4 + 2 = 11 bits
```
<!-- comprobar: T.bits_datos == "11111010100" -->

### Conclusión

El mensaje completo cabe en **11 bits**, frente a los 64 originales.

## Paso 5: de bits a bytes

### Concepto

Un archivo solo puede guardar bytes completos, es decir, grupos de 8 bits. Los 11 bits se reparten en bytes y el último se completa con ceros de **relleno**. Para no confundir el relleno con datos, se anota cuántos bits del último byte son útiles: ese número se llama **BS**.

### Ejecución con AAAAABBC

Cada color corresponde a una letra; los bits grises son el relleno:

```diagrama bits-zip
1 1 1 1 1 0 1 0 | 1 0 0 0 0 0 0 0
A A A A A  B    B   C   relleno
```

```calculo
11 bits = 1 × 8 + 3      → 1 byte completo y sobran 3 bits
BS      = 11 % 8 = 3     (bits útiles del último byte)
Relleno = 8 - BS = 8 - 3 = 5 ceros
Total   = 11 + 5 = 16 bits = 2 bytes
```
<!-- comprobar: T.bs == 11 % 8 == 3 and len(T.bits_relleno) == 16 -->

Ahora cada grupo de 8 bits se convierte en un número. Cada posición vale el doble que la de su derecha:

```calculo
Valor de cada posición:   128  64  32  16   8   4   2   1

Byte 1 = 1 1 1 1 1 0 1 0
       = 128 + 64 + 32 + 16 + 8 + 0 + 2 + 0 = 250
       250 = 15 × 16 + 10   → cifras hexadecimales F (15) y A (10) → FA

Byte 2 = 1 0 0 0 0 0 0 0
       = 128
       128 = 8 × 16 + 0     → cifras hexadecimales 8 y 0 → 80
```
<!-- comprobar: T.zip == bytes([250, 128]) and hexa(T.zip) == "FA 80" -->

> [!IDEA] Leer hexadecimal sin sufrir
> Cada cifra hexadecimal equivale exactamente a 4 bits. `1111` es F y `1010` es A, así que `11111010` es FA. Para `10000000`: `1000` es 8 y `0000` es 0, así que es 80.

### Resultado

Los 11 bits ocupan 2 bytes, **FA 80**, con **BS = 3**.

### Conclusión

BS existe porque el relleno es inevitable: sin él, el descompresor leería los 5 ceros finales como si fueran datos.

## ¿Cuánto se ganó?

### Concepto

Hay que distinguir dos cosas: los bits de **datos** y el **archivo completo**, que además guarda el árbol y dos bytes de control.

### Ejecución con AAAAABBC

```calculo
Datos:     64 bits → 11 bits
           ahorro = (64 - 11) ÷ 64 = 53 ÷ 64 ≈ 0,828  → 82,8 % menos
Promedio:  11 bits ÷ 8 letras = 1,375 bits por letra (antes, 8)

Archivo:   8 bytes → 14 bytes   (NF 1 + TREE 10 + BS 1 + ZIP 2)
           cambio = (14 - 8) ÷ 8 = 6 ÷ 8 = 0,75  → crece un 75 %
```
<!-- comprobar: len(T.pkz) == 1 + 10 + 1 + 2 == 14 and round(53 / 64, 3) == 0.828 -->

El ejemplo crece porque el árbol pesa más que lo que se ahorra en 8 letras. En archivos grandes el árbol se vuelve insignificante: el documento `doc.doc` de la carpeta de demostración pasa de 44.544 bytes a 18.855.
<!-- comprobar: len(demo("doc.doc.pkz")) == 18855 and len(descomprimir_bytes(demo("doc.doc.pkz"), "doc.doc.pkz")) == 44544 -->

> [!IDEA] Para profundizar: el límite teórico
> La **entropía** mide el mínimo promedio de bits por símbolo para unas frecuencias dadas. Para AAAAABBC:
> ```calculo
> H = -(5/8 · log₂(5/8) + 2/8 · log₂(2/8) + 1/8 · log₂(1/8))
>   = 0,4238 + 0,5000 + 0,3750
>   ≈ 1,2988 bits por símbolo
> ```
> Huffman usa 1,375 bits por símbolo: está entre H y H + 1, como garantiza la teoría.
<!-- comprobar: abs(-(5/8 * math.log2(5/8) + 2/8 * math.log2(2/8) + 1/8 * math.log2(1/8)) - 1.2988) < 0.0001 -->

### Conclusión

Huffman reduce mucho los datos, pero el archivo incluye el árbol. En mensajes muy cortos ese costo fijo pesa más que el ahorro.

## Decodificar a mano

### Concepto

Para recuperar el mensaje se leen los bits uno por uno desde la raíz: `0` baja a la izquierda y `1` a la derecha. Al llegar a una hoja se anota su letra y se vuelve a la raíz.

### Ejecución con AAAAABBC

```calculo
Bits útiles: 11111010 100       (del segundo byte solo valen BS = 3 bits)

1      → raíz, derecha → hoja A                   A
1      → A                                        A A
1      → A                                        A A A
1      → A                                        A A A A
1      → A                                        A A A A A
0 1    → izquierda, derecha → hoja B              A A A A A B
0 1    → B  (el 0 cierra el byte 1 y el 1 abre el byte 2)
0 0    → izquierda, izquierda → hoja C            A A A A A B B C
!Resultado: AAAAABBC
```
<!-- comprobar: "".join(c["simbolo"] for c in leer_codigos(T)) == "AAAAABBC" -->

### Conclusión

Como el código es prefijo, nunca hay que retroceder: cada hoja marca el final de un código. Fíjate además en que un código puede empezar en un byte y terminar en el siguiente.

# El formato .pkz por dentro

El archivo comprimido tiene cuatro campos, siempre en el mismo orden: **NF | TREE | BS | ZIP**. Con ellos el descompresor reconstruye el original sin consultar nada más.

## Los cuatro campos de un vistazo

### Concepto

<!-- anchos: 14, 26, 60 -->
| Campo | Tamaño | Qué guarda |
|---|---|---|
| **NF** | 1 byte | Cantidad de nodos internos del árbol (de 0 a 255). |
| **TREE** | 2 × (2 × NF + 1) bytes | El árbol en preorden, 2 bytes por nodo. |
| **BS** | 1 byte | Bits útiles del último byte de ZIP (de 1 a 8). |
| **ZIP** | el resto | Los códigos de todo el mensaje, empaquetados en bytes. |

### Ejecución con AAAAABBC

```diagrama formato-pkz
02 | 00 00 00 00 01 43 01 42 01 41 | 03 | FA 80
```

### Conclusión

El árbol y los datos viajan juntos. **No** se guarda la tabla de frecuencias: basta con la forma del árbol.

## NF: cuántos nodos internos hay

### Concepto

Cada unión del algoritmo crea exactamente un nodo interno y deja un nodo suelto menos. Con k símbolos se empieza con k nodos y se termina con 1, así que hay k - 1 uniones, es decir, **k - 1 nodos internos**.

### Ejecución con AAAAABBC

```calculo
k  = 3 símbolos (A, B y C)
NF = k - 1 = 3 - 1 = 2              → el primer byte del archivo es 02
Nodos totales = hojas + internos = 3 + 2 = 5 = 2 × NF + 1
```
<!-- comprobar: T.nf == 2 and T.pkz[0] == 2 -->

### Conclusión

Con NF se sabe cuántos nodos tiene el árbol (2 × NF + 1) y, por lo tanto, cuántos bytes ocupa TREE.

## TREE: el árbol en preorden

### Concepto

Para guardar un árbol en una fila de bytes se usa el **preorden**: primero el nodo actual, después todo su subárbol izquierdo y por último el derecho. Cada nodo ocupa 2 bytes:

- nodo interno: `00 00`;
- hoja: `01` seguido del byte del símbolo (por ejemplo, `01 43` es la hoja C).

### En palabras sencillas

Es como dictar el árbol por teléfono: «un nodo interno; su hijo izquierdo es otro nodo interno, cuyos hijos son C y B; el hijo derecho de la raíz es A». Quien escucha puede dibujarlo sin ver el original.

### Ejecución con AAAAABBC

Los números naranjas indican el orden en que se escribe cada nodo:

```diagrama preorden
1 raíz (00 00) → 2 interno (00 00) → 3 C (01 43) → 4 B (01 42) → 5 A (01 41)
```

```calculo
TREE   = 00 00   00 00     01 43   01 42   01 41
         raíz    interno   C       B       A
Tamaño = 2 × (2 × NF + 1) = 2 × (2 × 2 + 1) = 2 × 5 = 10 bytes
```
<!-- comprobar: hexa(T.arbol) == "00 00 00 00 01 43 01 42 01 41" and len(T.arbol) == 10 -->

> [!ATENCION] ¿Por qué hace falta el marcador 01?
> Un archivo puede contener el byte 0. Si las hojas se guardaran solo con su byte, una hoja del byte 0 se confundiría con un nodo interno. El primer byte de cada par (00 o 01) dice qué tipo de nodo es.

### Conclusión

El preorden permite reconstruir exactamente la misma forma de árbol sin guardar punteros ni separadores.

## BS: bits útiles del último byte

### Concepto

BS indica cuántos bits del último byte de ZIP son datos, y vale entre 1 y 8. Se calcula con el resto de dividir la cantidad de bits entre 8; si ese resto es 0, el último byte está completo y BS vale 8.

### Ejecución con AAAAABBC

```calculo
bits = 11      11 % 8 = 3      → BS = 3      → el byte 11 del archivo vale 03
```
<!-- comprobar: T.pkz[11] == T.bs == 3 -->

Si el mensaje hubiera tenido 16 bits, el resto sería 0 y BS valdría 8, no 0.

### Conclusión

BS = 0 solo aparece en el archivo vacío (`00 00`); en cualquier otro caso, un BS fuera del rango de 1 a 8 es un error.

## ZIP: los bits empaquetados

### Concepto

ZIP contiene los códigos de todo el mensaje, pegados y agrupados de 8 en 8. El primer bit del mensaje es el bit más significativo (el de la izquierda) del primer byte.

### Ejecución con AAAAABBC

ZIP = `FA 80`, es decir, `11111010` y `10000000`. Del segundo byte solo valen los 3 primeros bits (`100`); los otros 5 son relleno.

> [!NOTA] ZIP no es el formato ZIP
> Aquí ZIP es solo el nombre del campo con los datos comprimidos; no tiene relación con los archivos .zip comerciales.

## El archivo completo, byte a byte

### Ejecución con AAAAABBC

<!-- anchos: 11, 15, 13, 61 -->
<!-- tabla: pkz -->
| Índice | Byte (hex) | Campo | Significado |
|---|---|---|---|
| 0 | 02 | NF | 2 nodos internos |
| 1 | 00 | TREE | raíz: nodo interno (marcador) |
| 2 | 00 | TREE | raíz: nodo interno (segundo byte) |
| 3 | 00 | TREE | nodo interno de la izquierda (marcador) |
| 4 | 00 | TREE | nodo interno de la izquierda (segundo byte) |
| 5 | 01 | TREE | hoja (marcador) |
| 6 | 43 | TREE | símbolo C (67) |
| 7 | 01 | TREE | hoja (marcador) |
| 8 | 42 | TREE | símbolo B (66) |
| 9 | 01 | TREE | hoja (marcador) |
| 10 | 41 | TREE | símbolo A (65) |
| 11 | 03 | BS | 3 bits útiles en el último byte |
| 12 | FA | ZIP | 11111010: A A A A A, una B y el primer bit de la otra B |
| 13 | 80 | ZIP | 1 (fin de la segunda B), 00 (C) y 00000 de relleno |

```calculo
fin_arbol = 1 + 2 × (2 × NF + 1) = 1 + 2 × 5 = 11
TREE ocupa los índices 1 a 10, BS está en el índice 11 y ZIP empieza en el 12.
```
<!-- comprobar: T.fin_arbol == 11 -->

## Dos casos especiales

### Archivo vacío

Un archivo de 0 bytes no tiene símbolos, ni árbol, ni bits. Se guarda como **exactamente dos bytes**: `00 00` (NF = 0 y BS = 0). Un archivo no vacío nunca mide 2 bytes (el mínimo es 5: NF, una hoja de 2 bytes, BS y al menos un byte de ZIP), así que no hay confusión posible.
<!-- comprobar: comprimir_bytes(b"") == b"\x00\x00" and descomprimir_bytes(b"\x00\x00") == b"" -->

### Un solo símbolo

Con un único byte distinto, por ejemplo 17 letras X, el árbol es una sola hoja: NF = 0 y no hay caminos. Por convención, el código de esa hoja es `0`, así que cada X ocupa 1 bit.

```calculo
17 × X  → 17 bits "0"  →  17 = 2 × 8 + 1  →  3 bytes, BS = 1
.pkz    = 00 | 01 58 | 01 | 00 00 00          (7 bytes; 58 es la X)
```
<!-- comprobar: hexa(comprimir_bytes(b"X" * 17)) == "00 01 58 01 00 00 00" -->

### Conclusión

Los dos casos especiales se reconocen enseguida: `00 00` es el archivo vacío, y NF = 0 con una sola hoja es un archivo de un solo símbolo.

# El Python que necesitas

Los dos programas usan pocas herramientas de Python, pero cada una se aprovecha a fondo. Aquí están todas, con un ejemplo pequeño que se ejecutó al generar la guía y la línea del proyecto donde aparece.

## bytes, enteros y Counter

### Concepto

`b"..."` crea un objeto **bytes**: una secuencia que no se puede modificar, formada por enteros de 0 a 255. Al tomar un elemento o recorrerlo con `for` obtienes **enteros**, no letras. `Counter`, del módulo `collections`, cuenta cuántas veces aparece cada elemento y se comporta como un diccionario.

### Código real

```python ejecutar
from collections import Counter

datos = b"AAAAABBC"
print(datos[0], datos[-1])
frecuencias = Counter(datos)
print(frecuencias)
print(list(frecuencias.items()))
```
```salida
65 67
Counter({65: 5, 66: 2, 67: 1})
[(65, 5), (66, 2), (67, 1)]
```

### Conclusión

El compresor trabaja con números de 0 a 255; por eso le da igual si el archivo es texto, imagen o video. En el proyecto: `Counter(datos)` en la línea 10 de `comprimir.py` y `frecuencias.items()` en la línea 15.
<!-- comprobar: lc("frecuencias = Counter(datos)") == 10 and lc("frecuencias.items()") == 15 -->

## Tuplas y cómo compara Python

### Concepto

Una **tupla** agrupa varios valores entre paréntesis: `(1, 67, 67)`. Python compara tuplas **elemento por elemento**, de izquierda a derecha, y decide con el primer elemento distinto. Por eso `sort()` sobre una lista de tuplas ordena por el primer valor y, si hay empate, por el segundo.

### En palabras sencillas

Es como ordenar palabras en un diccionario: primero se mira la primera letra; solo si coincide se mira la segunda.

### Código real

```python ejecutar
print((1, 67, 67) < (2, 66, 66))
print((3, 65) < (3, 67))
nodos = [(5, 65, 65), (2, 66, 66), (1, 67, 67)]
nodos.sort()
print(nodos)
```
```salida
True
True
[(1, 67, 67), (2, 66, 66), (5, 65, 65)]
```

### Conclusión

En el proyecto cada nodo es `(frecuencia, byte mínimo, árbol)`, y `sort()` (línea 17) los ordena por frecuencia y, si empatan, por byte mínimo. Como dos nodos nunca comparten byte mínimo, Python nunca llega a comparar el tercer elemento.
<!-- comprobar: lc("nodos.sort()") == 17 -->

## pop(0), append y min

### Concepto

`lista.pop(0)` **quita y devuelve** el primer elemento. `lista.append(x)` agrega `x` al final. `min(a, b)` devuelve el menor de los dos valores.

### Código real

```python ejecutar
nodos = [(1, 67, 67), (2, 66, 66), (5, 65, 65)]
primero = nodos.pop(0)
segundo = nodos.pop(0)
print(primero, segundo, nodos)
nodos.append((primero[0] + segundo[0], min(primero[1], segundo[1]), (primero[2], segundo[2])))
print(nodos)
```
```salida
(1, 67, 67) (2, 66, 66) [(5, 65, 65)]
[(5, 65, 65), (3, 66, (67, 66))]
```

### Conclusión

Estas tres operaciones son exactamente la primera vuelta del ciclo de `comprimir.py`, líneas 18 a 21.
<!-- comprobar: lc("peso_izq, minimo_izq, izquierda = nodos.pop(0)") == 18 and lc("nodos.append((peso_izq") == 21 -->

## Tuplas como árbol e isinstance

### Concepto

En el proyecto un árbol se representa así: una **hoja** es un entero (el byte) y un **nodo interno** es una tupla `(izquierda, derecha)`. `isinstance(x, int)` pregunta si `x` es un entero, es decir, si es una hoja. `nodo[0]` y `nodo[1]` son los hijos izquierdo y derecho.

### Código real

```python ejecutar
raiz = ((67, 66), 65)
print(isinstance(raiz, int), isinstance(65, int))
print(raiz[0], raiz[1])
print(raiz[0][0], raiz[0][1])
```
```salida
False True
(67, 66) 65
67 66
```

### Conclusión

`raiz[0][1]` significa «izquierda y luego derecha»: el camino `01`, que lleva a la B (66). El índice de la tupla **es** la dirección del camino.

## Diccionarios, bytearray y join

### Concepto

- Un **diccionario** asocia claves con valores: `codigos[65] = "1"`.
- Un **bytearray** es como bytes, pero se puede modificar; `extend((1, 67))` le agrega dos bytes al final.
- `"".join(...)` pega muchas cadenas en una sola, en orden.

### Código real

```python ejecutar
codigos = {65: "1", 66: "01", 67: "00"}
arbol = bytearray()
arbol.extend((0, 0))
arbol.extend((1, 67))
print(arbol.hex(" "))
bits = "".join(codigos[byte] for byte in b"AAAAABBC")
print(bits, len(bits))
```
```salida
00 00 01 43
11111010100 11
```

### Conclusión

En `comprimir.py` aparecen en las líneas 24 (`codigos = {}`), 25 (`arbol = bytearray()`), 30 y 32 (`extend`) y 40 (`join`).
<!-- comprobar: [lc("codigos = {}"), lc("arbol = bytearray()"), lc("arbol.extend((1, nodo))"), lc("arbol.extend((0, 0))"), lc('bits = "".join(')] == [24, 25, 30, 32, 40] -->

## Bits como texto: %, or, int y to_bytes

### Concepto

El proyecto maneja los bits como **texto** de ceros y unos y solo al final los convierte en bytes:

- `n % 8` es el **resto** de dividir `n` entre 8.
- `x or y` devuelve `x` si `x` vale algo (no es 0 ni está vacío); si no, devuelve `y`.
- `"0" * 5` repite el texto: `"00000"`.
- `int(texto, 2)` lee el texto como un número en **base 2**.
- `numero.to_bytes(n, "big")` escribe el número en `n` bytes, empezando por el más significativo.

### Código real

```python ejecutar
print(11 % 8, 11 % 8 or 8, 16 % 8 or 8)
bits = "11111010100"
bits += "0" * (8 - 3)
print(bits)
numero = int(bits, 2)
print(numero, numero.to_bytes(2, "big").hex(" "))
```
```salida
3 3 8
1111101010000000
64128 fa 80
```

### Ejecución con AAAAABBC

```calculo
int("1111101010000000", 2) = 64128
64128 = 250 × 256 + 128      → to_bytes(2, "big") = [250, 128] = FA 80
```
<!-- comprobar: int(T.bits_relleno, 2) == 64128 == 250 * 256 + 128 -->

### Conclusión

`len(bits) % 8 or 8` calcula BS: el resto, salvo que sea 0, en cuyo caso el último byte está lleno y BS vale 8.

## De byte a texto de bits: f"{byte:08b}"

### Concepto

El descompresor hace la operación inversa. `f"{byte:08b}"` escribe un número en binario (`b`) con 8 cifras, rellenando con ceros a la izquierda (`08`). Con **rebanadas** se toman partes de un texto o de unos bytes: `texto[:3]` son los 3 primeros elementos y `texto[3:]`, todos los demás.

### Código real

```python ejecutar
texto = f"{128:08b}"
print(texto, texto[:3], texto[3:])
print(f"{250:08b}", "1" in "00000")
datos = bytes.fromhex("0200000000014301420141")
tipo, valor = datos[5:7]
print(tipo, valor)
```
```salida
10000000 100 00000
11111010 False
1 67
```

### Conclusión

En `descomprimir.py` aparecen en las líneas 30 (`tipo, valor = ...`), 50 (comprobación del relleno) y 63 (bits de cada byte).
<!-- comprobar: [ld("tipo, valor = datos[posicion:posicion + 2]"), ld('if "1" in f"{zip_bytes[-1]:08b}"[bs:]'), ld('for bit in f"{byte:08b}"[:validos]:')] == [30, 50, 63] -->

## Recursión y nonlocal

### Concepto

Una función es **recursiva** cuando se llama a sí misma. Funciona porque cada llamada resuelve un problema más pequeño y hay un **caso base** que ya no vuelve a llamar. Cada llamada tiene sus propias variables: Python las guarda en una **pila de llamadas** y, cuando una termina, continúa la anterior justo donde se quedó.

`nonlocal` permite que una función interna **modifique** una variable de la función que la contiene, en lugar de crear una variable nueva.

### Código real

```python ejecutar
def contar_hojas(nodo):
    if isinstance(nodo, int):
        return 1
    return contar_hojas(nodo[0]) + contar_hojas(nodo[1])

print(contar_hojas(((67, 66), 65)))

def contador():
    total = 0
    def sumar():
        nonlocal total
        total += 2
    sumar()
    sumar()
    return total

print(contador())
```
```salida
3
4
```

### Conclusión

`recorrer` (en el compresor) y `leer_arbol` (en el descompresor) siguen este mismo patrón: caso base en la hoja y dos llamadas, una por cada hijo. `leer_arbol` usa además `nonlocal posicion` para avanzar por TREE.

## Archivos y terminal

### Concepto

- `Path` representa una ruta: `.suffix` es la extensión, `.name` el nombre y `.with_name()` crea una ruta con otro nombre.
- `open("xb")` crea un archivo **binario** nuevo y **falla si ya existe** (`FileExistsError`). Así ninguno de los dos programas sobrescribe nada.
- `sys.argv` es la lista de palabras escritas en la terminal; `sys.exit("mensaje")` termina el programa mostrando ese mensaje.
- `try` / `except` captura un error para mostrar un mensaje breve en lugar de un informe técnico.

### Código real

```python ejecutar
from pathlib import Path

ruta = Path("aaaaabbc.txt.pkz")
print(ruta.suffix, ruta.name[:-4], ruta.with_name("otro.pkz").name)
Path("prueba.bin").write_bytes(b"x")
try:
    with Path("prueba.bin").open("xb") as archivo:
        archivo.write(b"y")
except FileExistsError as error:
    print("No se sobrescribe:", type(error).__name__)
```
```salida
.pkz aaaaabbc.txt otro.pkz
No se sobrescribe: FileExistsError
```

### Conclusión

El modo `"xb"` es la protección contra sobrescrituras de los dos programas: línea 53 de `comprimir.py` y línea 77 de `descomprimir.py`.
<!-- comprobar: lc('with destino.open("xb")') == 53 and ld('with destino.open("xb")') == 77 -->

# comprimir.py por dentro

Ahora sí, el programa real. Lo recorremos en 11 bloques pequeños; en cada uno verás el código exacto, qué hace cada instrucción y qué valores toman las variables con AAAAABBC.

## El mapa del programa

```diagrama flujo-comprimir
Leer y contar → Construir el árbol → Códigos y TREE → Bits, BS y ZIP → Guardar el .pkz
```

<!-- anchos: 10, 12, 78 -->
| Bloque | Líneas | Qué hace |
|---|---|---|
| 1 | 1-4 | Documentación e importaciones. |
| 2 | 7-10 | Lee el archivo y cuenta los bytes. |
| 3 | 12-15 | Crea la lista inicial de nodos. |
| 4 | 16-21 | Une los nodos hasta tener el árbol. |
| 5 | 23-25 | Prepara el diccionario de códigos y el TREE. |
| 6 | 27-34 | Recorre el árbol con recursión: códigos y TREE. |
| 7 | 36-37 | Arranca el recorrido desde la raíz. |
| 8 | 39-46 | Une los códigos y los empaqueta en bytes. |
| 9 | 48-50 | Arma NF, TREE, BS y ZIP. |
| 10 | 52-58 | Guarda el .pkz sin sobrescribir. |
| 11 | 61-67 | Permite usarlo desde la terminal. |
<!-- comprobar: [lc("def comprimir"), lc("frecuencias = Counter"), lc("# 1. Construir"), lc("nodos = [(frecuencia"), lc("while len(nodos) > 1"), lc("nodos.append((peso_izq"), lc("# 2. Crear"), lc("arbol = bytearray()"), lc("def recorrer"), lc('recorrer(nodo[1], codigo + "1")'), lc("if nodos:"), lc("recorrer(nodos[0][2])"), lc("# 3. Empaquetar"), lc("zip_bytes = int(bits"), lc("# 4. Guardar"), lc("contenido = bytes([nf])"), lc("destino = Path(salida)"), lc("return destino"), lc("if __name__")] == [7, 10, 12, 15, 16, 21, 23, 25, 27, 34, 36, 37, 39, 46, 48, 50, 52, 58, 61] and NLINEAS["comprimir.py"] == 67 -->

## Bloque 1 · Encabezado e importaciones

### Código real

```python comprimir.py:1-4
"""Comprime un archivo con Huffman. Uso: python comprimir.py archivo [salida.pkz]"""
import sys
from collections import Counter
from pathlib import Path
```

### Instrucción por instrucción

<!-- anchos: 34, 66 -->
| Instrucción | Qué hace y por qué |
|---|---|
| `"""..."""` | Documentación del programa: qué hace y cómo se usa. |
| `import sys` | Da acceso a `sys.argv` (argumentos) y `sys.exit` (terminar con un mensaje). |
| `from collections import Counter` | Trae el contador de frecuencias. |
| `from pathlib import Path` | Trae la clase que maneja rutas de archivos. |

### Conclusión

Solo se usan módulos de la **biblioteca estándar**: no hay que instalar nada para ejecutar el programa.

## Bloque 2 · Leer el archivo y contar

### Concepto

Primero hay que tener los bytes del archivo y saber cuántas veces aparece cada uno: es el paso 1 del algoritmo.

### Código real

```python comprimir.py:7-10
def comprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    datos = ruta.read_bytes()
    frecuencias = Counter(datos)
```

### Instrucción por instrucción

<!-- anchos: 10, 30, 31, 29 -->
| Línea | Instrucción | Qué hace | Por qué |
|---|---|---|---|
| 7 | `def comprimir(archivo, salida=None)` | Define la función; `salida` es opcional. | Si no se indica, se usará `<nombre>.pkz`. |
| 8 | `Path(archivo).expanduser()` | Convierte el texto en ruta; `~` pasa a ser la carpeta del usuario. | Facilita trabajar con rutas. |
| 9 | `ruta.read_bytes()` | Lee **todo** el archivo como bytes. | Hay que ver el archivo completo para contar. |
| 10 | `Counter(datos)` | Cuenta cada byte. | Son las frecuencias del algoritmo. |

### Ejecución con AAAAABBC

```calculo
archivo     = "aaaaabbc.txt"
datos       = b'AAAAABBC'                       (8 bytes)
frecuencias = Counter({65: 5, 66: 2, 67: 1})
```
<!-- comprobar: repr(T.datos) == "b'AAAAABBC'" and repr(T.frecuencias) == "Counter({65: 5, 66: 2, 67: 1})" -->

### Conclusión

Al terminar el bloque, el programa sabe que hay 3 bytes distintos: 65 (cinco veces), 66 (dos) y 67 (una).

## Bloque 3 · La lista inicial de nodos

### Concepto

Cada byte distinto se convierte en un nodo hoja. Para poder ordenarlos, cada nodo se guarda como una tupla de tres valores.

### Código real

```python comprimir.py:12-15
    # 1. Construir el árbol uniendo los dos nodos menos frecuentes.
    #    Cada nodo es (frecuencia, byte mínimo, árbol). El árbol de una hoja es
    #    su byte; el de un nodo interno es la tupla (izquierda, derecha).
    nodos = [(frecuencia, byte, byte) for byte, frecuencia in frecuencias.items()]
```

### En palabras sencillas

Cada nodo es una ficha con tres datos: **cuánto pesa** (frecuencia), **su byte más pequeño** (para desempatar) y **qué contiene** (el árbol). En una hoja el byte aparece dos veces: una para desempatar y otra como contenido.

### Ejecución con AAAAABBC

```calculo
frecuencias.items()  →  (65, 5), (66, 2), (67, 1)
nodos = [(5, 65, 65), (2, 66, 66), (1, 67, 67)]
          A            B            C
```
<!-- comprobar: T.nodos_inicio == [(5, 65, 65), (2, 66, 66), (1, 67, 67)] -->

La lista queda en el orden en que los bytes aparecen en el archivo (primero A). Todavía no está ordenada.

### Conclusión

`(frecuencia, byte, byte)` pone la frecuencia primero para que `sort()` ordene por ella.

## Bloque 4 · El ciclo que arma el árbol

### Concepto

Mientras quede más de un nodo, se ordenan, se sacan los dos menores y se mete su unión. Es el paso 3 del algoritmo.

### Código real

```python comprimir.py:16-21
    while len(nodos) > 1:
        nodos.sort()  # Por frecuencia; en empate, por byte mínimo (nunca se repite).
        peso_izq, minimo_izq, izquierda = nodos.pop(0)
        peso_der, minimo_der, derecha = nodos.pop(0)
        minimo = min(minimo_izq, minimo_der)
        nodos.append((peso_izq + peso_der, minimo, (izquierda, derecha)))
```

### Instrucción por instrucción

<!-- anchos: 10, 51, 39 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 16 | Repite mientras haya más de un nodo. | Al final debe quedar solo la raíz. |
| 17 | Ordena de menor a mayor (frecuencia y, si empatan, byte mínimo). | Así los dos menores quedan al principio. |
| 18 | Saca el primero y separa sus tres valores. | Es el menor: irá a la **izquierda** (0). |
| 19 | Saca el siguiente. | Es el segundo menor: irá a la **derecha** (1). |
| 20 | Calcula el byte mínimo del grupo nuevo. | Servirá para desempatar en vueltas futuras. |
| 21 | Agrega el nodo nuevo: peso sumado, mínimo y tupla de hijos. | El grupo nuevo vuelve a competir. |

### Ejecución con AAAAABBC

<!-- anchos: 9, 29, 17, 14, 9, 22 -->
<!-- tabla: vueltas -->
| Vuelta | Lista tras `sort()` (17) | Izquierda (18) | Derecha (19) | `minimo` (20) | Se agrega (21) |
|---|---|---|---|---|---|
| 1 | `[(1, 67, 67), (2, 66, 66), (5, 65, 65)]` | `(1, 67, 67)` | `(2, 66, 66)` | 66 | `(3, 66, (67, 66))` |
| 2 | `[(3, 66, (67, 66)), (5, 65, 65)]` | `(3, 66, (67, 66))` | `(5, 65, 65)` | 65 | `(8, 65, ((67, 66), 65))` |

```calculo
Vuelta 1:  peso = 1 + 2 = 3        minimo = min(67, 66) = 66
           nodos = [(5, 65, 65), (3, 66, (67, 66))]
Vuelta 2:  peso = 3 + 5 = 8        minimo = min(66, 65) = 65
           nodos = [(8, 65, ((67, 66), 65))]      → len(nodos) = 1: termina el while
```
<!-- comprobar: [v["despues"] for v in T.vueltas] == [[(5, 65, 65), (3, 66, (67, 66))], [(8, 65, ((67, 66), 65))]] -->

### Resultado

Queda un solo nodo: `(8, 65, ((67, 66), 65))`. Su tercer campo, `((67, 66), 65)`, es el árbol completo: a la izquierda el grupo formado por C y B, y a la derecha la A.

### Conclusión

Las tuplas anidadas **son** el árbol. `((67, 66), 65)` se lee: «la raíz tiene a la izquierda un nodo con C y B, y a la derecha la A».

> [!PREGUNTA] ¿Por qué ordenar la lista en cada vuelta y no usar heapq?
> Con 256 valores de byte posibles, la lista nunca tiene más de 256 nodos: ordenarla en cada vuelta es instantáneo y más fácil de explicar. El árbol que se obtiene es el mismo que con una cola de prioridad.

## Bloque 5 · Preparar códigos y TREE

### Código real

```python comprimir.py:23-25
    # 2. Crear códigos y guardar TREE en preorden (raíz, izquierda, derecha).
    codigos = {}
    arbol = bytearray()
```

### En palabras sencillas

Son dos cajas vacías que la función `recorrer` irá llenando: `codigos` guardará el código de cada byte y `arbol` los bytes del campo TREE.

### Conclusión

Se usan un diccionario y un bytearray porque ambos se pueden **modificar** desde dentro de `recorrer` sin tener que devolverlos.

## Bloque 6 · La función recursiva recorrer

### Concepto

Para obtener los códigos y el TREE hay que visitar todos los nodos del árbol. Como el árbol está formado por árboles más pequeños, lo natural es una función **recursiva**: visitar un nodo consiste en anotarlo y después visitar sus dos hijos.

### Código real

```python comprimir.py:27-34
    def recorrer(nodo, codigo=""):
        if isinstance(nodo, int):
            codigos[nodo] = codigo or "0"  # Árbol de una sola hoja: código 0.
            arbol.extend((1, nodo))       # Hoja: 01 + símbolo
        else:
            arbol.extend((0, 0))          # Nodo interno: 00 00
            recorrer(nodo[0], codigo + "0")
            recorrer(nodo[1], codigo + "1")
```

### Instrucción por instrucción

<!-- anchos: 10, 51, 39 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 27 | Recibe un nodo y el camino recorrido hasta él (`codigo`). | El camino desde la raíz **es** el código. |
| 28 | Pregunta si el nodo es una hoja (un entero). | Es el **caso base**: ahí termina la recursión. |
| 29 | Guarda el código de ese byte; `codigo or "0"` usa `"0"` si el camino está vacío. | Solo pasa si el árbol es una única hoja (un solo símbolo). |
| 30 | Escribe `01` y el byte en TREE. | Marca de hoja más el símbolo. |
| 32 | Escribe `00 00` en TREE. | Marca de nodo interno, **antes** de sus hijos: eso es el preorden. |
| 33 | Visita el hijo izquierdo agregando `0` al camino. | Izquierda = 0. |
| 34 | Visita el hijo derecho agregando `1` al camino. | Derecha = 1. |

### Ejecución con AAAAABBC

La función se llama 5 veces, una por cada nodo. Cada recuadro muestra una llamada, con lo que recibe y lo que escribe:

```diagrama llamadas-recorrer
llamada 1 (raíz, "") → llamada 2 ((67, 66), "0") → llamadas 3 y 4 (C "00", B "01") → llamada 5 (A "1")
```

<!-- anchos: 10, 15, 20, 11, 20, 24 -->
<!-- tabla: recorrer -->
| Llamada | Profundidad | `nodo` | `codigo` | Escribe en TREE | Código guardado |
|---|---|---|---|---|---|
| 1 | 0 | `((67, 66), 65)` | `""` | 00 00 | - |
| 2 | 1 | `(67, 66)` | `"0"` | 00 00 | - |
| 3 | 2 | `67` | `"00"` | 01 43 | C = 00 |
| 4 | 2 | `66` | `"01"` | 01 42 | B = 01 |
| 5 | 1 | `65` | `"1"` | 01 41 | A = 1 |

### En palabras sencillas: la pila de llamadas

Cuando la llamada 2 hace la llamada 3, la 2 queda **en pausa**. La 3 es una hoja: escribe `01 43` y termina. Entonces la 2 continúa en su siguiente línea (la 34) y hace la llamada 4. Cuando la 4 termina, la 2 también termina y se reanuda la 1, que hace la llamada 5.

```calculo
llamada 1  (raíz)          escribe 00 00 y llama a su izquierda
  llamada 2  (67, 66)      escribe 00 00 y llama a su izquierda
    llamada 3  (67)        hoja: C = "00", escribe 01 43    → termina
    llamada 4  (66)        hoja: B = "01", escribe 01 42    → termina
  ← termina la llamada 2
  llamada 5  (65)          hoja: A = "1",  escribe 01 41    → termina
← termina la llamada 1
```

### Resultado

```calculo
codigos = {67: '00', 66: '01', 65: '1'}
arbol   = 00 00 00 00 01 43 01 42 01 41       (10 bytes)
```
<!-- comprobar: T.codigos == {67: "00", 66: "01", 65: "1"} and hexa(T.arbol) == "00 00 00 00 01 43 01 42 01 41" -->

### Conclusión

Una sola función produce **dos resultados** a la vez: los códigos (gracias al camino) y el TREE (gracias al orden de visita).

## Bloque 7 · Arrancar el recorrido

### Código real

```python comprimir.py:36-37
    if nodos:                 # Un archivo vacío no tiene árbol.
        recorrer(nodos[0][2])
```

### En palabras sencillas

`nodos[0]` es el único nodo que queda, `(8, 65, ((67, 66), 65))`, y `[2]` toma su tercer campo: el árbol. Si el archivo está vacío, `nodos` es una lista vacía, el `if` es falso y no hay nada que recorrer.

### Conclusión

Con un archivo vacío, `codigos` y `arbol` quedan vacíos: es el camino que lleva al resultado `00 00`.

## Bloque 8 · Bits, BS y ZIP

### Concepto

Se reemplaza cada byte por su código, se calcula BS, se rellena hasta completar el último byte y se convierten los bits en bytes reales.

### Código real

```python comprimir.py:39-46
    # 3. Empaquetar los bits y registrar cuántos son válidos en el último byte.
    bits = "".join(codigos[byte] for byte in datos)
    bs = 0
    zip_bytes = b""
    if bits:
        bs = len(bits) % 8 or 8
        bits += "0" * (8 - bs)
        zip_bytes = int(bits, 2).to_bytes(len(bits) // 8, "big")
```

### Instrucción por instrucción

<!-- anchos: 10, 36, 31, 23 -->
| Línea | Instrucción | Qué hace | Con AAAAABBC |
|---|---|---|---|
| 40 | `"".join(codigos[byte] for byte in datos)` | Pega el código de cada byte, en orden. | `"11111010100"` |
| 41-42 | `bs = 0` y `zip_bytes = b""` | Valores para el archivo vacío. | se reemplazan abajo |
| 43 | `if bits:` | Solo empaqueta si hay bits. | hay 11 bits |
| 44 | `len(bits) % 8 or 8` | Bits útiles del último byte. | `11 % 8 = 3` |
| 45 | `"0" * (8 - bs)` | Agrega el relleno. | 5 ceros |
| 46 | `int(bits, 2).to_bytes(len(bits) // 8, "big")` | Convierte los 16 bits en 2 bytes. | `b'\xfa\x80'` |

### Ejecución con AAAAABBC

```calculo
bits         = "11111010100"            len(bits) = 11
bs           = 11 % 8 or 8 = 3 or 8 = 3     (3 no es 0, así que se queda 3)
bits        += "0" * (8 - 3)   →  "1111101010000000"      len = 16
int(bits, 2) = 64128
len(bits) // 8 = 16 // 8 = 2 bytes
64128.to_bytes(2, "big") = b'\xfa\x80'   →  FA 80
```
<!-- comprobar: T.bits_relleno == "1111101010000000" and T.zip == b"\xfa\x80" -->

> [!ATENCION] El caso del 0 en `% 8 or 8`
> Con 16 bits, `16 % 8` daría 0 y `0 or 8` daría 8: el último byte está completo. Sin el `or 8`, BS valdría 0 y se agregarían 8 ceros de relleno, es decir, un byte entero de más.

### Conclusión

Las cadenas de bits son temporales; lo que se guarda es `zip_bytes`, que son **bytes reales**: 2 bytes para 11 bits.

## Bloque 9 · Armar el contenido del .pkz

### Código real

```python comprimir.py:48-50
    # 4. Guardar NF | TREE | BS | ZIP sin sobrescribir archivos.
    nf = max(0, len(frecuencias) - 1)
    contenido = bytes([nf]) + arbol + bytes([bs]) + zip_bytes
```

### Ejecución con AAAAABBC

```calculo
nf        = max(0, 3 - 1) = 2
contenido = bytes([2]) + arbol + bytes([3]) + zip_bytes
          = 02 | 00 00 00 00 01 43 01 42 01 41 | 03 | FA 80        (14 bytes)
```
<!-- comprobar: T.nf == 2 and hexa(T.contenido) == "02 00 00 00 00 01 43 01 42 01 41 03 FA 80" -->

### En palabras sencillas

`max(0, ...)` evita un número negativo: con un archivo vacío hay 0 símbolos y `0 - 1` daría -1. `bytes([nf])` convierte un número en un byte, y `+` pega los cuatro campos en orden.

### Conclusión

`contenido` es exactamente el formato del capítulo 3: **NF | TREE | BS | ZIP**.

## Bloque 10 · Guardar sin sobrescribir

### Código real

```python comprimir.py:52-58
    destino = Path(salida).expanduser() if salida else ruta.with_name(ruta.name + ".pkz")
    with destino.open("xb") as archivo_salida:
        archivo_salida.write(contenido)

    print(f"Original: {len(datos)} bytes | Comprimido: {len(contenido)} bytes")
    print(f"Guardado en: {destino}")
    return destino
```

### Instrucción por instrucción

<!-- anchos: 10, 50, 40 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 52 | Si hay `salida`, la usa; si no, agrega `.pkz` al nombre original. | `aaaaabbc.txt` → `aaaaabbc.txt.pkz` conserva el nombre original. |
| 53 | Abre en modo `"xb"`: crear (x) en binario (b). | Si el archivo ya existe, falla y **no lo toca**. |
| 54 | Escribe los 14 bytes. | `with` cierra el archivo al terminar, aunque haya un error. |
| 56-57 | Muestra los tamaños y la ruta. | Información para quien usa el programa. |
| 58 | Devuelve la ruta creada. | Permite usar la función desde otro programa. |

### Conclusión

La protección contra sobrescrituras no es una comprobación aparte: la da el modo `"xb"`, que pide al sistema operativo crear un archivo nuevo.

## Bloque 11 · Usarlo desde la terminal

### Código real

```python comprimir.py:61-67
if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python comprimir.py archivo [salida.pkz]")
    try:
        comprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(f"No se pudo comprimir: {error}")
```

### Instrucción por instrucción

<!-- anchos: 10, 90 -->
| Línea | Qué hace |
|---|---|
| 61 | Solo se ejecuta si el archivo se lanza directamente, no si otro programa lo importa. |
| 62-63 | `sys.argv` incluye el nombre del script: con 2 o 3 elementos hay archivo y, opcionalmente, salida. Si no, muestra cómo se usa. |
| 65 | `*sys.argv[1:]` reparte la lista como argumentos: `comprimir("aaaaabbc.txt")`. El asterisco **no** multiplica. |
| 66-67 | Si hay un error de archivos (`OSError`) o de datos (`ValueError`), muestra un mensaje breve y termina con código 1. |

### Ejecución con AAAAABBC

```terminal
> python comprimir.py aaaaabbc.txt
Original: 8 bytes | Comprimido: 14 bytes
Guardado en: aaaaabbc.txt.pkz
> python comprimir.py aaaaabbc.txt
No se pudo comprimir: [Errno 17] File exists: 'aaaaabbc.txt.pkz'
> python comprimir.py
Uso: python comprimir.py archivo [salida.pkz]
```

### Conclusión

La segunda orden falla a propósito: el `.pkz` ya existe y el programa se niega a reemplazarlo.

## Resumen de comprimir.py con AAAAABBC

<!-- anchos: 17, 53, 30 -->
| Variable | Valor final | Dónde se calcula |
|---|---|---|
| `datos` | `b'AAAAABBC'` | línea 9 |
| `frecuencias` | `Counter({65: 5, 66: 2, 67: 1})` | línea 10 |
| `nodos` | `[(8, 65, ((67, 66), 65))]` | líneas 15 a 21 |
| `codigos` | `{67: '00', 66: '01', 65: '1'}` | líneas 27 a 37 |
| `arbol` | `00 00 00 00 01 43 01 42 01 41` | líneas 27 a 37 |
| `bits` | `"1111101010000000"` (11 bits y 5 de relleno) | líneas 40 a 45 |
| `bs` | `3` | línea 44 |
| `zip_bytes` | `FA 80` | línea 46 |
| `nf` | `2` | línea 49 |
| `contenido` | `02 00 00 00 00 01 43 01 42 01 41 03 FA 80` | línea 50 |
<!-- comprobar: T.nodos_fin == [(8, 65, ((67, 66), 65))] and lc("bs = len(bits) % 8 or 8") == 44 and lc("nf = max(0") == 49 -->

# descomprimir.py por dentro

El descompresor hace el camino inverso: lee NF, reconstruye el árbol desde TREE, interpreta los bits de ZIP y escribe los bytes originales. No necesita el archivo original ni las frecuencias.

## El mapa del programa

```diagrama flujo-descomprimir
Leer y revisar → Reconstruir el árbol → BS y relleno → Decodificar → Guardar
```

<!-- anchos: 10, 12, 78 -->
| Bloque | Líneas | Qué hace |
|---|---|---|
| 1 | 1-10 | Importaciones, extensión y lectura del .pkz. |
| 2 | 12-13 | Prepara el resultado y reconoce el archivo vacío. |
| 3 | 14-20 | Lee NF y calcula dónde termina TREE. |
| 4 | 22-24 | Prepara la lectura del árbol. |
| 5 | 26-39 | `leer_arbol`: reconstruye el árbol con recursión. |
| 6 | 41-43 | Comprueba que el árbol coincide con NF. |
| 7 | 45-51 | Lee BS y ZIP y revisa el relleno. |
| 8 | 53-58 | Caso de un solo símbolo. |
| 9 | 59-69 | Recorre el árbol bit a bit. |
| 10 | 71-82 | Elige el nombre y guarda sin sobrescribir. |
| 11 | 85-91 | Permite usarlo desde la terminal. |
<!-- comprobar: [ld("datos = ruta.read_bytes()"), ld("recuperado = bytearray()"), ld("# 1. NF"), ld('raise ValueError("Faltan datos'), ld("# 2. Leer TREE"), ld("simbolos = set()"), ld("def leer_arbol"), ld("return (leer_arbol(), leer_arbol())"), ld("raiz = leer_arbol()"), ld('raise ValueError("TREE no coincide'), ld("# 3. Leer los bits"), ld('raise ValueError("Los bits de relleno'), ld("# 4. Decodificar"), ld("recuperado = bytes([raiz]) * cantidad"), ld("else:"), ld('raise ValueError("ZIP termina'), ld("# 5. Guardar"), ld("return destino"), ld("if __name__")] == [10, 12, 14, 20, 22, 24, 26, 39, 41, 43, 45, 51, 53, 58, 59, 69, 71, 82, 85] and NLINEAS["descomprimir.py"] == 91 -->

## Bloque 1 · Encabezado, extensión y lectura

### Código real

```python descomprimir.py:1-10
"""Descomprime Huffman .pkz/.huf. Uso: python descomprimir.py archivo.pkz [salida]"""
import sys
from pathlib import Path


def descomprimir(archivo, salida=None):
    ruta = Path(archivo).expanduser()
    if ruta.suffix.lower() not in (".pkz", ".huf"):
        raise ValueError("Selecciona un archivo .pkz o .huf")
    datos = ruta.read_bytes()
```

### Instrucción por instrucción

<!-- anchos: 10, 51, 39 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 8 | `ruta.suffix.lower()` obtiene la extensión en minúsculas. | Acepta `.pkz`, `.PKZ` o `.huf`. |
| 9 | Si la extensión no es válida, lanza un `ValueError`. | Evita intentar descomprimir, por ejemplo, un `.txt`. |
| 10 | Lee todo el `.pkz` como bytes. | El formato se analiza en memoria. |

### Ejecución con AAAAABBC

```calculo
ruta.suffix = ".pkz"        → extensión válida
datos = b'\x02\x00\x00\x00\x00\x01C\x01B\x01A\x03\xfa\x80'       (14 bytes)
```
<!-- comprobar: repr(T.pkz) == "b'\\x02\\x00\\x00\\x00\\x00\\x01C\\x01B\\x01A\\x03\\xfa\\x80'" -->

Python muestra `C`, `B` y `A` en lugar de `\x43`, `\x42` y `\x41` porque esos bytes corresponden a letras imprimibles; los valores son los mismos.

### Conclusión

Antes de leer, el programa ya descartó los archivos con una extensión equivocada.

## Bloque 2 · El archivo vacío

### Código real

```python descomprimir.py:12-13
    recuperado = bytearray()
    if datos != b"\x00\x00":  # Dos ceros representan un archivo vacío.
```

### En palabras sencillas

`recuperado` empieza vacío. Si el `.pkz` es exactamente `00 00`, todo el bloque siguiente se salta y se guarda un archivo vacío. Cualquier otro contenido entra al `if` para ser decodificado.

### Conclusión

Con AAAAABBC, `datos` no es `00 00`, así que el programa continúa.

## Bloque 3 · NF y dónde termina TREE

### Concepto

El primer byte es NF. Con él se calcula **dónde termina TREE**, que es justo donde está BS. Antes de seguir se comprueba que el archivo tenga, como mínimo, el TREE completo, BS y un byte de ZIP.

### Código real

```python descomprimir.py:14-20
        # 1. NF indica los nodos internos. El árbol tiene 2 * NF + 1 nodos.
        if not datos:
            raise ValueError("Falta la cabecera del archivo comprimido")
        nf = datos[0]
        fin_arbol = 1 + 2 * (2 * nf + 1)
        if len(datos) < fin_arbol + 2:
            raise ValueError("Faltan datos de TREE, BS o ZIP")
```

### Ejecución con AAAAABBC

```calculo
nf        = datos[0] = 2
fin_arbol = 1 + 2 × (2 × nf + 1)
          = 1 + 2 × (2 × 2 + 1)
          = 1 + 2 × 5
          = 1 + 10 = 11        (1 byte de NF + 10 bytes de TREE)

Comprobación: len(datos) = 14   y   fin_arbol + 2 = 13
              14 < 13 es falso → el archivo tiene todo lo necesario
```
<!-- comprobar: T.d_nf == 2 and T.fin_arbol == 11 and len(T.pkz) == 14 -->

### Instrucción por instrucción

<!-- anchos: 10, 90 -->
| Línea | Qué detecta |
|---|---|
| 15-16 | Un `.pkz` de 0 bytes: ni siquiera tiene NF. |
| 19-20 | Un archivo más corto que NF + TREE + BS + 1 byte de ZIP. El `+ 2` cuenta BS y ese primer byte de ZIP. |

### Conclusión

`fin_arbol` no se memoriza: sale de contar 1 byte de NF más 2 bytes por cada uno de los 2 × NF + 1 nodos.

## Bloque 4 · Preparar la lectura del árbol

### Código real

```python descomprimir.py:22-24
        # 2. Leer TREE en preorden. Cada nodo ocupa dos bytes.
        posicion = 1
        simbolos = set()
```

### En palabras sencillas

`posicion` es un **cursor** que indica qué par de bytes de TREE toca leer; empieza en 1, justo después de NF. `simbolos` es un conjunto que recuerda las hojas ya leídas, para detectar si alguna aparece repetida.

## Bloque 5 · leer_arbol: reconstruir el árbol

### Concepto

TREE se escribió en preorden, así que se lee igual: se lee un nodo y, si es interno, se lee completo su subárbol izquierdo y después el derecho. Otra vez, una función recursiva.

### Código real

```python descomprimir.py:26-39
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
```

### Instrucción por instrucción

<!-- anchos: 10, 51, 39 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 27 | `nonlocal posicion` | Para **modificar** el cursor de `descomprimir`, que comparten todas las llamadas. |
| 28-29 | Si el cursor ya llegó a `fin_arbol`, el árbol pide más nodos de los que hay. | Evita leer BS o ZIP como si fueran parte del árbol. |
| 30 | Toma el par de bytes actual: `tipo` y `valor`. | Cada nodo ocupa 2 bytes. |
| 31 | Avanza el cursor 2 posiciones. | El siguiente nodo empieza 2 bytes después. |
| 32-36 | Si `tipo` es 1, es una hoja: comprueba que no esté repetida y devuelve el byte. | Es el **caso base** de la recursión. |
| 37-38 | Si el par no es `(0, 0)`, no es válido. | Detecta un TREE dañado. |
| 39 | Nodo interno: lee el hijo izquierdo, luego el derecho, y devuelve la tupla. | Reconstruye `(izquierda, derecha)`. |

### Ejecución con AAAAABBC

En el diagrama, cada recuadro es una llamada a `leer_arbol` y muestra dónde estaba el cursor, qué par leyó y qué devolvió:

```diagrama llamadas-leer-arbol
llamada 1 (posicion 1, 00 00) → llamada 2 (posicion 3, 00 00) → llamadas 3 y 4 (C, B) → llamada 5 (A)
```

<!-- anchos: 11, 15, 12, 11, 9, 20, 22 -->
<!-- tabla: leer_arbol -->
| Llamada | Profundidad | `posicion` al leer | Bytes leídos | Tipo | Devuelve | `posicion` al terminar |
|---|---|---|---|---|---|---|
| 1 | 0 | 1 | 00 00 | interno | `((67, 66), 65)` | 11 |
| 2 | 1 | 3 | 00 00 | interno | `(67, 66)` | 9 |
| 3 | 2 | 5 | 01 43 | hoja | `67` | 7 |
| 4 | 2 | 7 | 01 42 | hoja | `66` | 9 |
| 5 | 1 | 9 | 01 41 | hoja | `65` | 11 |

### En palabras sencillas: el árbol se arma de abajo hacia arriba

Las llamadas **empiezan** de arriba hacia abajo (la raíz primero), pero **terminan** de abajo hacia arriba: primero devuelven las hojas y con ellas se arman los nodos internos.

```diagrama reconstruccion
67, 66 → (67, 66) → ((67, 66), 65)
```

```calculo
llamadas 3 y 4 devuelven 67 y 66     →  la llamada 2 arma (67, 66)
llamada 5 devuelve 65                →  la llamada 1 arma ((67, 66), 65)
```

### Resultado

`raiz = ((67, 66), 65)`: exactamente el mismo árbol que construyó el compresor.
<!-- comprobar: T.raiz_d == T.raiz == ((67, 66), 65) -->

### Conclusión

La última columna muestra por qué hace falta `nonlocal`: la llamada 2 termina con el cursor en 9 porque sus hijos (las llamadas 3 y 4) lo movieron.

## Bloque 6 · ¿Coincide el árbol con NF?

### Código real

```python descomprimir.py:41-43
        raiz = leer_arbol()
        if posicion != fin_arbol:
            raise ValueError("TREE no coincide con NF")
```

### En palabras sencillas

Si el árbol terminó antes de llegar a `fin_arbol`, NF prometía más nodos de los que tiene TREE. Con AAAAABBC, `posicion` termina en 11, igual que `fin_arbol`: todo cuadra.
<!-- comprobar: T.pos_final == T.fin_arbol == 11 -->

> [!IDEA] Una sola comprobación basta
> Un árbol en el que cada nodo interno tiene exactamente dos hijos y que ocupa 2 × NF + 1 nodos tiene, por fuerza, NF nodos internos y NF + 1 hojas. Por eso no hace falta contarlos por separado.

## Bloque 7 · BS, ZIP y el relleno

### Código real

```python descomprimir.py:45-51
        # 3. Leer los bits de ZIP. Del último byte solo valen los primeros BS bits.
        bs = datos[fin_arbol]
        zip_bytes = datos[fin_arbol + 1:]
        if not 1 <= bs <= 8:
            raise ValueError("BS debe estar entre 1 y 8")
        if "1" in f"{zip_bytes[-1]:08b}"[bs:]:  # Lo que sigue a BS es relleno.
            raise ValueError("Los bits de relleno no son cero")
```

### Ejecución con AAAAABBC

```calculo
bs            = datos[11] = 3
zip_bytes     = datos[12:] = b'\xfa\x80'          (FA 80)
1 <= 3 <= 8                                     → BS válido
zip_bytes[-1] = 128  →  f"{128:08b}" = "10000000"
"10000000"[3:] = "00000"                        → relleno sin ningún "1": válido
```
<!-- comprobar: T.d_bs == 3 and T.d_zip == b"\xfa\x80" and f"{T.d_zip[-1]:08b}"[T.d_bs:] == "00000" -->

### En palabras sencillas

`[bs:]` corta el texto del último byte justo donde terminan los datos: lo que queda es el relleno, que el compresor siempre llena con ceros. Si aparece un `1`, el archivo fue modificado.

### Conclusión

`1 <= bs <= 8` es una comparación encadenada: equivale a `1 <= bs and bs <= 8`.

## Bloque 8 · Un solo símbolo

### Concepto

Si la raíz es un entero, el árbol es una sola hoja y no hay caminos que seguir. Cada bit válido es una copia del símbolo, y todos esos bits deben ser `0`.

### Código real

```python descomprimir.py:53-58
        # 4. Decodificar: recorrer el árbol desde la raíz con cada bit válido.
        if isinstance(raiz, int):        # Un solo símbolo: cada bit válido es una copia.
            if any(zip_bytes):
                raise ValueError("El símbolo único debe tener código 0")
            cantidad = (len(zip_bytes) - 1) * 8 + bs
            recuperado = bytes([raiz]) * cantidad
```

### Ejecución con 17 letras X

AAAAABBC no pasa por aquí (su raíz es una tupla). Con el archivo de 17 X del capítulo 3:

```calculo
.pkz       = 00 | 01 58 | 01 | 00 00 00
raiz       = 88 (la X)        bs = 1        zip_bytes = 00 00 00
any(zip_bytes) = False        → todos los bits son 0
cantidad   = (3 - 1) × 8 + 1 = 2 × 8 + 1 = 17
recuperado = bytes([88]) × 17 = b'XXXXXXXXXXXXXXXXX'
```
<!-- comprobar: descomprimir_bytes(comprimir_bytes(b"X" * 17)) == b"X" * 17 and ord("X") == 88 -->

### Conclusión

Cada byte de ZIP aporta 8 bits, salvo el último, que aporta solo BS. Por eso la línea 57 calcula `(len(zip_bytes) - 1) * 8 + bs`.
<!-- comprobar: ld("cantidad = (len(zip_bytes) - 1) * 8 + bs") == 57 -->

## Bloque 9 · Recorrer el árbol bit a bit

### Concepto

Para cada byte de ZIP se toman sus bits (8, o solo BS si es el último) y con cada bit se baja un nivel: `0` a la izquierda, `1` a la derecha. Al llegar a una hoja se agrega su byte al resultado y se vuelve a la raíz.

### Código real

```python descomprimir.py:59-69
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
```

### Instrucción por instrucción

<!-- anchos: 10, 51, 39 -->
| Línea | Qué hace | Por qué |
|---|---|---|
| 60 | Empieza en la raíz. | Todo código se lee desde la raíz. |
| 61 | Recorre los bytes de ZIP numerándolos desde 1. | Así el último cumple `indice == len(zip_bytes)`. |
| 62 | Del último byte usa solo BS bits; de los demás, 8. | Descarta el relleno. |
| 63 | Recorre los bits del byte como texto. | `f"{byte:08b}"` da los 8 bits con ceros a la izquierda. |
| 64 | `nodo[int(bit)]` baja al hijo 0 o al hijo 1. | El índice de la tupla **es** la dirección. |
| 65-67 | Si llegó a una hoja, guarda el byte y vuelve a la raíz. | Terminó un código; empieza el siguiente. |
| 68-69 | Si al final no está en la raíz, quedó un código a medias. | Detecta un ZIP cortado o un BS dañado. |

### Ejecución con AAAAABBC

<!-- anchos: 8, 15, 12, 8, 14, 14, 12 -->
<!-- tabla: pasos -->
| Paso | Byte (`indice`) | Bit del byte | Bit | Dirección | Llega a | Recupera |
|---|---|---|---|---|---|---|
| 1 | 1 (FA) | 1 | 1 | derecha | hoja A | A |
| 2 | 1 (FA) | 2 | 1 | derecha | hoja A | A |
| 3 | 1 (FA) | 3 | 1 | derecha | hoja A | A |
| 4 | 1 (FA) | 4 | 1 | derecha | hoja A | A |
| 5 | 1 (FA) | 5 | 1 | derecha | hoja A | A |
| 6 | 1 (FA) | 6 | 0 | izquierda | interno | - |
| 7 | 1 (FA) | 7 | 1 | derecha | hoja B | B |
| 8 | 1 (FA) | 8 | 0 | izquierda | interno | - |
| 9 | 2 (80) | 1 | 1 | derecha | hoja B | B |
| 10 | 2 (80) | 2 | 0 | izquierda | interno | - |
| 11 | 2 (80) | 3 | 0 | izquierda | hoja C | C |

Cada panel muestra en naranja el camino de un código:

```diagrama recorrido-bits
1 → A (×5)  |  0 1 → B  |  0 | 1 → B (cruza bytes)  |  0 0 → C
```

### Resultado

`recuperado = AAAAABBC` (8 bytes). En el paso 8 el cursor quedó en el nodo interno y continuó desde ahí con el primer bit del byte 2: un código puede cruzar de un byte al siguiente.
<!-- comprobar: T.recuperado == b"AAAAABBC" and len(T.pasos) == 11 -->

### Conclusión

Solo se leyeron 11 bits (8 + BS); los 5 ceros de relleno nunca entraron al recorrido.

## Bloque 10 · Elegir el nombre y guardar

### Código real

```python descomprimir.py:71-82
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
```

### Instrucción por instrucción

<!-- anchos: 10, 55, 35 -->
| Línea | Qué hace | Con AAAAABBC |
|---|---|---|
| 72 | Quita los 4 últimos caracteres (`.pkz`) para obtener el nombre original. | `aaaaabbc.txt` |
| 73-74 | Sin salida explícita, rechaza nombres que no sirven: vacío, `.` o `..` (por ejemplo, el archivo `..pkz`). | no aplica |
| 75 | Destino: la salida indicada o la carpeta `recuperados` junto al `.pkz`. | `recuperados\aaaaabbc.txt` |
| 76 | Crea la carpeta si no existe. | crea `recuperados` |
| 77-78 | Escribe en modo `"xb"`: nunca reemplaza un archivo existente. | 8 bytes |
| 80-82 | Muestra el resultado y devuelve la ruta. | ver la terminal abajo |

> [!ATENCION] ¿Qué pasaría sin la comprobación del nombre?
> Con `..pkz` el nombre sería `.`, y la ruta `recuperados/.` es la propia carpeta: el programa crearía un **archivo** llamado `recuperados` en lugar de una carpeta. Con `...pkz` el nombre sería `..` y la ruta apuntaría a la carpeta que contiene `recuperados`.

### Conclusión

La salida se crea al final, solo cuando todo se validó y decodificó: un `.pkz` dañado nunca deja un archivo recuperado a medias.

## Bloque 11 · Usarlo desde la terminal

### Código real

```python descomprimir.py:85-91
if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Uso: python descomprimir.py archivo.pkz [salida]")
    try:
        descomprimir(*sys.argv[1:])
    except (OSError, ValueError) as error:
        sys.exit(f"No se pudo descomprimir: {error}")
```

Funciona igual que el bloque 11 de `comprimir.py`. Aquí `ValueError` cubre todas las validaciones del formato.

### Ejecución con AAAAABBC

```terminal
> python descomprimir.py aaaaabbc.txt.pkz
Recuperado: 8 bytes
Guardado en: recuperados\aaaaabbc.txt
> python descomprimir.py aaaaabbc.txt.pkz
No se pudo descomprimir: [Errno 17] File exists: 'recuperados\\aaaaabbc.txt'
> python descomprimir.py aaaaabbc.txt
No se pudo descomprimir: Selecciona un archivo .pkz o .huf
```

### Conclusión

El archivo recuperado tiene los mismos 8 bytes que el original: la compresión es **sin pérdida**. La segunda orden falla porque el recuperado ya existe, y la tercera porque `.txt` no es un archivo comprimido.

## Resumen de descomprimir.py con AAAAABBC

<!-- anchos: 18, 47, 35 -->
| Variable | Valor | Dónde |
|---|---|---|
| `nf` | `2` | línea 17 |
| `fin_arbol` | `11` | línea 18 |
| `raiz` | `((67, 66), 65)` | línea 41 |
| `bs` | `3` | línea 46 |
| `zip_bytes` | `FA 80` | línea 47 |
| `recuperado` | `AAAAABBC` (8 bytes) | líneas 59 a 69 |
| `destino` | `recuperados\aaaaabbc.txt` | línea 75 |
<!-- comprobar: [ld("nf = datos[0]"), ld("fin_arbol = 1 + 2"), ld("raiz = leer_arbol()"), ld("bs = datos[fin_arbol]"), ld("zip_bytes = datos[fin_arbol + 1:]"), ld("destino = Path(salida)")] == [17, 18, 41, 46, 47, 75] -->

# Validaciones y casos límite

Un buen descompresor no solo funciona con archivos correctos: también reconoce los dañados y explica qué pasa. Todos los mensajes de este capítulo son los que muestra el programa real.

## Cada validación, con un archivo de prueba

### Concepto

Cada uno de los 12 `raise ValueError` de `descomprimir.py` detecta un problema distinto. Para verlos en acción se preparó un archivo con cada defecto, casi siempre a partir del `.pkz` correcto de AAAAABBC, que es `02 00 00 00 00 01 43 01 42 01 41 03 FA 80`.
<!-- comprobar: sum("raise ValueError" in l for l in CODIGO["descomprimir.py"]) == 12 -->

### Ejecución con AAAAABBC

<!-- anchos: 11, 33, 28, 28 -->
<!-- tabla: errores -->
| Archivo | Contenido (hex) | Qué tiene de malo | Mensaje real |
|---|---|---|---|
| caso.txt | 02 00 00 00 00 01 43 01 42 01 41 03 FA 80 | La extensión no es .pkz ni .huf | Selecciona un archivo .pkz o .huf |
| caso.pkz | (vacío) | No tiene ni siquiera NF | Falta la cabecera del archivo comprimido |
| caso.pkz | 02 00 00 00 00 01 43 | TREE cortado; faltan BS y ZIP | Faltan datos de TREE, BS o ZIP |
| caso.pkz | 01 00 00 00 00 01 43 01 42 01 41 03 FA 80 | NF = 1, pero el árbol pide más nodos | Árbol incompleto |
| caso.pkz | 03 00 00 00 00 01 43 01 42 01 41 00 00 00 00 03 FA 80 | NF = 3, pero el árbol termina antes | TREE no coincide con NF |
| caso.pkz | 02 00 00 00 00 02 43 01 42 01 41 03 FA 80 | Marcador 02: no es hoja ni interno | Nodo inválido en TREE |
| caso.pkz | 02 00 00 00 00 01 43 01 43 01 41 03 FA 80 | La hoja C aparece dos veces | Símbolo repetido en TREE |
| caso.pkz | 02 00 00 00 00 01 43 01 42 01 41 00 FA 80 | BS = 0 | BS debe estar entre 1 y 8 |
| caso.pkz | 02 00 00 00 00 01 43 01 42 01 41 03 FA 81 | Hay un 1 en el relleno (81 = 10000001) | Los bits de relleno no son cero |
| caso.pkz | 02 00 00 00 00 01 43 01 42 01 41 02 FA 80 | BS = 2: los bits terminan dentro de un código | ZIP termina a mitad de un código |
| caso.pkz | 00 01 41 01 80 | Un solo símbolo, pero con un bit 1 | El símbolo único debe tener código 0 |
| ..pkz | 02 00 00 00 00 01 43 01 42 01 41 03 FA 80 | Al quitar .pkz, el nombre queda «.» | El archivo no tiene un nombre original válido |

### Conclusión

Cada validación protege contra un tipo de daño concreto, y ninguna repite el trabajo de otra.

## Lo que el formato no puede detectar

### Concepto

El formato no guarda una suma de verificación (*checksum*) ni la longitud original. Si un byte de ZIP cambia pero la estructura sigue siendo válida, el descompresor no tiene forma de saberlo.

### Ejecución con AAAAABBC

Cambia el byte FA por FB: el último bit del primer byte pasa de 0 a 1.

```calculo
ZIP original:  11111010 100   → 1 1 1 1 1 01 01 00  → A A A A A B B C
ZIP alterado:  11111011 100   → 1 1 1 1 1 01 1 1 00 → A A A A A B A A C
                                                     (9 bytes y ningún error)
```
<!-- comprobar: descomprimir_bytes(bytes.fromhex("0200000000014301420141" + "03FB80")) == b"AAAAABAAC" -->

### Conclusión

Las validaciones detectan **errores de estructura**, no cualquier alteración. Es una limitación conocida que conviene mencionar en la exposición.

## Archivos vacíos y de un solo símbolo, de principio a fin

Los archivos `vacio.txt` (0 bytes) y `equis.txt` (17 letras X) se comprimen y se recuperan sin problema:

```terminal
> python comprimir.py vacio.txt
Original: 0 bytes | Comprimido: 2 bytes
Guardado en: vacio.txt.pkz
> python descomprimir.py vacio.txt.pkz
Recuperado: 0 bytes
Guardado en: recuperados\vacio.txt
> python comprimir.py equis.txt
Original: 17 bytes | Comprimido: 7 bytes
Guardado en: equis.txt.pkz
> python descomprimir.py equis.txt.pkz
Recuperado: 17 bytes
Guardado en: recuperados\equis.txt
```

## Nombres sin original

Se puede elegir cualquier nombre de salida al comprimir, incluso uno que después no sirva para descomprimir sin más:

```terminal
> python comprimir.py aaaaabbc.txt ..pkz
Original: 8 bytes | Comprimido: 14 bytes
Guardado en: ..pkz
> python descomprimir.py ..pkz
No se pudo descomprimir: El archivo no tiene un nombre original válido
> python descomprimir.py ..pkz copia.txt
Recuperado: 8 bytes
Guardado en: copia.txt
```

Con un nombre de salida explícito el problema desaparece, porque ya no se usa el nombre del `.pkz`.

# Ejercicios resueltos

Intenta resolver cada ejercicio antes de leer la solución. Todas las soluciones se comprobaron con los programas reales.

## Un mensaje con empate: ABBCCC

> [!EJERCICIO] Construye el árbol, los códigos y el .pkz de ABBCCC
> Las frecuencias son A = 1, B = 2 y C = 3. Atención: en la segunda vuelta hay un empate.

> [!SOLUCION]
> ```calculo
> Inicio:    A·1   B·2   C·3
> Vuelta 1:  A·1 + B·2 = 3      A a la izquierda, B a la derecha
>            mínimo = min(65, 66) = 65
>            quedan (3, 65, grupo AB) y (3, 67, C)
> Vuelta 2:  empate a 3 → decide el byte mínimo: 65 < 67
>            el grupo AB va a la izquierda (0) y C a la derecha (1)
> Códigos:   A = 00    B = 01    C = 1
> Bits:      A  B  B  C C C → 00 01 01 1 1 1 → 000101111   (9 bits)
> BS:        9 % 8 = 1            relleno = 8 - 1 = 7 ceros
> ZIP:       00010111 10000000 → 17 80
> TREE:      00 00   00 00   01 41   01 42   01 43
> !.pkz = 02 | 00 00 00 00 01 41 01 42 01 43 | 01 | 17 80
> ```
> El programa real produce exactamente esos bytes:
> ```terminal
> > python comprimir.py abbccc.txt
> Original: 6 bytes | Comprimido: 14 bytes
> Guardado en: abbccc.txt.pkz
> ```
<!-- comprobar: hexa(T2.pkz) == "02 00 00 00 00 01 41 01 42 01 43 01 17 80" and T2.codigos == {65: "00", 66: "01", 67: "1"} and T2.vueltas[1]["ordenada"] == [(3, 65, (65, 66)), (3, 67, 67)] -->

## ¿Cuánto vale BS?

> [!EJERCICIO] Calcula BS para mensajes de 1, 7, 8, 9, 16 y 17 bits
> Usa la regla de la línea 44: `len(bits) % 8 or 8`.

> [!SOLUCION]
> <!-- tabla: bs -->
> | Bits | Cálculo | BS |
> |---|---|---|
> | 1 | 1 % 8 = 1 | 1 |
> | 7 | 7 % 8 = 7 | 7 |
> | 8 | 8 % 8 = 0 → 0 or 8 | 8 |
> | 9 | 9 % 8 = 1 | 1 |
> | 16 | 16 % 8 = 0 → 0 or 8 | 8 |
> | 17 | 17 % 8 = 1 | 1 |
>
> Se comprobó comprimiendo archivos de 1, 7, 8, 9, 16 y 17 letras X: con un solo símbolo, cada letra ocupa 1 bit.

## Un solo símbolo

> [!EJERCICIO] ¿Cómo queda el .pkz de 17 letras X? ¿Cuántas X recupera el descompresor?

> [!SOLUCION]
> ```calculo
> NF = 1 - 1 = 0          TREE = 01 58   (una hoja: la X es el byte 88 = 58 en hex)
> Código de la X = "0"    17 bits = 2 bytes completos + 1 bit  → BS = 1
> ZIP = 00 00 00          .pkz = 00 | 01 58 | 01 | 00 00 00   (7 bytes)
> Recupera: (3 - 1) × 8 + 1 = 17 letras X
> ```
<!-- comprobar: hexa(comprimir_bytes(b"X" * 17)) == "00 01 58 01 00 00 00" and 0x58 == 88 -->

## El archivo vacío

> [!EJERCICIO] ¿Qué guarda el compresor para un archivo de 0 bytes y cómo lo reconoce el descompresor?

> [!SOLUCION]
> No hay frecuencias, así que `nodos` está vacío y no se llama a `recorrer`; `bits` es `""`, BS y ZIP conservan sus valores iniciales (`0` y `b""`) y NF = `max(0, 0 - 1) = 0`. El resultado es `00 00`. El descompresor compara el contenido con `b"\x00\x00"` (línea 13) y no entra al bloque de decodificación.
<!-- comprobar: comprimir_bytes(b"") == b"\x00\x00" and ld('if datos != b"\\x00\\x00"') == 13 -->

## Decodificar a mano

> [!EJERCICIO] Descomprime a mano 02 00 00 00 00 01 41 01 42 01 43 01 17 80

> [!SOLUCION]
> ```calculo
> NF = 2 → fin_arbol = 11     TREE: raíz, interno, A, B, C → ((65, 66), 67)
> Códigos: A = 00, B = 01, C = 1         BS = 01 → 1 bit útil en el último byte
> ZIP: 17 80 → 00010111 | 1 0000000
> Bits útiles: 000101111
> 00 → A    01 → B    01 → B    1 → C    1 → C    1 → C
> !Resultado: ABBCCC
> ```
<!-- comprobar: descomprimir_bytes(bytes.fromhex("0200000000014101420143011780")) == b"ABBCCC" -->

## Calcular fin_arbol

> [!EJERCICIO] ¿En qué índice está BS si NF vale 0, 2 o 255?

> [!SOLUCION]
> ```calculo
> NF = 0:    1 + 2 × (2 × 0 + 1)   = 1 + 2 × 1   = 3
> NF = 2:    1 + 2 × (2 × 2 + 1)   = 1 + 2 × 5   = 11
> NF = 255:  1 + 2 × (2 × 255 + 1) = 1 + 2 × 511 = 1023
> ```
> Con 256 bytes distintos, que es el máximo, TREE ocupa 1022 bytes.
<!-- comprobar: [1 + 2 * (2 * nf + 1) for nf in (0, 2, 255)] == [3, 11, 1023] and len(comprimir_bytes(bytes(range(256)))) == 1 + 1022 + 1 + 256 -->

## Binario y hexadecimal

> [!EJERCICIO] Convierte a hexadecimal 11111010 y 00010111, y a binario el byte 80

> [!SOLUCION]
> ```calculo
> 11111010 = 1111 1010 = F A → FA        (128 + 64 + 32 + 16 + 8 + 2 = 250)
> 00010111 = 0001 0111 = 1 7 → 17        (16 + 4 + 2 + 1 = 23)
> 80       = 8 0 = 1000 0000 → 10000000  (128)
> ```
<!-- comprobar: int("11111010", 2) == 0xFA == 250 and int("00010111", 2) == 0x17 == 23 and f"{0x80:08b}" == "10000000" -->

## Identificar el error

> [!EJERCICIO] ¿Qué mensaje muestra el descompresor con 02 00 00 00 00 01 43 01 42 01 41 09 FA 80?

> [!SOLUCION]
> El byte del índice 11 es BS y vale 09: está fuera del rango de 1 a 8. El mensaje es «BS debe estar entre 1 y 8».
<!-- comprobar: descomprimir_bytes(bytes.fromhex("0200000000014301420141" + "09FA80")) == "BS debe estar entre 1 y 8" -->

## Eficiencia del código

> [!EJERCICIO] ¿Cuántos bits por letra usa en promedio el código de AAAAABBC? ¿Y el de ABBCCC?

> [!SOLUCION]
> ```calculo
> AAAAABBC:  11 bits ÷ 8 letras = 1,375 bits por letra
> ABBCCC:     9 bits ÷ 6 letras = 1,5 bits por letra
> ```
> En ambos casos se usa mucho menos que los 8 bits de un byte.
<!-- comprobar: len(T.bits_datos) / 8 == 1.375 and len(T2.bits_datos) / 6 == 1.5 -->

# Preguntas de exposición

Respuestas breves a las preguntas más frecuentes. Responde siempre con el mecanismo («porque el árbol se guarda en preorden…»), no solo con el nombre de una función.

## Sobre el algoritmo

**¿Qué es Huffman y por qué comprime?**

Es un algoritmo que asigna códigos binarios de longitud variable: cortos a los bytes frecuentes y largos a los raros. Como lo frecuente aparece muchas veces, el total de bits baja.

**¿Por qué se dice que es voraz?**

En cada paso une los dos nodos de menor frecuencia y nunca deshace esa decisión. Esa elección local conduce al resultado óptimo.

**¿Qué garantiza Huffman?**

Para unas frecuencias dadas, produce el código prefijo con el menor número total de bits. No garantiza que el archivo completo sea más pequeño, porque también hay que guardar el árbol.

**¿Por qué no hacen falta separadores entre códigos?**

Porque es un código prefijo: los símbolos solo están en las hojas, así que ningún código es el comienzo de otro.

**¿Qué pasa si dos nodos tienen la misma frecuencia?**

Va primero el que contiene el byte más pequeño (el segundo campo de la tupla). Así el resultado es siempre el mismo.

## Sobre el formato

**¿Qué contiene un .pkz?**

NF (nodos internos), TREE (el árbol en preorden), BS (bits útiles del último byte) y ZIP (los bits comprimidos).

**¿Se guardan las frecuencias?**

No. Solo la forma del árbol y los bytes de sus hojas: es todo lo que hace falta para decodificar.

**¿Por qué BS puede valer 8 y no 0?**

Porque cuando el último byte está completo tiene 8 bits útiles. El 0 se reserva para el archivo vacío.

**¿Cómo se representa un archivo vacío?**

Con exactamente dos bytes: `00 00`.

**¿Por qué cada nodo de TREE ocupa dos bytes?**

El primero dice si es hoja (`01`) o interno (`00`); el segundo es el símbolo. Sin el marcador, una hoja del byte 0 se confundiría con un nodo interno.

## Sobre el código

**¿Cómo representa el programa el árbol?**

Con tuplas anidadas: una hoja es un entero y un nodo interno es `(izquierda, derecha)`. El árbol de AAAAABBC queda así: `((67, 66), 65)`.

**¿Por qué cada nodo de la lista tiene tres valores?**

`(frecuencia, byte mínimo, árbol)`: la frecuencia para ordenar, el byte mínimo para desempatar y el árbol como contenido.

**¿Por qué ordenar una lista y no usar heapq?**

Hay como máximo 256 nodos: ordenar en cada vuelta es instantáneo y más fácil de explicar. El árbol resultante es el mismo.

**¿Para qué sirve nonlocal en leer_arbol?**

Para que todas las llamadas recursivas lean y avancen el mismo cursor `posicion`, que pertenece a `descomprimir`. Como `leer_arbol` asigna `posicion += 2`, sin `nonlocal` Python la trataría como una variable local nueva y todavía sin valor: la línea 28 fallaría con `UnboundLocalError` en la primera llamada.
<!-- comprobar: error_sin_linea("nonlocal posicion") == ("UnboundLocalError", ld("if posicion == fin_arbol:")) and ld("if posicion == fin_arbol:") == 28 -->

**¿Necesita el descompresor el archivo original?**

No. Todo está en el `.pkz`: el árbol (TREE) y los bits (ZIP), junto con NF y BS.

**¿Cómo se evita sobrescribir archivos?**

Abriendo la salida en modo `"xb"`: el sistema operativo se niega a crear un archivo que ya existe.

## Sobre los límites

**¿Por qué el ejemplo crece en lugar de reducirse?**

Porque 8 bytes son muy pocos: NF, TREE y BS ocupan 12 de los 14 bytes del `.pkz`.

**¿Por qué un video o un archivo ya comprimido casi no cambia?**

Sus bytes aparecen con frecuencias casi iguales, así que no hay símbolos frecuentes que aprovechar.

**¿Detecta cualquier archivo dañado?**

No. Detecta errores de estructura, pero no tiene *checksum*: un bit cambiado en ZIP puede producir otro contenido sin ningún error.

**¿Hay un tamaño máximo?**

No hay un límite en el código, pero todo se hace en memoria (`read_bytes` y cadenas de bits), así que depende de la RAM del equipo.

**¿Por qué tu .pkz no es idéntico al de la carpeta de demostración?**

Esos archivos se crearon con otra herramienta que desempata de otra forma. Tienen el mismo tamaño y se descomprimen igual: ambos árboles son óptimos.
<!-- comprobar: all(len(nuevo) == len(original) and nuevo != original and igual for original, nuevo, igual in map(recomprimir_demo, ("doc.doc.pkz", "NRC-AL-65074.xlsx.pkz", "pdf.pdf.pkz"))) -->

# Glosario

## Términos de Huffman y compresión

<!-- anchos: 20, 55, 25 -->
| Término | Significado | Dónde aparece |
|---|---|---|
| Bit | La unidad mínima de información: 0 o 1. | Todo el proyecto |
| Byte | Grupo de 8 bits; vale de 0 a 255. | `datos`, `zip_bytes` |
| Frecuencia | Cantidad de veces que aparece un byte. | `frecuencias` |
| Código prefijo | Conjunto de códigos en el que ninguno es el comienzo de otro. | Capítulo 1 |
| Árbol binario | Estructura en la que cada nodo interno tiene dos hijos. | `raiz` |
| Raíz | El nodo de arriba, donde empieza todo camino. | `nodos[0][2]`, `raiz` |
| Nodo interno | Nodo con dos hijos; no contiene símbolo. | Tupla `(izquierda, derecha)` |
| Hoja | Nodo sin hijos; contiene un byte. | Un entero |
| Peso | Suma de las frecuencias de las hojas de un subárbol. | `peso_izq + peso_der` |
| Algoritmo voraz | El que en cada paso toma la mejor decisión local. | Ciclo `while` del compresor |
| Desempate | Regla para decidir entre nodos con la misma frecuencia. | Byte mínimo |
| Preorden | Recorrido: nodo, subárbol izquierdo y subárbol derecho. | `recorrer`, `leer_arbol` |
| NF | Número de nodos internos; primer byte del `.pkz`. | Capítulo 3 |
| TREE | El árbol guardado en preorden, 2 bytes por nodo. | `arbol` |
| BS | Bits útiles del último byte de ZIP (de 1 a 8). | `bs` |
| ZIP | Los bits del mensaje empaquetados en bytes. | `zip_bytes` |
| Relleno | Ceros que completan el último byte. | `"0" * (8 - bs)` |
| Entropía | Mínimo teórico de bits por símbolo. | Capítulo 2 |
| Sin pérdida | La recuperación es idéntica, byte a byte. | Objetivo del proyecto |
| Checksum | Suma de verificación para detectar cambios; este formato no la tiene. | Capítulo 7 |

## Términos de Python

<!-- anchos: 24, 46, 30 -->
| Término | Qué es | Ejemplo en el proyecto |
|---|---|---|
| `bytes` | Secuencia inmutable de enteros de 0 a 255. | `ruta.read_bytes()` |
| `bytearray` | Como `bytes`, pero se puede modificar. | `arbol = bytearray()` |
| `Counter` | Diccionario que cuenta apariciones. | `Counter(datos)` |
| Tupla | Grupo de valores entre paréntesis; se compara elemento por elemento. | `(frecuencia, byte, byte)` |
| Lista | Secuencia que se puede modificar. | `nodos` |
| `sort()` | Ordena la lista en su lugar. | `nodos.sort()` |
| `pop(0)` | Quita y devuelve el primer elemento. | `nodos.pop(0)` |
| `append()` | Agrega un elemento al final. | `nodos.append(...)` |
| Diccionario | Asocia claves con valores. | `codigos[nodo] = ...` |
| Conjunto (`set`) | Colección sin repetidos; `in` pregunta si contiene algo. | `simbolos` |
| `isinstance(x, int)` | Pregunta si `x` es un entero. | Detectar hojas |
| Recursión | Función que se llama a sí misma. | `recorrer`, `leer_arbol` |
| Caso base | Situación en la que la recursión termina. | La hoja |
| `nonlocal` | Permite modificar una variable de la función exterior. | `posicion` |
| Generador | Expresión que produce valores uno a uno. | `codigos[byte] for byte in datos` |
| `join` | Une varias cadenas en una. | `"".join(...)` |
| `%` (módulo) | Resto de una división. | `len(bits) % 8` |
| `x or y` | Devuelve `x` si no es 0 ni vacío; si no, `y`. | `codigo or "0"` |
| `int(texto, 2)` | Lee un texto como número binario. | `int(bits, 2)` |
| `to_bytes(n, "big")` | Escribe un entero en `n` bytes, del más significativo al menos. | `zip_bytes` |
| `f"{x:08b}"` | Escribe `x` en binario con 8 cifras. | `f"{byte:08b}"` |
| Rebanada | Parte de una secuencia: `a[i:j]`. | `datos[posicion:posicion + 2]` |
| `enumerate(..., start=1)` | Recorre y numera desde 1. | Bytes de ZIP |
| `Path` | Ruta de archivo con métodos útiles. | `Path(archivo)` |
| Modo `"xb"` | Crea un archivo binario nuevo; falla si ya existe. | Protección contra sobrescrituras |
| `with` | Asegura que el archivo se cierre al terminar. | `with destino.open("xb")` |
| `try` / `except` | Captura errores para mostrar un mensaje breve. | Bloque de terminal |
| `sys.argv` | Las palabras escritas en la terminal. | `*sys.argv[1:]` |
| `sys.exit()` | Termina el programa mostrando un mensaje. | Mensajes de uso y de error |
| `ValueError` / `OSError` | Errores de datos / de archivos. | Validaciones y lectura |
| `__name__ == "__main__"` | Es verdadero si el archivo se ejecuta directamente. | Bloque de terminal |

# Apéndice A. Código completo de comprimir.py {-}

Versión definitiva: 67 líneas, commit 6dd8539. Úsalo para repasar el programa de corrido después de estudiar los bloques del capítulo 5.

```python comprimir.py:1-67
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
```

# Apéndice B. Código completo de descomprimir.py {-}

Versión definitiva: 91 líneas, commit 6dd8539. Corresponde a los bloques del capítulo 6.

```python descomprimir.py:1-91
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
```

# Apéndice C. Cómo se comprobó esta guía {-}

Esta guía no se escribió a ojo: el generador `output/guia_estudio/generar_guia_estudio.py` la contrasta con los programas reales antes de producir el PDF.

- Cada fragmento de código se compara, línea por línea, con `comprimir.py` y `descomprimir.py`.
- Los ejemplos de Python del capítulo 4 se ejecutan y su salida se compara con la que muestra la guía.
- Las sesiones de terminal se ejecutan con los dos programas en una carpeta temporal.
- Las tablas de valores (vueltas del ciclo, llamadas recursivas, recorrido bit a bit y errores) se comparan con una ejecución trazada de los programas.
- Cada cálculo lleva junto a él una comprobación automática que se evalúa con esos mismos datos.

Si alguna explicación dejara de coincidir con el código, el generador se detiene e indica la línea de la guía que hay que corregir. Para volver a generar el PDF, ejecuta desde la carpeta del proyecto:

```texto
python output/guia_estudio/generar_guia_estudio.py
```

<!-- anchos: 22, 10, 68 -->
| Archivo | Líneas | SHA-256 |
|---|---|---|
| comprimir.py | 67 | `38fbd12cf74fbbe264cdb5062abd8836396a2cf4a8809424ea0bce9409cc87cd` |
| descomprimir.py | 91 | `545459f5158e3398b6384bfc319c70d9fdfed44ff3183264073ceedec1cd7993` |
<!-- comprobar: SHA["comprimir.py"] == "38fbd12cf74fbbe264cdb5062abd8836396a2cf4a8809424ea0bce9409cc87cd" and SHA["descomprimir.py"] == "545459f5158e3398b6384bfc319c70d9fdfed44ff3183264073ceedec1cd7993" and COMMIT == "6dd8539" -->
