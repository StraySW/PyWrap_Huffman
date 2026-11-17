# PyWrap · Huffman en Python

Proyecto universitario de Diseño de Algoritmos, Ingeniería de Sistemas, UNIMINUTO. Aplicación de escritorio que comprime y recupera archivos mediante Huffman implementado manualmente. Conserva el algoritmo, la interfaz y el formato funcionales del repositorio inicial, con operaciones de archivo separadas, protección de destinos y visualización educativa del algoritmo.

Trabaja con **bytes**, sin interpretar la extensión ni convertir texto: admite TXT, PDF, imágenes, videos y cualquier archivo binario. No requiere paquetes de `pip`.

**Documentación de entrega y sustentación:**

- [Instalación y migración entre computadores: macOS y Windows](docs/INSTALACION_Y_MIGRACION.md)
- [Informe académico](docs/INFORME_ACADEMICO.md)
- [Guía de sustentación](docs/GUIA_SUSTENTACION.md)
- [Preguntas probables](docs/PREGUNTAS_SUSTENTACION.md)
- [Demostración reproducible](docs/DEMO.md)

## Instalación y ejecución en macOS

El algoritmo y la consola funcionan desde Python 3.9; para una instalación nueva se recomienda Python 3.11 o posterior. La interfaz requiere Tkinter; en macOS, Tcl/Tk 8.6 o posterior.

