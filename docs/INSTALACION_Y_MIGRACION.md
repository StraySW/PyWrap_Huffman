# PyWrap: instalación y migración entre computadores

Manual de la fase 4.1 · Revisado el 14 de noviembre de 2026.

Esta guía permite recibir el proyecto, preparar otro computador y comprobar que funciona. Se distribuye **código fuente**, no un instalador `.exe` ni una aplicación `.app`: el computador receptor necesita Python. Se conserva el formato académico `NF | TREE | BS | ZIP`.

**Evidencia:** macOS fue verificado con Python 3.15.2 y Tk 9.0.5. Las instrucciones de Windows 10/11 son propuestas basadas en documentación oficial y en el código multiplataforma; **no se ejecutaron en Windows**. La sección 10 registra las comprobaciones de esta entrega.

## 1. Requisitos reales del proyecto

| Elemento | Requisito |
| --- | --- |
| Python | Mínimo técnico: **3.9**. Para una instalación nueva, usa una versión estable reciente, preferiblemente la misma versión principal/secundaria que el equipo de desarrollo (aquí 3.15). |
| Interfaz | Tkinter/ttk y una sesión gráfica. En macOS, PyWrap exige Tk **8.6 o posterior**; Tk 9.0.5 fue verificado. |
| Dependencias externas | **Ninguna** para aplicación, pruebas o benchmarks. |
| `requirements.txt` | No existe ni es necesario: no hay paquetes que instalar con `pip`. |
| Entorno virtual | Opcional; útil para seleccionar un intérprete por proyecto. Se crea de nuevo en cada computador. |
| Git, GitHub y VS Code | Opcionales. La ejecución desde Terminal/PowerShell no depende de ellos. |
| Archivos | Carpeta local con permiso de lectura y escritura, y espacio para entradas, temporales y salidas. |
| Internet | Para descargar Python, VS Code o una copia desde GitHub. Después, PyWrap y sus pruebas funcionan sin conexión. |

El mínimo 3.9 corresponde al código y sus APIs, entre ellas `random.Random.randbytes`, usada en pruebas. No es una recomendación de instalar una versión antigua. Se verificó también la suite con Python 3.9.6: las cinco pruebas GUI se omiten con el Tk 8.5 de Apple; la interfaz no queda validada con ese intérprete.

Los imports se limitan a módulos propios y biblioteca estándar: `tkinter`, `pathlib`, `heapq`, `collections`, `dataclasses`, `hashlib`, `threading`, `queue`, `tempfile`, `shutil`, `unittest`, entre otros. No se requieren Java, NetBeans, NumPy, Pillow, pytest, compiladores ni frameworks web.

### 1.1 Qué debe contener una copia

```text
PyWrap_Huffman/
├── main.py                         # Entrada de la interfaz
├── cli.py                          # Entrada de la consola
├── pywrap/                         # Todos sus módulos .py
├── tests/                          # Todas las pruebas
│   └── fixtures/                   # Cuatro .pkz históricos y README
├── benchmarks/                     # Incluye reference_decoder.py
├── docs/                           # Manuales, informe y capturas
├── data/
│   ├── source/anita.txt             # Ejemplo exacto, sin salto final
│   ├── wrp/.gitkeep
│   └── unwrp/.gitkeep
├── README.md
├── VALIDACION.md
└── .gitignore
```

**Conserva `benchmarks/` incluso si no medirás rendimiento:** `tests/test_decoding.py` importa `benchmarks/reference_decoder.py`. Las carpetas `tests/` y `benchmarks/` funcionan sin añadirles un `__init__.py`; no cambies la estructura para instalar.

Los archivos del usuario no forman parte obligatoria de esta copia; su conservación se explica en la sección 5.

### 1.2 Convenciones de los comandos

Ejecuta los comandos desde la carpeta que contiene `main.py`, `cli.py`, `pywrap/` y `tests/`. Los nombres de carpetas de ejemplo se pueden sustituir por la ubicación real. Mantén las comillas si una ruta contiene espacios.

En macOS se usa `python3`; en Windows, `py`. Si seleccionas otro ejecutable, utiliza **ese mismo intérprete** para comprobar Tk, crear el entorno y ejecutar aplicación/pruebas. No escribas los símbolos de prompt `$` o `PS>` delante de los comandos.

## 2. Instalación en macOS

### 2.1 Instalar y comprobar Python

