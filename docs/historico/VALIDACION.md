# Registro de verificación

## Simplificación adicional · 17 de noviembre de 2026

Esta es la revisión actual; las secciones siguientes conservan el historial.

- La interfaz pasa de selector de operación, botón de ejecución y cuatro tarjetas
  a una selección de archivo, dos botones y un resultado. Se conservan las
  estadísticas en el resultado y en la consola.
- Un hilo procesa el archivo y una cola entrega el resultado al hilo de Tk.
  La ventana sigue respondiendo. No se permiten operaciones simultáneas ni el
  cierre normal durante una operación. No se añadió cancelación.
- `_operation` reúne apertura, destino, temporal y limpieza. La compresión
  calcula BS con las frecuencias y escribe el encabezado una sola vez.
- Se conservan el formato, los desempates, la API de consola y la protección
  contra reemplazos no autorizados. Los cuatro fixtures siguen produciendo
  exactamente los mismos bytes.
- **24 pruebas aprobadas, 0 omitidas**, en Windows con Python 3.13.17 y Tk 8.6.
- La nueva prueba con **8 MiB** usa los 256 bytes, vigila que ninguna lectura
  exceda 64 KiB ni se solicite leer todo el archivo, y acota las escrituras.
  Elimina el original antes de recuperar y comprueba SHA-256. No quedan temporales.
- Otra prueba recorre más de tres bloques con códigos de más de 8 bits y
  comprueba la recuperación exacta al cruzar límites de bloques y bytes.
- Las pruebas de GUI verifican compresión, descompresión, rechazo y aceptación
  de reemplazo, errores y procesamiento de eventos mientras el trabajador espera.

No hay filtros por tipo de archivo ni un tope de tamaño en el código. El límite
práctico depende del espacio, el sistema de archivos y el tiempo. La prueba de
8 MiB no constituye una verificación con archivos de varios GiB. Algunos archivos
pueden crecer con Huffman. Se mantiene la limitación de no detectar cambios del
original entre lecturas y la ausencia de checksum en el formato.

## Versión simplificada · Windows · 17 de noviembre de 2026

Esta sección corresponde al código actual. Las fases que siguen son registros
históricos de otra versión: sus 59 pruebas, pestañas educativas, benchmarks y
módulos ausentes no describen esta copia.

Entorno preparado: Python **3.13.17**, Tcl/Tk **8.6**, entorno virtual `.venv`,
sin dependencias de pip. Python se instaló para el usuario mediante el paquete
oficial `Python.Python.3.13` de winget.

Comprobaciones realizadas:

- Suite: **20 pruebas aprobadas, 0 omitidas** con
  `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Compilación de `main.py`, `cli.py`, `pywrap/` y `tests/` sin errores.
- La prueba GUI abre Tk real, comprime, recupera y verifica la cancelación de
  reemplazo. Sus salidas se aíslan en un directorio temporal.
- Los cuatro fixtures históricos se recuperan correctamente y se recomprimen
  con bytes idénticos.
- Consola: `anita patina`, **12 B → 28 B → 12 B**, NF=5, TREE=22 B, BS=6,
  ZIP=4 B. SHA-256 original y recuperado:
  `6e07e9bbd00943f73c3379b39e61c07eafdf2f01cd4b5eb6ce60e0c33614d440`.
- Repetir la compresión sin `--overwrite` devuelve código 1 y conserva el destino.
- Se reprodujo y corrigió la pérdida de la salida anterior cuando fallaba su
  reemplazo: ahora se usa `os.replace` sin borrado previo. Se prueba en ambas
  operaciones, incluida la limpieza de temporales.
- Se prueba que un destino creado por otro proceso durante la operación no se
  sobrescribe sin autorización.
- Se rechazan bits de relleno distintos de cero y códigos distintos de 0 para
  árboles de un solo símbolo, conservando cualquier salida anterior.
- Se añadió `Iniciar_PyWrap.cmd` y se actualizaron README, instalación y demo
  para la ventana simplificada que realmente contiene el repositorio.
- El acceso `.cmd` se inició desde una carpeta distinta al proyecto y creó una
  ventana titulada `PyWrap | Compresor Huffman`, con el proceso respondiendo.
- `fc.exe /b data\source\anita.txt data\unwrp\anita.txt` confirmó que no hay
  diferencias. Las salidas de esta demostración quedaron disponibles en `data/`.

La herramienta de inspección visual de Windows falló al conectar con su canal
nativo (`The system cannot find the file specified`, error 2), incluso tras
reiniciarla. La prueba de Tk y el arranque del proceso sí funcionaron; esta
revisión no afirma haber comprobado visualmente la distribución de la ventana.

Límites: la interfaz ejecuta operaciones de forma síncrona; el formato no tiene
checksum; no se detectan cambios del original entre las dos lecturas. No se
verificaron en esta revisión macOS/Linux, WinWrap/Java ni USB físico.

## Fase 4 · Entrega y sustentación

Fecha: 14 de noviembre de 2026. No se modificaron el algoritmo, el formato, la interfaz ni las pruebas.

### Archivos creados o modificados

- **Nuevos:** `docs/INFORME_ACADEMICO.md`, `docs/GUIA_SUSTENTACION.md`, `docs/PREGUNTAS_SUSTENTACION.md` y `docs/DEMO.md`.
- `README.md`: enlaces a esos cuatro documentos.
- `.gitignore`: excluye `data/source/demo_*`, el archivo grande que se genera para la demostración.

### Comprobaciones realizadas

- `python3 -m unittest discover -s tests`:
  - Python 3.15.2 / Tk 9.0.5: **59 aprobadas, 0 omitidas**.
  - Python 3.9.6 de Apple: **59 ejecutadas, 5 omitidas** (GUI, por Tk 8.5), 0 fallos.
- `python3 -m compileall -q main.py cli.py pywrap tests benchmarks`: sin errores.
- Los comandos de `docs/DEMO.md` se extrajeron del propio documento y se ejecutaron en zsh sobre una copia del proyecto. Resultados:
  - `anita patina` → 28 bytes, con los bytes exactos `05 … 06 ca f1 3b 4c`.
  - SHA-256 `6e07e9bb…14d440` en el original y el recuperado; `cmp` sin diferencias.
  - `demo_grande.txt` generado con semilla: 7.723.775 B → 4.152.648 B (−46,24 %), SHA-256 `437d3a5d…e909ca` en ambos. Tiempos: 1,13 s / 0,28 s con Python 3.15 y 2,33 s / 0,53 s con Python 3.9.
- Ida y vuelta con archivos reales del sistema y generados con semilla (TXT, PDF, JPG, PNG, MP4, ejecutable, los 256 valores, aleatorio y 64 MiB), borrando el original antes de descomprimir: todos idénticos byte a byte y por SHA-256. Las cifras están en `docs/INFORME_ACADEMICO.md` §13.2.
- Paquete de entrega: `git archive` sobre una copia con commit genera 55 entradas, sin `.DS_Store`, `__pycache__`, temporales, salidas de `data/wrp` y `data/unwrp` ni `demo_grande.txt`.
- No hay rutas privadas ni datos personales en los `.md`, `.py` ni `.json` del proyecto.
- Durante las pruebas de GUI, Tk puede imprimir `invalid command name "…_check_events"` al destruir ventanas. No afecta al resultado y está explicado en `docs/DEMO.md`.

### Pendientes y asuntos para confirmar con el docente

- **Por confirmar con el docente:**
  - si se acepta usar `heapq` y `Counter` de la biblioteca estándar o se exige programar a mano la cola de prioridad;
  - la convención de NF y TREE del enunciado.
- **Pendientes de comprobar:** compatibilidad con WinWrap/Java, Windows real y una memoria USB física.
- Completar los integrantes, el docente y la fecha en la portada de `docs/INFORME_ACADEMICO.md`.

## Fase 3.1 · Correcciones de auditoría

Entorno: Python **3.15.2**, macOS **26.3.1 ARM64**, Tk **9.0.5**. Se revisaron publicación, lectura de ZIP, pruebas, fixtures, documentación y exclusiones. No se modificaron el constructor Huffman, los desempates, los códigos, la serialización, el formato, el modelo educativo ni la estructura de la GUI.

### Compatibilidad de publicación

`files._publish` mantiene `os.link` cuando está soportado. Ante `ENOTSUP`/`EOPNOTSUPP`/`ENOSYS`, o errores Windows 1/50, usa copia por bloques con creación exclusiva `xb`. Las pruebas comprueban que otros errores no activan esta alternativa. No se hace `exists` seguido de un reemplazo que pudiera pisar un archivo recién creado por otro proceso. `overwrite=True` conserva la publicación con `os.replace`.

La reserva del nombre es atómica; **la copia no lo es**. Puede verse un destino parcial durante la escritura. Si falla, se limpia el temporal de entrada y se devuelve un error explícito en español, conservando el destino posiblemente incompleto para evitar borrar por nombre un archivo sustituido por otro proceso. Esta elección está documentada y probada, incluido un reemplazo concurrente durante un error. No se garantiza durabilidad ante pérdida de energía, ni limpieza si el sistema impide acceder al volumen desconectado.

Se crearon imágenes desechables de 64 MiB, se montaron con el controlador real de macOS y se confirmó su formato con `diskutil info`:

| Sistema de archivos | `os.link` real | Recuperación exacta + SHA-256 | Sin sobrescritura | Sin temporales |
| --- | --- | --- | --- | --- |
| ExFAT | Error 45, Operation not supported | Correcta | Correcto | Correcto |
| MS-DOS FAT32 | Error 45, Operation not supported | Correcta | Correcto | Correcto |

El archivo de prueba tenía 262.412 bytes y el `.pkz` 263.436 bytes; su ZIP supera el umbral de tabla, por lo que la prueba combina el decodificador optimizado y la publicación alternativa. SHA-256 original/recuperado: `f749c739b50be009c85d380d7bdfacc76a3fb7c417b7690a8d52d85143c7907f`. Se desmontaron ambas imágenes después de usarlas. No se probó una memoria USB física. Registro: [filesystem-validation.json](docs/filesystem-validation.json); script reproducible: `benchmarks/check_filesystem.py`.

### Rendimiento medido antes y después

Se midió primero el código original, conservando una copia exacta de `files.py` para el benchmark de 64 MiB. Las tres descompresiones tardaron **58,840553 / 58,420911 / 58,588669 s**, con SHA-256 correcto. Solo después se implementó la tabla.

El nuevo `decoding.py` transforma el árbol ya validado en un autómata con hasta 255 estados internos y 256 transiciones por estado. Una transición emite los bytes completados y conserva el estado de continuación. No vuelve a construir el árbol ni cambia sus códigos. El último byte mantiene procesamiento por bits, BS, relleno y terminación en la raíz. Se preserva el bucle anterior para ZIP de menos de 128 KiB y árboles de una hoja; el caso vacío no entra en el decodificador de ZIP.

Resultados finales, medianas de tres repeticiones:

| Caso | Antes | Después | Factor |
| --- | ---: | ---: | ---: |
| Uniforme, 64 MiB | 58,588669 s | 3,564232 s | 16,44× |
| Texto UTF-8, 8 MiB | 4,137729 s | 0,274239 s | 15,09× |
| Un símbolo, 8 MiB | 0,766070 s | 0,758058 s | Sin cambio de ruta; variación de medición |

Las tres mediciones finales de 64 MiB fueron **3,564232 / 3,560983 / 3,614649 s**. Se comprobó que los hashes de los originales y archivos `.pkz` coinciden entre versiones; cada recuperado se valida por SHA-256 fuera del cronómetro. Las mediciones incluyen preparación de tabla y operaciones completas de disco, sin vaciar caché ni forzar `fsync`. No se presentan como mediciones de hardware USB. Metodología, comandos y JSON completos: [benchmarks/README.md](benchmarks/README.md).

Se contrastaron los hashes registrados del módulo de E/S y del módulo de tabla con el código final: coinciden. Una medición adicional con `tracemalloc` observó 4.755.218 bytes de pico al construir las 65.280 transiciones del árbol uniforme de 256 símbolos; es un caso medido, no una cota universal de memoria. No se usó `tracemalloc` dentro de los tiempos comparados.

### Suite final y regresión

Comandos ejecutados:

```bash
python3 -m compileall -q main.py cli.py pywrap tests benchmarks
python3 -m unittest discover -s tests -v
```

Resultado final: **59 pruebas aprobadas, 0 fallos, 0 omitidas**, en **5,227 segundos**. Se conservan las 37 pruebas anteriores y todos los fixtures. Se añadieron 22 pruebas: 11 de publicación, 7 de decodificación y 4 de propiedades/corpus.

Cobertura relevante:

- Optimalidad contra un oráculo exhaustivo que prueba todas las parejas de unión para alfabetos de 2 a 6 símbolos con pesos 1–3, sin usar el heap del producto.
- Códigos libres de prefijos y suma de Kraft en alfabetos múltiples; el símbolo único conserva el código convencional 0.
- 720 órdenes de inserción para frecuencias con empates: mismos códigos y misma serialización.
- 60 archivos binarios reproducibles con 12 semillas y alfabetos de 1, 2, 3, 17 y 256 valores, igualdad byte a byte y SHA-256.
- Comparación con el decodificador bit a bit congelado: 96 combinaciones de ZIP arbitrario y BS, cruces de códigos largos entre bytes y bloques, 44 variantes de fixtures y streams truncados.
- BS 1–8, relleno válido/inválido, encabezados/árboles corruptos, errores de escritura/publicación y limpieza de temporales.
- Falta de soporte de enlaces simulada, permisos/espacio/EIO/EXDEV/EINVAL sin alternativa indebida, colisiones y enlaces simbólicos existentes, reemplazo explícito y conservación de archivos ajenos durante fallos.
- Los cuatro fixtures anteriores mantienen SHA-256, recuperación exacta y recompresión idéntica. `anita patina` sigue produciendo **30 bits y 28 bytes**.
- Las cinco pruebas de integración con Tk real siguen pasando: operaciones, tabla/árbol, casos límite, hilo de análisis y restauración tras errores.

### Organización y límites pendientes

El directorio no tenía repositorio Git. Se inicializó con `git init -b main`, sin añadir archivos al índice ni crear commits. `git check-ignore` confirmó la exclusión de `.DS_Store` tanto en raíz como dentro de `data/`, cachés, temporales y salidas generadas. `git ls-files --others --exclude-standard` confirmó que los cuatro fixtures, sus instrucciones y los `.gitkeep` siguen disponibles para versionar. Los `.DS_Store` existentes no se borraron.

Pendientes: hardware USB físico, Windows real y compatibilidad Java no comprobados. La copia alternativa puede dejar un destino parcial en caso de error; requiere espacio adicional y no ofrece publicación de contenido atómica. Los límites de detección de corrupción del formato sin checksum se conservan y no se intentan corregir añadiendo campos en esta fase.

---

## Fase 2 · Visualización educativa

Entorno confirmado: Python **3.15.2**, Tcl **9.0.4**, Tk **9.0.5**, macOS. El bloqueo de Tk 8.5 registrado en la fase 1 ya no afecta al intérprete `python3` seleccionado en esta fase.

### Diagnóstico y decisiones

Se inspeccionaron todos los módulos, pruebas, documentación y archivos de datos de la fase anterior. `_build_tree`, `_codes` y `_serialize` ya exponían los elementos necesarios: el nuevo análisis los reutiliza directamente. No se modificaron `huffman.py`, `files.py`, `main.py`, `cli.py`, `reporting.py` ni sus convenciones de formato. No se añadieron dependencias.

Antes de editar se generaron cuatro referencias fijas con la implementación de fase 1: ejemplo, vacío, un símbolo y los 256 valores. Se conservaron sus archivos y SHA-256 en `tests/fixtures/` y `test_analysis.py`. Las pruebas no regeneran las referencias. Se verifican tanto su recuperación exacta como la recompresión idéntica.

Se añadieron `analysis.py` (modelo, muestras, estadísticas y disposición del árbol) y `education.py` (vistas Tkinter). Se reorganizó `gui.py` en tres pestañas conservando las operaciones existentes. El análisis lee bloques en un hilo y entrega los datos por una cola; todas las actualizaciones de widgets ocurren en el hilo principal. Se mantienen hasta 256 filas/hojas y 511 nodos; la explicación binaria guarda un máximo de 64 bytes del original. El árbol usa desplazamiento, texto a tamaño legible y selección de rutas.

### Pruebas ejecutadas

La suite inicial, antes de los cambios, pasó sus **23 pruebas**, incluida la integración GUI que se había omitido en la fase 1 por el entorno.

Se ejecutó nuevamente:

```bash
python3 -m unittest discover -s tests -v
```

Resultado de la verificación de fase 2: **37 pruebas aprobadas, 0 fallos y 0 omitidas**. Incluye las 23 existentes, 10 de análisis/compatibilidad y 4 nuevas de GUI.

Cobertura agregada:

- Frecuencias completas y códigos exactos del ejemplo; cada código sigue el árbol real.
- Comparación del análisis con TREE, BS, ZIP y tamaños generados por el compresor.
- Vacío, un símbolo, 256 símbolos, UTF-8 y representaciones no imprimibles.
- Disposición de 511 nodos sin coordenadas duplicadas, ramas y rutas correspondientes.
- Archivos de más de 2 MiB: frecuencias completas, muestra acotada y análisis sin escrituras.
- Relleno y muestra parcial, porcentajes, encabezado y consistencia al descomprimir.
- Compatibilidad binaria con las cuatro referencias previas y SHA-256.
- Tk real: las tres pestañas, tabla, resaltado, bits, tarjetas, gráfica y casos límite.
- Hilo de análisis pausado mediante eventos de prueba: se comprueba que el bucle principal sigue atendiendo eventos; al terminar se recuperan los controles.
- Error de análisis: mensaje y restauración de controles.
- Se mantiene la prueba de compresión/descompresión desde GUI y rechazo de sobrescritura.

### Arranque y revisión visual

Se ejecutó **`python3 main.py`** y se observó la ventana real en macOS. Se navegó mediante teclado a la pestaña de análisis, se activó el ejemplo y se revisaron tabla, árbol, explicación binaria y estadísticas. Se ajustó el espaciado del árbol para mostrar completo el ejemplo.

Se obtuvieron capturas reales, sin generar imágenes de interfaz ficticias:

- [Tabla de frecuencias](docs/screenshots/frecuencias.png)
- [Árbol completo](docs/screenshots/arbol.png)
- [Explicación binaria](docs/screenshots/bits.png)
- [Comparación de tamaños](docs/screenshots/estadisticas.png)

El ejemplo mantiene: original=12, símbolos=6, nodos=11, NF=5, TREE=22, bits=30, BS=6, ZIP=4 y total=28 bytes. La gráfica distingue ZIP=4 del encabezado=24 y del total=28; el crecimiento se identifica en ámbar.

### Límites pendientes

Windows y compatibilidad WinWrap Java siguen sin verificarse. Se analiza el original completo, no el árbol guardado en un `.pkz`; si se selecciona un `.pkz` como original se analizan literalmente sus bytes. La vista binaria se limita a 64 bytes, mientras que tabla, árbol y estadísticas representan toda la lectura. El análisis es una proyección de compresión: el archivo debe mantenerse sin cambios para compararlo después. No hay animación paso a paso de las extracciones del heap ni cancelación de trabajos; el README explica las uniones del ejemplo y el cierre solicita esperar. Se conservan los límites de integridad del formato sin checksum de la fase 1.

---

## Registro histórico · Fase 1

Fecha: 14 de noviembre de 2026 (America/Bogota).

## Inspección inicial

Se revisaron `main.py`, `cli.py`, `pywrap/__init__.py`, `pywrap/huffman.py`, `pywrap/gui.py`, `tests/test_huffman.py`, `README.md`, `.gitignore` y el contenido de `data/`, incluidos los marcadores `.gitkeep`. No se encontraron instrucciones AGENTS.md en el proyecto.

Se conservaron el algoritmo por bytes, el heap determinista, la serialización preorden, el formato NF/TREE/BS/ZIP, los casos vacío/un símbolo, el procesamiento por bloques y la interfaz en segundo plano.

Problemas iniciales observados:

- La primera ejecución de las pruebas falló con `TypeError: dataclass() got an unexpected keyword argument 'slots'`: el `python3` disponible es Python 3.9.6. Se retiró ese argumento, sin cambiar el algoritmo.
- Compresión y descompresión reemplazaban destinos sin confirmación. Ahora requieren autorización explícita y publican el temporal sin reemplazo por defecto.
- La interfaz carecía de indicador de actividad y cantidad explícita de símbolos; el porcentaje de la API usaba una base inadecuada para descompresión. Se corrigieron estos puntos.
- La lectura/escritura estaba mezclada con el árbol. Se extrajo a `files.py`, conservando las funciones públicas originales.
- Las pruebas iniciales no cubrían archivos de varios bloques, ciclos, protección de destinos, cambios de entrada, gran parte de las validaciones ni CLI. Se añadieron pruebas para esos casos.
- El README no detallaba frecuencias/códigos ni los límites reales de detección de corrupción y conservación del nombre. Se documentaron sin cambiar el formato.

## Comandos ejecutados y resultados

```bash
python3 -m unittest discover -s tests -v
```

Resultado final: **23 pruebas descubiertas; 22 aprobadas y 1 omitida**, sin fallos. Tiempo de esa ejecución: 10,563 segundos. Incluye un archivo pseudoaleatorio de 3.145.807 bytes, UTF-8, todos los valores de byte, límites de BS, corrupción estructural, ciclos, igualdad byte a byte y SHA-256.

La prueba omitida es `test_start_roundtrip_and_decline_overwrite`, que necesita un Tk compatible para crear una ventana real. No se sustituyó Tkinter por una simulación para afirmar que la GUI funciona.

```bash
python3 -m compileall -q main.py cli.py pywrap tests
python3 cli.py compress data/source/anita.txt
python3 cli.py decompress data/wrp/anita.txt.pkz
shasum -a 256 data/source/anita.txt data/unwrp/anita.txt
cmp data/source/anita.txt data/unwrp/anita.txt
```

Compilación de los módulos comprobados sin errores. Demostración CLI completada: original 12 bytes, comprimido 28 bytes, 6 símbolos, NF=5, TREE=22, BS=6, ZIP=4. `cmp` terminó con código 0 y ambos hashes fueron:

```text
6e07e9bbd00943f73c3379b39e61c07eafdf2f01cd4b5eb6ce60e0c33614d440
```

Los comandos de demostración dejaron `data/wrp/anita.txt.pkz` y `data/unwrp/anita.txt`. Una nueva ejecución pide autorización de reemplazo (CLI: `--overwrite`).

## Arranque gráfico: límite del entorno

Intérprete: Python 3.9.6 de las herramientas de desarrollo de Apple, Tk 8.5. Importar `tkinter` sí funciona. Crear una ventana Tk de prueba en un subproceso terminó con código 134 y el mensaje nativo `macOS 26 (2603) or later required, have instead 16 (1603) !`.

Tras añadir el diagnóstico, se ejecutó `python3 main.py`: termina con código 1, sin ese aborto nativo, e indica instalar un Python con Tk 8.6 o posterior y consultar el README. **No se verificaron visualmente la ventana, sus diálogos ni la animación en este entorno.** El test de integración está preparado para ejecutarlos con un Tk compatible.

## Pendientes de validación externa

- Instalar/seleccionar un Python con Tk compatible, ejecutar `python3 -m tkinter`, `python3 main.py` y repetir la suite; la prueba GUI debe dejar de omitirse.
- Probar en Windows; se usaron APIs estándar compatibles, pero no se ejecutó allí.
- Verificar compatibilidad Java solamente si se suministran archivos de referencia.

El formato no guarda checksum, tamaño original ni nombre interno. El límite de detección de corrupción y la recuperación del nombre externo están documentados en README y cubiertos por pruebas. No se afirma integridad de un archivo alterado únicamente porque el decodificador lo acepte.