1. Instala Python desde [python.org para macOS](https://www.python.org/downloads/macos/). Sus instaladores incluyen Tcl/Tk: [documentación oficial](https://www.python.org/download/mac/tcltk/).
2. Abre una **terminal nueva**, entra en la carpeta del proyecto y comprueba:

   ```bash
   python3 --version
   python3 -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
   python3 -m tkinter
   ```

   El último comando debe abrir una ventana de prueba; ciérrala para continuar.
3. Ejecuta:

   ```bash
   python3 main.py
   ```

Selecciona **Comprimir**, elige el archivo con **Examinar** y pulsa **Ejecutar**. El resultado queda en `data/wrp/`. Selecciona **Descomprimir** y abre el `.pkz`: la recuperación queda en `data/unwrp/`. La consola muestra las rutas completas, tamaños exactos y estadísticas. La barra animada indica actividad, sin estimar un porcentaje. No cierres la aplicación durante una operación.

Las carpetas de salida se crean automáticamente y se calculan desde la ubicación del proyecto, incluso si lo ejecutas desde otro directorio. No hay rutas del equipo del autor en el código.

### Problemas de Tkinter en Mac

- `ModuleNotFoundError: _tkinter`: ese intérprete no tiene soporte Tcl/Tk. Instala la distribución oficial y comprueba de nuevo `python3 -m tkinter`. Instalar un paquete llamado `tkinter` con `pip` no resuelve la falta de soporte nativo.
- Si `sys.executable` apunta a las herramientas de Apple y muestra Tk 8.5, usa el Python de python.org. Cierra y abre la terminal; revisa `which -a python3` para comprobar cuál ejecutas. No reemplaces `/usr/bin/python3`.
- PyWrap detecta Tk 8.5 en macOS antes de crear una ventana, porque puede abortar el proceso nativo. Si falta Tk o falla su inicialización, presenta un diagnóstico en la terminal. La consola sigue disponible.
- Si utilizas Homebrew, instala la fórmula `python-tk@X.Y` correspondiente a tu versión de Python y ejecuta ese mismo intérprete; consulta las [fórmulas oficiales](https://formulae.brew.sh/) para la versión disponible.

En Windows, usa `py main.py` o `python main.py` con una instalación que incluya Tcl/Tk. Se usan `pathlib`, `threading` y bibliotecas estándar multiplataforma. Windows no se ha probado en este entorno.

## Fase 2: tres pestañas

### Comprimir / Descomprimir

Conserva el selector, las operaciones, la confirmación antes de reemplazar, el indicador de actividad y la consola. Cinco tarjetas muestran tamaño original, tamaño `.pkz`, variación total, símbolos y nodos. El crecimiento se muestra en ámbar y con un mensaje explícito: que el proceso termine correctamente no significa que haya ahorrado espacio.

### Análisis de Huffman

Pulsa **Analizar archivo original…** para realizar un análisis de solo lectura o **Ejemplo: anita patina** para preparar la demostración sin crear archivos. El análisis de archivos se ejecuta en un hilo; el hilo principal recibe los datos mediante una cola y actualiza los widgets. Durante ese trabajo los botones de nuevas operaciones quedan bloqueados, pero se puede navegar por las pestañas.

El análisis tiene tres vistas:

- **Frecuencias y códigos:** símbolo legible, byte decimal, frecuencia, código, longitud y `frecuencia × longitud` bits. La suma de esta última columna es el total de bits Huffman. La tabla se ordena por valor de byte y tiene desplazamiento vertical/horizontal, incluso para códigos largos.
- **Árbol binario:** nodos internos azules y hojas verdes; `f` es la frecuencia y `Σ` identifica la suma de las frecuencias de los hijos. Las ramas están marcadas 0 (izquierda) y 1 (derecha). Haz doble clic en una fila, o selecciónala y pulsa Enter, para resaltar su camino y centrar la hoja. También puedes pulsar una hoja. Las barras y el arrastre sobre el fondo permiten recorrer árboles grandes sin reducir el texto hasta volverlo ilegible. Para un símbolo único, la raíz es una hoja y se usa el código convencional `0`, sin aristas.
- **Bits y bytes:** datos originales como representación de bytes, correspondencia símbolo/código, secuencia concatenada, relleno, grupos de ocho bits y valores decimales ZIP. Muestra también TREE en hexadecimal y cómo se recorre para recuperar los datos.

Los espacios, TAB, LF, CR, NUL y DEL tienen nombres explícitos. Los demás bytes no ASCII imprimibles aparecen como `\xXX`. No se interpreta un byte UTF-8 aislado como un carácter Unicode completo; una letra con tilde puede ocupar varios símbolos.

La tabla y el árbol incluyen **todos los símbolos del archivo completo** (máximo 256 hojas y 511 nodos), pero la vista binaria conserva solo los **primeros 64 bytes**. Si hay más datos, se indica **MUESTRA** y se muestran los bytes completos de ese prefijo y sus bits pendientes. No se añade relleno ficticio al prefijo ni se presentan sus valores como el ZIP completo. Las frecuencias y estadísticas siempre corresponden a toda la lectura.

El análisis reutiliza `_build_tree`, `_codes` y `_serialize` de `huffman.py`, exactamente las funciones que usa `files.compress`; no hay otra implementación del algoritmo. Se conserva el criterio de desempate. El archivo analizado debe mantenerse sin cambios para comparar la proyección con una compresión posterior.

**Alcance:** se analiza el contenido de un archivo original. No se inspecciona el árbol almacenado dentro de un `.pkz`; si seleccionas uno como original, se analizan sus bytes como los de cualquier archivo. Para explicar un archivo recuperado, selecciónalo desde `data/unwrp/`.

### Estadísticas

Muestra el último resultado de una operación o la última proyección de análisis, con una etiqueta que distingue ambas procedencias. Un análisis no crea un `.pkz`. Incluye original, ZIP, TREE, encabezado **NF + TREE + BS**, bits codificados, BS, símbolos, hojas y nodos internos y totales. No sumes TREE otra vez al encabezado: ya está incluido.

La gráfica compara original, ZIP y archivo completo `.pkz` en bytes y se adapta al tamaño de la ventana. Para `anita patina`, los datos bajan de 12 a 4 bytes, pero el encabezado de 24 bytes eleva el archivo a 28. La reducción total es negativa: se muestra **crecimiento del 133,33 %**.

### Guion de demostración

1. Abre **Análisis de Huffman → Ejemplo: anita patina**. La tabla cuenta 12 bytes y 6 símbolos, incluido el espacio.
2. Explica el heap mínimo: se extraen los dos nodos de menor frecuencia, se unen y se reinserta la suma. En empates se usa el byte mínimo del subárbol. Los detalles de cada unión están en el ejemplo académico de este README.
3. En el árbol, sigue una ruta desde la raíz: por ejemplo, `p` corresponde a `1001`. Las hojas contienen los símbolos y los internos suman frecuencias.
4. En la tabla, suma frecuencia por longitud: son 30 bits. En **Bits y bytes** comprueba los dos ceros de relleno, los cuatro bytes `[202, 241, 59, 76]` y BS=6.
5. Explica TREE en preorden: 11 nodos de 2 bytes = 22 bytes. En **Estadísticas** muestra `1 + 22 + 1 + 4 = 28` y el crecimiento debido al encabezado.
6. En la primera pestaña comprime `data/source/anita.txt`, luego descomprime el resultado. El decodificador sigue cada bit hasta una hoja y vuelve a la raíz después de emitir su byte.
7. Compara el original y la recuperación con `cmp` y SHA-256, según los comandos de más abajo.

Capturas reales de esta fase (Python 3.15.2 / Tk 9.0.5 en macOS): [tabla](docs/screenshots/frecuencias.png), [árbol](docs/screenshots/arbol.png), [bits](docs/screenshots/bits.png), [estadísticas](docs/screenshots/estadisticas.png).

## Uso desde consola

```bash
python3 cli.py compress data/source/anita.txt
python3 cli.py decompress data/wrp/anita.txt.pkz
python3 cli.py compress data/source/anita.txt --output-dir salida
```

La aplicación **no sobrescribe por defecto**. La interfaz solicita confirmación. En consola debes autorizar explícitamente el reemplazo:

```bash
python3 cli.py compress data/source/anita.txt --overwrite
python3 cli.py decompress data/wrp/anita.txt.pkz --overwrite
```

La API también protege por defecto: `compress(origen, carpeta, overwrite=False)` y `decompress(origen, carpeta, overwrite=False)`. `overwrite=True` autoriza reemplazar el destino. Los errores de consola terminan con código 1 y un mensaje legible.

Las operaciones escriben un temporal en la misma carpeta de salida y validan el resultado antes de publicarlo. Un error de formato o de decodificación no reemplaza un archivo anterior. Los temporales se eliminan al manejar errores; un cierre forzado o una desconexión del volumen puede impedir su limpieza.

### Publicación en USB: exFAT y FAT32

- En sistemas con enlaces duros, `os.link` publica el temporal completo de forma atómica y sin reemplazar destinos existentes.
- Cuando el sistema indica **falta de soporte**, se copia por bloques usando creación exclusiva **`xb` (`O_CREAT | O_EXCL`)**. Si otro proceso crea un archivo o un enlace simbólico con ese nombre, la creación falla sin reemplazarlo. No se utiliza la combinación insegura «comprobar que no existe y luego reemplazar».
- La alternativa solo se activa para `ENOTSUP`, `EOPNOTSUPP` o `ENOSYS`, o los errores Windows `ERROR_INVALID_FUNCTION`/`ERROR_NOT_SUPPORTED` (1/50). Permisos, disco lleno, errores de entrada/salida, rutas entre volúmenes y destinos existentes no se confunden con falta de soporte.
- Si autorizas sobrescritura, se mantiene `os.replace`, sin necesitar enlaces duros.

**Límite de atomicidad de la copia:** la reserva exclusiva del nombre es atómica, pero la copia completa **no** lo es. Otros procesos pueden ver un archivo parcial mientras se escribe. Se necesita espacio para el temporal completo y para la copia al destino. Si la copia falla (por ejemplo, disco lleno), PyWrap informa del error en español y limpia su temporal, pero conserva el destino posiblemente incompleto. No lo presenta como un resultado correcto. Revísalo antes de eliminarlo o autorizar su reemplazo. Se evita borrarlo automáticamente porque otro proceso podría haber sustituido esa ruta; comprobar su identidad y borrarla después tampoco elimina esa carrera.

La finalización normal no garantiza persistencia frente a pérdida de energía: no se implementa un protocolo de `fsync` de archivos y directorios. El formato continúa sin checksum; un parcial no debe considerarse válido porque llegue a abrirse.

Se verificaron exFAT y FAT32 reales mediante imágenes de disco montadas en macOS, sin simular `os.link`; ambos reprodujeron el error 45. No se probó hardware USB físico. Para probar tu volumen sin tocar archivos existentes:

```bash
python3 benchmarks/check_filesystem.py --directory "/Volumes/MI_USB"
```

El script crea y elimina únicamente un directorio temporal propio dentro del volumen. Verifica recuperación exacta, SHA-256, rechazo de sobrescritura y limpieza. No formatea ni monta dispositivos. El registro real está en [docs/filesystem-validation.json](docs/filesystem-validation.json).

## Fase 3.1: rendimiento y regresiones

Se conserva el árbol, su desempate, la serialización y `NF | TREE | BS | ZIP`. La descompresión de ZIP de al menos **128 KiB** con más de un símbolo usa una tabla precalculada a partir del árbol leído. Cada entrada consume ocho bits, emite los símbolos completados y conserva el nodo donde continúa el siguiente byte. Soporta códigos de más de ocho bits y cruces entre bloques. El último byte se procesa según BS, verificando relleno y terminación en la raíz. Los originales vacíos, los árboles de una hoja y los ZIP pequeños mantienen su tratamiento anterior.

La tabla tiene como máximo **255 estados × 256 entradas = 65.280 transiciones**. Añade memoria y costo de preparación acotados; por eso no se prepara para ZIP pequeños. No se modifican las funcionalidades educativas.

Medianas de tres ejecuciones en Python 3.15.2, macOS 26.3.1 ARM64:

| Original | Antes | Después | Factor |
| --- | ---: | ---: | ---: |
| Binario uniforme, 64 MiB | 58,589 s | 3,564 s | 16,44× |
| Texto UTF-8, 8 MiB | 4,138 s | 0,274 s | 15,09× |
| Un símbolo, 8 MiB | 0,766 s | 0,758 s | Sin optimización; variación de medición |

Se mide la llamada completa de descompresión, incluida la preparación de la tabla, lectura, escritura y publicación; no se cronometra la creación del original, la compresión ni SHA-256. No se vacía la caché del sistema ni se fuerza escritura física. Son mediciones de esta máquina, no una garantía de velocidad para otros equipos o memorias USB. En todas las repeticiones se comprobó SHA-256 del recuperado; los originales y los `.pkz` tienen hashes idénticos entre antes y después.

Datos y metodología: [benchmarks/README.md](benchmarks/README.md). El bucle anterior se conserva exclusivamente para QA en `benchmarks/reference_decoder.py`; la aplicación no lo importa. Para reproducir:

```bash
python3 benchmarks/benchmark_decode.py --size-mib 64 --repeats 3 --cases uniform --reference --json benchmarks/local-before.json
python3 benchmarks/benchmark_decode.py --size-mib 64 --repeats 3 --cases uniform --json benchmarks/local-after.json
```

Las pruebas permanentes incluyen un oráculo exhaustivo de optimalidad para alfabetos pequeños, propiedad libre de prefijos, 720 órdenes de inserción con empates, 60 archivos binarios aleatorios reproducibles y comparación diferencial del nuevo decodificador con el anterior. Se comprueban además corrupción, truncamientos, límites de BS, códigos largos, fallos de disco, carreras de publicación y limpieza de temporales. Se conservan todos los fixtures anteriores.

### Preparación para Git

Se inicializó un repositorio local, sin crear commits ni añadir archivos al índice. `.gitignore` excluye `.DS_Store` en cualquier nivel, metadatos Windows, temporales, cachés, entornos virtuales y salidas de demostración de `data/wrp/` y `data/unwrp/`. Los `.gitkeep`, fixtures `.pkz`, capturas y registros de benchmarks siguen disponibles para versionar. No se eliminaron archivos del usuario; las exclusiones no borran archivos del disco.


## Organización

```text
main.py                   Arranque y diagnóstico de Tkinter
cli.py                    Interfaz de consola
pywrap/__init__.py        API pública
pywrap/huffman.py         Árbol, heap, códigos y serialización; API original conservada
pywrap/files.py           Frecuencias, bloques, validación y publicación protegida
pywrap/decoding.py        Tabla de decodificación por byte para ZIP grandes
pywrap/reporting.py       Estadísticas compartidas por GUI y CLI
pywrap/gui.py             Coordinación de pestañas, operaciones, hilo y cola
pywrap/analysis.py        Modelo de análisis de solo lectura y disposición del árbol
pywrap/education.py       Tabla, Canvas del árbol, explicación binaria y gráfica
tests/test_huffman.py     Casos originales e igualdad de bytes y SHA-256
tests/test_files.py       Archivos grandes, corrupción, protección y CLI
tests/test_gui.py         Integración real de operaciones y visualización con Tk
tests/test_analysis.py    Frecuencias, códigos, bits, límites y compatibilidad
tests/test_publish.py     USB simulado, errores, carreras y limpieza
tests/test_properties.py  Optimalidad, prefijos, empates y corpus binario
tests/test_decoding.py    Comparación con el decodificador anterior
benchmarks/               Medición reproducible, referencia y prueba de volumen
tests/fixtures/           Archivos .pkz fijos generados antes de la fase 2
docs/screenshots/         Capturas reales de la interfaz
docs/*.md                 Informe, guía, preguntas y demostración de la sustentación
data/source/anita.txt     Ejemplo de clase, sin salto de línea final
data/wrp/                 Archivos comprimidos
data/unwrp/               Archivos recuperados
```

## Huffman y árbol binario

Cada hoja representa un byte distinto y su frecuencia. Cada nodo interno tiene exactamente dos hijos y una frecuencia igual a la suma de las de sus hijos. Una cola de prioridad mínima (`heapq`) permite extraer los dos nodos menos frecuentes y unirlos; se repite hasta tener una sola raíz. Se implementan manualmente la construcción del árbol, los recorridos, la serialización y el empaquetado de bits; no se usa una biblioteca de compresión.

La rama **izquierda representa 0** y la **derecha 1**. El camino de la raíz a una hoja es el código del símbolo. Ningún código es prefijo de otro: permite decodificar sin separadores. Los símbolos frecuentes suelen tener caminos más cortos.

Para `k` símbolos en un archivo no vacío hay `k` hojas, `k−1` nodos internos y `2k−1` nodos totales. La prioridad usa frecuencia, byte mínimo del subárbol y un contador de desempate. El primer nodo extraído queda a la izquierda. Esto hace reproducible la salida.

### Ejemplo de clase: `anita patina`

Contiene **12 bytes**, incluido el espacio, sin salto de línea. Estos son los códigos que genera esta implementación:

| Símbolo | Byte decimal | Frecuencia | Código | Aporte en bits |
| --- | ---: | ---: | --- | ---: |
| espacio | 32 | 1 | `1000` | 4 |
| a | 97 | 4 | `11` | 8 |
| i | 105 | 2 | `101` | 6 |
| n | 110 | 2 | `00` | 4 |
| p | 112 | 1 | `1001` | 4 |
| t | 116 | 2 | `01` | 4 |
| **Total** | | **12** | | **30** |

Las combinaciones del heap son: espacio + p = 2; ese subárbol + i = 4; n + t = 4; el subárbol de espacio/p/i + a = 8; finalmente el de n/t + ese conjunto = 12. Los empates se resuelven por el byte mínimo del subárbol.

El árbol resultante, con las frecuencias entre paréntesis:

```text
raíz (12)
├── 0: interno (4)
│   ├── 0: n (2)
│   └── 1: t (2)
└── 1: interno (8)
    ├── 0: interno (4)
    │   ├── 0: interno (2)
    │   │   ├── 0: espacio (1)
    │   │   └── 1: p (1)
    │   └── 1: i (2)
    └── 1: a (4)
```

Concatenación de códigos: `110010101111000100111011010011` (30 bits). Se agregan dos ceros de relleno: ZIP contiene los bytes decimales `[202, 241, 59, 76]`. Hay 6 símbolos, **NF=5**, 11 nodos totales, **TREE=22 bytes**, **BS=6** y **ZIP=4 bytes**. El archivo completo ocupa **1 + 22 + 1 + 4 = 28 bytes**. Crece 133,33 % respecto de los 12 originales por la cabecera.

### Compresión paso a paso

1. Lee bloques de hasta 1 MiB y cuenta cada uno de los 256 valores posibles. También calcula SHA-256 de esta primera lectura.
2. Construye el heap y combina mínimos para obtener el árbol.
3. Recorre el árbol y obtiene código y longitud de cada byte.
4. Escribe NF, TREE y un espacio reservado para BS.
5. Lee otra vez el original y concatena sus códigos en un acumulador. Extrae bytes completos desde los bits más significativos; escribe bloques de salida sin conservar todo el archivo en memoria.
6. Completa con ceros el último byte cuando haga falta y actualiza BS. Compara el SHA-256 de ambas lecturas para detectar cambios del original durante el procesamiento.
7. Publica el temporal como `.pkz` si la operación terminó correctamente.

### Descompresión paso a paso

1. Lee NF y calcula el tamaño exacto de TREE. Reconoce por separado el archivo vacío.
2. Reconstruye el árbol en preorden, comprobando etiquetas, hojas únicas y cantidad de nodos.
3. Lee BS y verifica que haya ZIP y que los bits de relleno sean cero.
4. Procesa ZIP del bit más significativo al menos significativo. Cada bit selecciona izquierda o derecha. Al llegar a una hoja, escribe su byte y vuelve a la raíz.
5. En el último byte procesa solamente BS bits. Si termina dentro de un código, rechaza el archivo.
6. Publica el archivo recuperado después de validar toda la estructura.

## Formato académico `.pkz`

Se mantiene **`NF | TREE | BS | ZIP`**, sin campos adicionales. Es la convención del repositorio inicial; **no se ha comprobado compatibilidad con WinWrap Java**, y no se suministraron fotografías ni archivos Java de referencia para verificarla. Preorden, etiquetas, desempates, orientación de bits y casos especiales son decisiones de implementación. Distintos desempates pueden dar otros códigos óptimos con el mismo número de bits.

| Campo | Tamaño | Codificación |
| --- | --- | --- |
| NF | 1 byte sin signo | Cantidad de nodos internos, de 0 a 255. |
| TREE | `2 × (2 × NF + 1)` bytes para un original no vacío | Preorden: nodo, subárbol izquierdo, subárbol derecho. Cada nodo tiene 2 bytes: `00 00` si es interno; `01 xx` si es hoja, donde `xx` es el valor de byte, incluso `00` o `FF`. |
| BS | 1 byte sin signo | Bits válidos del último byte ZIP, entre 1 y 8. `8` indica que todos sus bits son útiles. |
| ZIP | Hasta fin de archivo | Códigos empaquetados MSB-first, con relleno cero en los bits bajos del último byte. |

Casos especiales:

- **Vacío:** exactamente `00 00`: NF=0 y BS=0, sin TREE ni ZIP.
- **Un símbolo:** NF=0, TREE=`01 xx`, código `0` por cada repetición. Cada bit válido produce un byte original. Se conserva así la cantidad de repeticiones.
- **256 símbolos:** NF=255, TREE=1022 bytes y 511 nodos totales.

El tamaño no vacío es `1 + 2 × (2 × NF + 1) + 1 + ceil(bits / 8)`. ZIP no tiene longitud guardada: se lee hasta el final del archivo.

**Nombre original:** se conserva en el nombre externo: `foto.jpg` → `foto.jpg.pkz` → `foto.jpg`. No se almacena dentro de NF/TREE/BS/ZIP. Si renombras el `.pkz`, cambiará el nombre recuperado. Incluirlo en la cabecera requeriría modificar el formato y el tamaño de 28 bytes. No se conservan permisos, fechas, directorios ni otros metadatos; sí todos los bytes del contenido.

## Estadísticas

```text
reducción (%) = (1 − tamaño_comprimido / tamaño_original) × 100
```

Se usa el tamaño completo del `.pkz`, incluida su cabecera. Si el resultado es negativo, se informa **crecimiento** con su magnitud positiva. Se aplica la misma base al descomprimir. Para un original vacío el porcentaje no está definido y se muestra «no aplica»; la API retorna 0 como valor convencional. La consola informa tamaño original y comprimido, símbolos, nodos totales, NF, TREE, BS y ZIP.

## Pruebas y demostración de integridad

Desde la carpeta del proyecto:

```bash
python3 -m unittest discover -s tests -v
```

Cubren el ejemplo exacto, vacío, un símbolo repetido y límites de byte, los 256 valores, UTF-8, binario determinista, un archivo de más de 3 MiB, ciclos consecutivos, archivos corruptos o incompletos, protección de destinos, cambios entre lecturas y CLI desde otro directorio. Los ciclos verifican **igualdad byte a byte y SHA-256**. Se verifican también tabla/códigos frente al árbol, límites de muestra, estadísticas y cuatro `.pkz` fijos de la fase 1: vacío, un símbolo, ejemplo y 256 símbolos. La recompresión debe ser idéntica a esas referencias. Las pruebas GUI se omiten si falta Tk o hay Tk 8.5 en macOS; otros fallos al crear la ventana se reportan como errores.

Demostración en terminal (usa `--overwrite` únicamente si quieres reemplazar salidas existentes):

```bash
python3 cli.py compress data/source/anita.txt
python3 cli.py decompress data/wrp/anita.txt.pkz
shasum -a 256 data/source/anita.txt data/unwrp/anita.txt
cmp data/source/anita.txt data/unwrp/anita.txt
```

Los SHA-256 deben coincidir y `cmp` debe terminar sin diferencias. En Windows puedes comparar con `Get-FileHash RUTA -Algorithm SHA256` en PowerShell.

## Límites y alcance

- JPG, MP4, PDF y ZIP pueden crecer, pues muchos ya usan compresión. El árbol también puede superar el ahorro de archivos pequeños.
- La memoria de trabajo está limitada por los bloques, el árbol (máximo 256 hojas) y el búfer de salida; el contenido completo no se carga en RAM. Procesar bits en Python puede ser lento para videos grandes. Construir el árbol cuesta `O(k log k)`; codificar/decodificar depende del número de bits procesados, con `k ≤ 256`.
- Se detectan árboles inválidos, cabeceras incompletas, BS fuera de rango, códigos incompletos y relleno incorrecto. **No se puede detectar toda corrupción**: sin checksum ni longitud original almacenados, cambiar un bit o truncar ZIP en un límite válido puede producir otro contenido aceptado. Una prueba documenta este límite. Compara SHA-256 contra un original conocido; la comprobación entre lecturas al comprimir no es un checksum almacenado.
- El formato carece de firma identificadora. Un archivo arbitrario que cumpla la estructura podría aceptarse. Añadir firma, versión, longitud y checksum requeriría una futura versión del formato.
- Sin enlaces duros se usa copia con creación exclusiva. La copia es visible mientras se completa y un error puede dejar un destino parcial, como se detalla en la sección USB. No se reemplazan archivos existentes sin autorización.
- No hay cancelación durante una operación; la interfaz solicita esperar antes de cerrar. No se han validado Windows ni interoperabilidad Java en este equipo.
- En la fase 2 se verificó el arranque y la interfaz en macOS con Python 3.15.2 y Tk 9.0.5. Sigue disponible el diagnóstico para el Python antiguo de Apple con Tk 8.5. Véase el [registro de verificación](VALIDACION.md).