1. Entra en [descargas oficiales para macOS](https://www.python.org/downloads/macos/).
2. Elige un instalador estable compatible con tu macOS y arquitectura. Instala el paquete oficial siguiendo el asistente, con sus componentes habituales.
3. Cierra y vuelve a abrir Terminal para cargar la configuración del instalador. No sustituyas ni borres el Python de Apple: ambas instalaciones pueden coexistir. [Documentación oficial de macOS](https://docs.python.org/3/using/mac.html).
4. Comprueba:

```bash
python3 --version
python3 -c "import sys; print(sys.executable)"
which -a python3
```

Debes ver Python 3.9 o posterior. Para reproducir el entorno verificado se utilizó 3.15.2; no es obligatorio que todas las revisiones de parche sean idénticas.

### 2.2 Comprobar Tkinter y evitar Tk 8.5 de Apple

Primero comprueba qué Tk importará el intérprete, **antes de intentar abrir una ventana**:

```bash
python3 -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
```

Si muestra Tk 8.6 o posterior, ejecuta:

```bash
python3 -m tkinter
```

Debe abrirse una ventana de demostración de Tk; ciérrala para continuar. Es la comprobación recomendada por la [documentación de Tkinter](https://docs.python.org/3/library/tkinter.html).

Si aparece Tk 8.5, o un ejecutable de `CommandLineTools`, no continúes con ese intérprete para la GUI: en el entorno inicial de PyWrap llegaba a abortar el proceso nativo. `main.py` detecta ese caso y muestra un diagnóstico. Selecciona la instalación de python.org, sin tocar la del sistema:

```bash
command -v python3.15
python3.15 --version
python3.15 -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
python3.15 -m tkinter
```

`3.15` es un ejemplo verificado: sustitúyelo por la versión que instalaste. Si el comando versionado no está disponible, selecciona el ejecutable descubierto en VS Code o usa su ruta real entre comillas. No copies una ruta del computador de otro integrante. La consola `cli.py` no necesita Tk.

### 2.3 Recibir y abrir el proyecto

Si recibiste un ZIP, extráelo completamente antes de trabajar. Sitúa la carpeta en una ubicación de tu usuario, por ejemplo Documentos. En Terminal:

```bash
cd "$HOME/Documents/PyWrap_Huffman"
pwd
ls main.py cli.py pywrap tests benchmarks
```

Si tu carpeta está en otro lugar, arrastra su icono desde Finder a Terminal después de escribir `cd `, o copia su ruta y colócala entre comillas. Si `main.py` no aparece, posiblemente estás en la carpeta exterior del ZIP: entra en la carpeta interior correcta. Una carpeta compartida o un USB pueden usarse, pero para comenzar resulta más sencillo una copia local con permiso de escritura.

### 2.4 Entorno virtual opcional

Si `python3` ya selecciona la instalación correcta:

```bash
python3 -m venv .venv
./.venv/bin/python --version
./.venv/bin/python -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
```

Si todavía apunta al Python de Apple, crea el entorno con el comando versionado correcto, por ejemplo `python3.15 -m venv .venv`. Usa un nombre nuevo si ya existe un entorno de otra instalación; no sobrescribas una carpeta con datos. El entorno no corrige un Python base que carece de Tkinter.

No hay dependencias que instalar. Puedes invocar directamente `./.venv/bin/python` sin activar nada. Como alternativa:

```bash
source .venv/bin/activate
python --version
python main.py
```

Cierra la ventana y ejecuta `deactivate` para salir del entorno. El resto del manual usa `python3` sin entorno; si utilizas `.venv`, reemplázalo por `./.venv/bin/python` o por `python` mientras esté activado.

### 2.5 Ejecutar interfaz y pruebas

```bash
python3 main.py
```

Se abrirá **PyWrap | Huffman**. Para revisar el proyecto desde Terminal, cierra la aplicación y ejecuta:

```bash
python3 -m unittest discover -s tests -v
python3 cli.py --help
```

La suite actual descubre 59 pruebas. `OK` con pruebas omitidas no equivale a tener toda la GUI verificada: revisa las líneas `skipped`. Un entorno gráfico compatible debe poder ejecutar las cinco pruebas GUI.

## 3. Instalación en Windows 10 y Windows 11

**Todo este apartado está pendiente de validación en un Windows real.** Se usa PowerShell, sin WSL. El procedimiento es el mismo en Windows 10 y 11; la apariencia de los menús puede variar.

### 3.1 Descargar e instalar

Abre [Python para Windows en python.org](https://www.python.org/downloads/windows/) y elige una instalación normal para la arquitectura de tu equipo. No elijas el paquete **embeddable**, destinado a integrar Python dentro de otras aplicaciones.

Hay dos formas de instalación; utiliza una, sin combinarlas innecesariamente:

- **Python Install Manager:** instala el administrador oficial y un runtime estable; por ejemplo, con `pymanager install 3.15`. `pymanager list` permite revisar sus runtimes. Si `py` pertenece al lanzador antiguo, usa `pymanager exec` para evitar esa ambigüedad. [Guía oficial actual](https://docs.python.org/3/using/windows.html).
- **Instalador completo `.exe`, cuando esté disponible para tu versión:** conserva Tcl/Tk/IDLE y el lanzador, y habilita **Add python.exe to PATH** si deseas usar `python` desde PowerShell. Reabre la terminal al terminar. Las opciones se describen en la [guía del instalador clásico](https://docs.python.org/3.13/using/windows.html#installation-steps).

### 3.2 Verificar los comandos y Tk

En una ventana nueva de PowerShell, comprueba primero:

```powershell
py --version
py -c "import sys; print(sys.executable)"
py -c "import tkinter; print('Tk', tkinter.TkVersion)"
py -m tkinter
```

La última instrucción debe abrir una ventana; ciérrala. Si `py` no existe, prueba la misma secuencia con `python`, empezando por `python --version`. Con Install Manager también puedes utilizar:

```powershell
pymanager exec --version
pymanager exec -m tkinter
```

Para ver qué comandos encuentra PowerShell:

```powershell
Get-Command py, python, pymanager -All -ErrorAction SilentlyContinue
where.exe python
```

Si ninguno resuelve un intérprete, revisa la instalación y vuelve a abrir PowerShell. Como alternativa, localiza el `python.exe` real mediante el instalador o VS Code y ejecútalo así, sustituyendo la ruta:

```powershell
$PyWrapPython = "C:\RUTA_REAL\python.exe"
& $PyWrapPython --version
& $PyWrapPython -m tkinter
```

`C:\RUTA_REAL\python.exe` es un marcador, no una ruta universal. En PowerShell, `&` ejecuta un programa cuya ruta está en una variable o entre comillas. Si eliges este método, usa `& $PyWrapPython` en lugar de `py` en los comandos siguientes. No necesitas cambiar variables globales del sistema para PyWrap.

### 3.3 Abrir la carpeta correcta

En Explorador de archivos, extrae el ZIP con **Extraer todo**. No abras `main.py` dentro del ZIP. Sitúa la carpeta bajo Documentos o en otra ubicación con escritura y abre PowerShell:

```powershell
Set-Location (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PyWrap_Huffman')
Get-Location
Get-Item .\main.py, .\cli.py, .\pywrap, .\tests, .\benchmarks
```

Si está en otra ubicación, usa `Set-Location "D:\Proyectos\PyWrap_Huffman"` cambiando la ruta real. La consulta de Documentos evita asumir que siempre está en `C:\Users\NOMBRE\Documents`; podría estar redirigido a OneDrive.

### 3.4 Entorno virtual y ejecución

No hay paquetes externos que instalar. El entorno es opcional:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m tkinter
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No hace falta ejecutar `Activate.ps1`; invocar el ejecutable del entorno evita problemas de políticas de scripts. También puedes prescindir del entorno:

```powershell
py main.py
py -m unittest discover -s tests -v
py cli.py --help
```

Si elegiste `python`, sustituye `py` por `python` en esas instrucciones. Mantén el mismo intérprete en todos los pasos.

Algunas pruebas de enlaces simbólicos pueden omitirse si Windows no permite crearlos con los permisos actuales. Registra las omisiones; no se recomienda ejecutar toda la aplicación como administrador para ocultar ese resultado.

## 4. Trabajar desde VS Code y procesar archivos

### 4.1 VS Code en ambos sistemas

VS Code es opcional. Instálalo desde su sitio oficial y utiliza **File → Open Folder / Archivo → Abrir carpeta** sobre la carpeta raíz del proyecto. Instala la extensión **Python de Microsoft** para las herramientas del editor; no es una dependencia de PyWrap.

Abre la paleta con `Cmd+Shift+P` en Mac o `Ctrl+Shift+P` en Windows. Ejecuta **Python: Select Interpreter** y elige la instalación comprobada o el entorno local:

- macOS: `.venv/bin/python`.
- Windows: `.venv\Scripts\python.exe`.

Si no aparece, selecciona la opción de introducir/buscar su ruta. Abre una terminal integrada nueva y comprueba `sys.executable` con el comando de tu plataforma. Un terminal ya abierto puede conservar otro entorno. La selección del editor y el comando escrito manualmente en la terminal deben concordar. [Documentación de entornos de VS Code](https://code.visualstudio.com/docs/python/environments).

Ejecuta `main.py` desde esa terminal para poder leer cualquier error de arranque. No hace falta configurar extensiones de pruebas, Code Runner ni `launch.json`.

### 4.2 Uso de la interfaz

1. En **Comprimir / Descomprimir**, selecciona **Comprimir**.
2. Pulsa **Examinar…**, elige `data/source/anita.txt` y pulsa **Ejecutar**.
3. Consulta `data/wrp/anita.txt.pkz`: debe medir **28 bytes**.
4. Selecciona **Descomprimir**, abre ese `.pkz` y ejecuta de nuevo.
5. El recuperado aparecerá en `data/unwrp/anita.txt`.
6. Si ya existe un destino, acepta su reemplazo únicamente si quieres sustituirlo; puedes cancelar sin perderlo. Espera a que termine la operación antes de cerrar.
7. En **Análisis de Huffman → Ejemplo: anita patina** puedes explicar sus **30 bits** sin crear otro archivo. **Estadísticas** separa ZIP, encabezado y total.

Los selectores aceptan archivos binarios, TXT, PDF, imágenes y videos. Un archivo ya comprimido puede crecer. La consola muestra la ruta completa de salida y los errores.

### 4.3 Uso de CLI y comparación exacta

En la primera ejecución, sin salidas previas, **macOS**:

```bash
python3 cli.py compress data/source/anita.txt
python3 cli.py decompress data/wrp/anita.txt.pkz
shasum -a 256 data/source/anita.txt data/unwrp/anita.txt
cmp data/source/anita.txt data/unwrp/anita.txt
```

Los dos hashes deben coincidir y `cmp` debe terminar sin salida y con código 0. Justo después puedes consultar `echo $?`.

**PowerShell, propuesto para Windows**:

```powershell
py cli.py compress .\data\source\anita.txt
py cli.py decompress .\data\wrp\anita.txt.pkz
Get-FileHash .\data\source\anita.txt -Algorithm SHA256
Get-FileHash .\data\unwrp\anita.txt -Algorithm SHA256
fc.exe /b .\data\source\anita.txt .\data\unwrp\anita.txt
$LASTEXITCODE
```

Usa **`fc.exe`**, porque `fc` por sí solo puede ser un alias de PowerShell. Espera hashes iguales y código 0 del comparador. Que un archivo se abra no demuestra igualdad de contenido.

Para repetir la demostración autorizando reemplazo, añade `--overwrite` a cada operación CLI. La versión GUI solicita confirmación; la CLI no pregunta y falla por defecto si el destino existe. Para separar datos personales de la carpeta del proyecto puedes seleccionar una carpeta de salida propia:

```bash
python3 cli.py compress "archivo con espacios.pdf" --output-dir "../Mis_comprimidos"
python3 cli.py decompress "../Mis_comprimidos/archivo con espacios.pdf.pkz" --output-dir "../Mis_recuperados"
```

En Windows usa `py` y las rutas reales. Esos nombres son ejemplos: el archivo de entrada debe existir.

### 4.4 Cómo resuelve las rutas la aplicación

La GUI y la CLI sin `--output-dir` calculan `data/wrp/` y `data/unwrp/` desde la ubicación del proyecto, no desde un usuario fijo. Esas carpetas se crean si faltan. Las entradas relativas y `--output-dir` relativo se interpretan desde la carpeta actual de la terminal. Por eso esta guía entra primero en la raíz del proyecto.

No hace falta cambiar el código al moverlo de disco, usuario o sistema operativo. El selector GUI puede leer fuera del proyecto; las salidas GUI siguen estando dentro de `data/`. Guarda la copia del proyecto en una ubicación escribible.

## 5. Migración entre computadores

### 5.1 Preparación común

Antes de transferir, cierra PyWrap cuando haya terminado de trabajar. Conserva una copia del proyecto y otra, separada, de los datos del usuario. Transfiere archivos completos, no una sesión abierta del editor.

| Copiar en la entrega académica | Conservar aparte si son del usuario | No es necesario transferir |
| --- | --- | --- |
| `main.py`, `cli.py`, todos los `.py` de `pywrap/`, `tests/`, `benchmarks/` | Originales personales de cualquier ubicación | `.venv/`, `venv/`, entornos de otro sistema |
| Todos los fixtures y su README, sin regenerarlos | `.pkz` generados en `data/wrp/` o en otras carpetas | `__pycache__/`, `.pyc`, cachés de herramientas |
| `README.md`, `VALIDACION.md`, `.gitignore` | Recuperados personales de `data/unwrp/` | `.DS_Store`, `._*`, `Thumbs.db`, temporales `.pywrap-*.tmp` |
| Documentos académicos de `docs/`, capturas y registros de benchmarks | Documentos privados, rutas, capturas o registros personales | `.vscode/` y configuraciones específicas de otro computador |
| `data/source/anita.txt` y marcadores `.gitkeep` | Entradas y archivos grandes creados para demos personales | `.git/` en un ZIP académico; no es necesario para ejecutar |

No borres esos elementos de la copia de trabajo para preparar la entrega. La sección 7 genera un ZIP desde una selección explícita sin alterar el origen. Conserva `.git/` en tu respaldo de desarrollo si quieres preservar historia y ramas; una entrega académica es otra cosa.

### 5.2 Los cuatro escenarios

| Migración | Qué hacer en el receptor |
| --- | --- |
| Mac → Mac | Instalar/seleccionar Python propio con Tk compatible; copiar fuentes y datos; crear un entorno nuevo si se usa. No asumir que el otro Mac tiene la misma arquitectura ni instalación. |
| Mac → Windows | Instalar Python para Windows; extraer el proyecto completo; recrear `.venv` con `py`; usar los comandos PowerShell y rutas Windows. No convertir archivos binarios ni finales de línea de `.pkz`. |
| Windows → Mac | Instalar Python de python.org para Mac; seleccionar Tk 8.6+; copiar fuentes y recrear `.venv` con `python3`; usar Terminal. No se ejecuta `Scripts\python.exe` de Windows en Mac. |
| Windows → Windows | Instalar/seleccionar Python en el destino y recrear el entorno aunque parezcan equipos iguales. Las rutas de usuario y las instalaciones pueden diferir. |

En todos los casos: comprueba intérprete, Tk, manifiesto o hashes de transferencia, suite, compresión del ejemplo y comparación exacta. La compatibilidad del formato no depende de copiar el intérprete del emisor.

### 5.3 Entornos y dependencias

Un entorno virtual contiene ejecutables y referencias a una instalación base; **no es una carpeta portable**. Esto también aplica entre dos equipos con el mismo sistema o después de mover el proyecto a otra ruta. Recrea el entorno con el Python del receptor y no guardes archivos de trabajo dentro de `.venv`. [Documentación oficial de `venv`](https://docs.python.org/3/library/venv.html).

En esta versión no hay una reinstalación de paquetes pendiente: vuelve a instalar Python con Tkinter y, opcionalmente, crea `.venv`. No ejecutes `pip install -r requirements.txt`, `pip freeze` ni `pip install tkinter` como pasos de instalación de PyWrap. Si una fase futura introduce dependencias, debe documentarlas y suministrar su manifiesto; no inventes uno para esta versión.

### 5.4 Compatibilidad y conservación de `.pkz`

Los `.pkz` antiguos de PyWrap incluyen el árbol y los bits necesarios para decodificar. No necesitan una base de datos de frecuencias externa, otro archivo de árbol, Java ni la instalación original de Python. Mantén las fuentes compatibles del proyecto y los cuatro fixtures históricos para comprobar regresiones.

El **nombre original se conserva en el nombre externo**: `foto.jpg` → `foto.jpg.pkz` → `foto.jpg`. No está guardado dentro de la cabecera. Mantén el nombre completo y los bytes del `.pkz`; en Windows activa la visualización de extensiones para no terminar con `.pkz.pkz` o `.pkz.txt`. Si el nombre contiene caracteres no admitidos por el sistema receptor, conserva el archivo original en un respaldo y documenta cualquier cambio: cambiará el nombre de la recuperación, aunque el contenido pueda recuperarse igual.

Los fixtures de `tests/fixtures/` no son las salidas de `data/wrp/`: transfiere ambos grupos según corresponda y no sustituyas los fixtures por nuevos archivos. Los tests fijan sus SHA-256. No se afirma compatibilidad con WinWrap Java.

Para datos personales, guarda hashes antes de moverlos y compáralos en el destino (`shasum -a 256` o `Get-FileHash`). El formato no contiene checksum: que la descompresión termine sin error no garantiza que una transferencia alterada conserve el original.

### 5.5 Transferencia por USB

Copia el proyecto o su ZIP y, en una carpeta separada, los datos personales que quieras migrar. Espera a que termine la copia y expulsa el dispositivo correctamente. Verifica hashes después de copiar y evita ejecutar mientras se está desconectando el USB.

PyWrap admite la publicación alternativa sin enlaces duros de exFAT/FAT32. Se verificó con imágenes reales montadas en macOS; **no con una memoria física ni en Windows**. La copia exclusiva evita reemplazos, pero no es una publicación completa atómica: puede verse un destino parcial y, si la copia falla, quedar incompleto. Revisa el error antes de reutilizar ese archivo. Se requiere espacio para el temporal completo y la copia de salida.

Para comprobar un volumen, puedes ejecutar:

```bash
python3 benchmarks/check_filesystem.py --directory "/Volumes/MI_USB"
```

Propuesta PowerShell equivalente:

```powershell
py benchmarks/check_filesystem.py --directory "E:\"
```

Cambia la ubicación por la real. El comprobador crea y elimina solo un directorio temporal propio; no formatea el dispositivo. No se debe aplicar como solución general `--overwrite`: eso autoriza sustituir datos y no corrige falta de espacio, permisos o un volumen desconectado.

### 5.6 Transferencia por ZIP

Usa la entrega limpia de la sección 7. Calcula SHA-256 del ZIP y envía ese valor al receptor para compararlo. En el destino, comprueba integridad, extrae a una carpeta nueva y verifica el manifiesto. No ejecutes desde la vista comprimida ni mezcles directamente la extracción con una instalación anterior que contenga archivos personales.

### 5.7 Transferencia mediante GitHub

Git y GitHub son opcionales. El repositorio actual está inicializado localmente, pero **no tiene un commit válido ni remoto configurado** en la revisión de esta guía. Por eso no se proporciona `git archive HEAD` como procedimiento de entrega.

Antes de publicar, el propietario debe revisar qué archivos piensa compartir: `.gitignore` no bloquea originales personales nuevos en `data/source/` ni documentos privados de `docs/`. Tampoco elimina del historial un archivo que ya estuviera versionado. Publicar en GitHub es una decisión separada de instalar PyWrap; este manual no ha publicado ni configurado una cuenta o repositorio remoto.

Si el equipo **ya dispone de un repositorio GitHub revisado y con commits**, el receptor puede usar **Code → Download ZIP**, o bien, con Git instalado:

```text
git clone URL_REAL_DEL_REPOSITORIO PyWrap_Huffman
cd PyWrap_Huffman
git rev-parse HEAD
git status --short
```

Sustituye `URL_REAL_DEL_REPOSITORIO`; no existe una URL de PyWrap configurada por este manual. Registra el identificador de commit y compáralo con el entregado por el emisor. Después, sigue la instalación de tu sistema. Un ZIP descargado de GitHub no incluye la historia `.git`.

Las salidas de `data/wrp/`, `data/unwrp/`, entornos y ciertos archivos de demostración están ignorados: **no llegarán mediante clone si no están versionados**. Los `.pkz` personales deben transferirse por otro canal acordado, sin forzarlos dentro de la entrega pública. Todos los fixtures académicos sí deben estar incluidos en el commit compartido.

## 6. Solución de problemas

| Síntoma | Diagnóstico y solución |
| --- | --- |
| `python: command not found` en Mac | Prueba `python3`. Si utilizas entorno, invoca `./.venv/bin/python`. Comprueba `sys.executable`. |
| `python3: command not found` | Instala Python y abre una terminal nueva. Prueba el comando versionado que instalaste; localízalo con `command -v`. No crees enlaces sobre `/usr/bin/python3`. |
| Windows no reconoce `py` o `python` | Prueba el otro comando, `pymanager exec` o la ruta del ejecutable con `&`. Reabre PowerShell tras instalar. `Get-Command` muestra las coincidencias. |
| `python` abre Store o selecciona otro runtime | Comprueba los alias de ejecución de aplicaciones y el administrador/lanzador instalado. Identifica el ejecutable antes de cambiar configuración; usa `.venv\Scripts\python.exe` para fijar el intérprete del proyecto. [Diagnóstico oficial Windows](https://docs.python.org/3/using/windows.html#troubleshooting). |
| `ModuleNotFoundError: tkinter` o `_tkinter` | Ese Python no tiene el componente nativo. Repara o instala una distribución con Tcl/Tk; en un instalador completo Windows revisa Tcl/Tk/IDLE. `pip install tkinter` no lo incorpora al intérprete. |
| Tk 8.5, fallo nativo o diagnóstico de PyWrap en Mac | Usa la instalación de python.org con Tk 8.6+ y recrea el entorno si nació del Python de Apple. Ver sección 2.2. |
| `TclError` al abrir una ventana | Prueba Tk por separado con el mismo intérprete. Usa una sesión de escritorio local; un entorno sin pantalla puede permitir CLI y no GUI. No consideres omitidas las pruebas gráficas como validación visual. |
| Falta un módulo `pywrap` | Extrae/copía todos los `.py`, entra en la raíz y comprueba que no estés ejecutando otro `main.py`. No instales un paquete homónimo de internet. |
| Falta `benchmarks.reference_decoder` o un fixture | La copia está incompleta. Recupera `benchmarks/`, `tests/fixtures/` y las pruebas originales desde la entrega. No alteres los tests para que pasen. |
| `can't open file main.py`, ruta inexistente o archivo no seleccionado | Comprueba `pwd`/`Get-Location`, la carpeta interior del ZIP y las comillas en rutas con espacios. Usa **Examinar…** para escoger un archivo existente, no una carpeta. |
| Se intenta descomprimir un archivo ajeno | Selecciona un `.pkz` producido por PyWrap. La extensión por sí sola no convierte otro formato; respalda y verifica su transferencia si está corrupto. |
| Permisos denegados o carpeta de solo lectura | Usa una copia bajo tu usuario y una carpeta de salida escribible en CLI. Revisa permisos con las herramientas del sistema. No hace falta ejecutar como administrador ni aplicar permisos globales amplios. |
| Ya existe el destino | Es protección deliberada. Usa otra carpeta, cancela, o autoriza su reemplazo tras revisar el contenido; CLI: `--overwrite`. |
| Falla la escritura en USB | Revisa montaje, espacio, permisos y conexión. Conserva el error completo. Un fallo de copia puede dejar un destino parcial; revísalo antes de borrarlo o sustituirlo. Prueba primero una carpeta local. |
| Dos Python diferentes o editor/terminal no coinciden | Compara `sys.executable` en ambos, selecciona el intérprete en VS Code y abre una terminal nueva. No copies `.venv` ni borres instalaciones del sistema para resolverlo. |
| PowerShell bloquea `Activate.ps1` | Usa directamente `.\.venv\Scripts\python.exe`; no es necesario modificar la política de ejecución. |
| Pruebas con errores | Ejecuta la suite desde la raíz con el mismo Python, conserva el traceback y comprueba la copia/fixtures. Revisa Tk, permisos y omisiones. No sustituyas el comando por uno que descubra cero pruebas. |
| El `.pkz` es mayor que el original | Puede ser correcto: el árbol/cabecera añade espacio y los datos ya comprimidos pueden no reducirse. El ejemplo de 12 bytes genera 28. |

Si persiste un problema, comparte sistema operativo, versión Python, `sys.executable`, versión Tk, comando y error completos, sin adjuntar archivos personales. No hay dependencias externas que instalar para corregir un traceback de esta versión.

## 7. Preparar una entrega académica limpia

### 7.1 Selección y privacidad

Trabaja desde una copia revisada o genera un ZIP sin alterar la carpeta original. Conserva fuera de la entrega originales, comprimidos y recuperados personales, sus hashes y cualquier documento privado. Revisa también nombres de integrantes, capturas y contenido de los informes: que un archivo sea Markdown no lo hace automáticamente público.

El procedimiento siguiente incluye módulos, pruebas, todos los fixtures `.pkz`, documentación académica nombrada, capturas y registros públicos de benchmarks. Solo incluye `anita.txt` de las entradas y los marcadores de salida. Excluye por selección `.git`, entornos, cachés, metadatos, temporales y datos generados. Si agregas documentos académicos futuros, revisa y amplía la lista; no los agregues a ciegas junto con datos personales.

### 7.2 Crear el ZIP sin depender de commits

Copia el siguiente código a un archivo llamado **`preparar_entrega.py` fuera de la carpeta del proyecto** (por ejemplo, en su carpeta padre). Es una herramienta de preparación transitoria del manual, no un módulo nuevo de PyWrap. Guárdalo como texto UTF-8. Ejecútalo **estando en la raíz de PyWrap**. Crea el ZIP en la carpeta padre, agrega `MANIFEST_SHA256.json` y no reemplaza un ZIP existente.

```python
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED

root = Path.cwd().resolve()
output = (Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1
          else root.parent / 'PyWrap_entrega.zip')
if output.is_relative_to(root):
    raise SystemExit('Elige un ZIP fuera del proyecto.')

fixed = '''main.py
cli.py
README.md
VALIDACION.md
.gitignore
data/source/anita.txt
data/wrp/.gitkeep
data/unwrp/.gitkeep
tests/fixtures/README.md
benchmarks/README.md
benchmarks/before-64mib.json
benchmarks/after-64mib.json
benchmarks/before-8mib.json
benchmarks/after-8mib.json
docs/INSTALACION_Y_MIGRACION.md
docs/INFORME_ACADEMICO.md
docs/GUIA_SUSTENTACION.md
docs/PREGUNTAS_SUSTENTACION.md
docs/DEMO.md
docs/filesystem-validation.json
docs/screenshots/frecuencias.png
docs/screenshots/arbol.png
docs/screenshots/bits.png
docs/screenshots/estadisticas.png'''.splitlines()
selected = {root / name for name in fixed}
for folder in ('pywrap', 'tests', 'benchmarks'):
    selected.update((root / folder).glob('*.py'))
selected.update((root / 'tests' / 'fixtures').glob('*.pkz'))
if not (root / 'main.py').is_file() or len(list((root / 'tests' / 'fixtures').glob('*.pkz'))) < 4:
    raise SystemExit('Raíz incorrecta o fixtures incompletos.')
missing = [str(p.relative_to(root)) for p in selected if not p.is_file()]
if missing:
    raise SystemExit('Faltan archivos: ' + ', '.join(missing))
if output.exists():
    raise SystemExit('El ZIP ya existe; elige otro nombre de salida.')

manifest = {}
with ZipFile(output, 'x', compression=ZIP_DEFLATED) as archive:
    for path in sorted(selected):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        manifest[relative] = hashlib.sha256(data).hexdigest()
        archive.writestr('PyWrap_Huffman/' + relative, data)
    archive.writestr('PyWrap_Huffman/MANIFEST_SHA256.json',
                     json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
print('ZIP creado:', output)
print('Archivos del proyecto:', len(manifest))
print('Revisa su contenido y verifica la copia antes de entregarla.')
```

En **macOS**, suponiendo que el auxiliar está en la carpeta padre:

```bash
python3 ../preparar_entrega.py
python3 -m zipfile -l ../PyWrap_entrega.zip
python3 -m zipfile -t ../PyWrap_entrega.zip
shasum -a 256 ../PyWrap_entrega.zip
```

En **PowerShell**, propuesto:

```powershell
py ..\preparar_entrega.py
py -m zipfile -l ..\PyWrap_entrega.zip
py -m zipfile -t ..\PyWrap_entrega.zip
Get-FileHash ..\PyWrap_entrega.zip -Algorithm SHA256
```

Si ya existe el ZIP, pasa otra ruta como segundo argumento: `python3 ../preparar_entrega.py ../PyWrap_entrega_v2.zip` o `py ..\preparar_entrega.py ..\PyWrap_entrega_v2.zip`. No hace falta instalar herramientas ZIP externas. El manifiesto verifica que los archivos extraídos conservan sus bytes; no sustituye la revisión de privacidad ni autentica al remitente. Para comprobar que recibiste el ZIP esperado, compara también su hash con el valor del emisor.

Revisa el listado: debe aparecer `PyWrap_Huffman/`, los cuatro fixtures y todos los documentos listados; no deben aparecer `.venv`, `__pycache__`, `.DS_Store`, `.git`, temporales ni tus `.pkz` personales. `zipfile -t` verifica la integridad ZIP, no el funcionamiento de PyWrap.

### 7.3 Extraer y verificar el manifiesto

Usa un nombre de carpeta de prueba que **no exista**. Ejecuta cada instrucción por separado y detente si falla la creación; no extraigas sobre tu copia original.

**macOS**:

```bash
mkdir ../PyWrap_prueba_limpia
python3 -m zipfile -e ../PyWrap_entrega.zip ../PyWrap_prueba_limpia
cd ../PyWrap_prueba_limpia/PyWrap_Huffman
```

**PowerShell**, propuesto:

```powershell
New-Item -ItemType Directory -Path ..\PyWrap_prueba_limpia -ErrorAction Stop
py -m zipfile -e ..\PyWrap_entrega.zip ..\PyWrap_prueba_limpia
Set-Location ..\PyWrap_prueba_limpia\PyWrap_Huffman
```

Dentro de la raíz extraída, comprueba todos los hashes. Este código es común; en Windows reemplaza `python3` por `py`:

```bash
python3 -c "import hashlib,json; from pathlib import Path; r=Path('.'); m=json.loads((r/'MANIFEST_SHA256.json').read_text(encoding='utf-8')); bad=[p for p,h in m.items() if not (r/p).is_file() or hashlib.sha256((r/p).read_bytes()).hexdigest()!=h]; print('Archivos diferentes o ausentes:',bad); raise SystemExit(bool(bad))"
```

Espera una lista vacía y código 0. Verifica el manifiesto antes de generar nuevas salidas. El manifiesto no incluye su propio hash; el hash del ZIP sirve para comprobar el paquete completo.

### 7.4 Ensayo de instalación desde una copia limpia

Sin usar el entorno del proyecto original, sigue las instrucciones de tu plataforma y crea un entorno nuevo dentro de la copia extraída. No necesitas desinstalar Python ni modificar el sistema para este ensayo.

**macOS**:

```bash
python3 -m venv .venv
./.venv/bin/python -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
./.venv/bin/python -m tkinter
./.venv/bin/python main.py
./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python cli.py compress data/source/anita.txt
./.venv/bin/python cli.py decompress data/wrp/anita.txt.pkz
shasum -a 256 data/source/anita.txt data/unwrp/anita.txt
cmp data/source/anita.txt data/unwrp/anita.txt
```

Cierra cada ventana antes de continuar. Si el intérprete inicial era incorrecto, crea el entorno con el comando versionado correcto, según la sección 2.2.

**PowerShell**, propuesto:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -c "import sys, tkinter; print(sys.executable); print('Tk', tkinter.TkVersion)"
.\.venv\Scripts\python.exe -m tkinter
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe cli.py compress .\data\source\anita.txt
.\.venv\Scripts\python.exe cli.py decompress .\data\wrp\anita.txt.pkz
Get-FileHash .\data\source\anita.txt -Algorithm SHA256
Get-FileHash .\data\unwrp\anita.txt -Algorithm SHA256
fc.exe /b .\data\source\anita.txt .\data\unwrp\anita.txt
$LASTEXITCODE
```

No uses `--overwrite` en este primer ensayo: una copia limpia no debe traer esas salidas. Si aparecen, revisa cómo se preparó el ZIP. Conserva el ZIP limpio original para entregar; las salidas y el entorno creados durante el ensayo pertenecen a la carpeta de prueba.

## 8. Lista de verificación para el receptor

Marca cada punto con la evidencia real de ese computador:

- [ ] Extraje/copíe el proyecto completo a una ubicación escribible y encuentro `main.py`.
- [ ] `python3 --version` (Mac) o `py --version` (Windows) muestra una versión compatible.
- [ ] Revisé `sys.executable` y utilicé el mismo intérprete en todos los pasos.
- [ ] Tkinter está disponible; en Mac es Tk 8.6+. La demostración `-m tkinter` abre una ventana.
- [ ] No hay dependencias externas pendientes; si uso `.venv`, lo creé localmente.
- [ ] Abrí `main.py` y vi las tres pestañas de PyWrap.
- [ ] Ejecuté `-m unittest discover -s tests -v`: registré cantidad, fallos y omisiones, no solo la última línea.
- [ ] La copia conserva documentos, capturas y los cuatro fixtures históricos.
- [ ] Verifiqué el SHA-256 del ZIP/datos y, si existe, el manifiesto extraído.
- [ ] Comprimí `anita.txt`: 12 bytes originales, 30 bits, BS=6 y `.pkz` de 28 bytes.
- [ ] Descomprimí ese `.pkz` y recuperé `anita.txt`.
- [ ] Comparé los hashes y también los bytes (`cmp` o `fc.exe /b`): coinciden.
- [ ] Conservé por separado originales, `.pkz` y recuperados personales; no los incluí en la entrega académica.
- [ ] Si usé USB, esperé el final, revisé errores y expulsé el dispositivo correctamente.

## 9. Qué registrar al compartir una versión

Anota identificador de commit **si existe**, versión de Python, Tk y sistema, número de pruebas y omisiones, hash del ZIP y fecha de preparación. Guarda esa información junto a la entrega. El identificador de commit no sustituye los datos del usuario excluidos de Git.

Para la exposición, consulta [DEMO.md](DEMO.md), [GUIA_SUSTENTACION.md](GUIA_SUSTENTACION.md), [INFORME_ACADEMICO.md](INFORME_ACADEMICO.md) y [PREGUNTAS_SUSTENTACION.md](PREGUNTAS_SUSTENTACION.md). El historial de QA previo está en [VALIDACION.md](../VALIDACION.md).

## 10. Validación de este manual

Este apartado distingue la verificación local de las instrucciones de instalación que deben ejecutarse en cada receptor. No se reinstaló el sistema operativo ni se descargó un nuevo Python para esta fase.

| Comprobación | Evidencia de esta fase |
| --- | --- |
| Inspección de imports y rutas | Solo biblioteca estándar y módulos propios; sin manifiesto de dependencias externas. GUI/CLI mantienen las rutas descritas. |
| Python/Tk en macOS | Python 3.15.2, Tcl 9.0.4 y Tk 9.0.5 comprobados mediante un intérprete Tk real. |
| Compatibilidad mínima | Python 3.9.6: **54 aprobadas, 5 omitidas por Tk 8.5, 0 fallos**; 59 descubiertas. La interfaz no se valida con ese intérprete. |
| ZIP limpio | Se ejecutó el auxiliar del apartado 7.2: **46 archivos de proyecto y un manifiesto**, cuatro fixtures conservados, integridad ZIP y hashes correctos, sin datos personales ni cachés. Una segunda creación fue rechazada sin alterar el ZIP existente. |
| Copia independiente | Con un entorno virtual nuevo y Python 3.15.2: **59 aprobadas, 0 fallos y 0 omitidas**, en 4,979 s. CLI generó 28 bytes; `cmp` terminó con código 0 y ambos SHA-256 fueron iguales. También se comprobó una salida con espacios en su ruta y la activación del entorno en zsh. |
| Arranque de GUI | Integración con Tk real y ejecución de la entrada `main.py` con cierre automático de prueba; no se presenta como una instalación interactiva en otro computador. |
| Conservación del producto | Se compararon hashes del código, tests, fixtures y archivos previos para confirmar que esta fase solo añade el manual y el enlace del README. |
| VS Code | Instrucciones contrastadas con la documentación oficial; no se realizó una selección interactiva de intérprete durante esta fase. |
| Windows 10/11 | No ejecutado: quedan pendientes instalador, PowerShell, selección de intérprete y prueba completa en Windows. |
| Otro Mac / USB físico / GitHub remoto | No se realizó una transferencia a otro equipo ni una publicación. La evidencia previa de exFAT/FAT32 corresponde a imágenes montadas, no a hardware USB. |

SHA-256 del ejemplo original y recuperado en la copia: `6e07e9bbd00943f73c3379b39e61c07eafdf2f01cd4b5eb6ce60e0c33614d440`. La compresión conservó 30 bits, NF=5, TREE=22, BS=6, ZIP=4 y 28 bytes totales.

Las instrucciones de instalación se contrastaron con fuentes oficiales enlazadas en sus apartados. Los comandos que requieren nombres de usuario, rutas, URL o dispositivos reales son plantillas que el receptor debe adaptar; no se afirma haberlos ejecutado literalmente en ubicaciones ficticias.
