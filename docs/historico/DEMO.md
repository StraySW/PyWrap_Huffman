# Demostración reproducible de PyWrap

Versión simplificada. Ejecuta desde la raíz del proyecto en PowerShell. Si ya tienes salidas con estos nombres, la consola las conserva y termina con error; añade `--overwrite` únicamente si quieres reemplazarlas.

## 1. Ejecutar las pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado esperado: 24 pruebas, `OK`, con Tk disponible.

## 2. Comprimir el ejemplo

```powershell
.\.venv\Scripts\python.exe cli.py compress data/source/anita.txt
```

El original contiene `anita patina`, sin salto de línea: 12 bytes y 6 símbolos. La salida es `data/wrp/anita.txt.pkz`, de 28 bytes. NF=5, TREE=22, BS=6 y ZIP=4. Crece un 133,33 % por el encabezado.

## 3. Recuperar y comparar

```powershell
.\.venv\Scripts\python.exe cli.py decompress data/wrp/anita.txt.pkz
Get-FileHash data/source/anita.txt, data/unwrp/anita.txt -Algorithm SHA256
fc.exe /b data\source\anita.txt data\unwrp\anita.txt
```

Ambos SHA-256 deben ser:

```text
6e07e9bbd00943f73c3379b39e61c07eafdf2f01cd4b5eb6ce60e0c33614d440
```

`fc.exe` debe indicar que no hay diferencias.

## 4. Ver los bytes del formato

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; print(Path('data/wrp/anita.txt.pkz').read_bytes().hex(' '))"
```

Salida esperada:

```text
05 00 00 00 00 01 6e 01 74 00 00 00 00 00 00 01 20 01 70 01 69 01 61 06 ca f1 3b 4c
```

`05` es NF; siguen 22 bytes de TREE; `06` es BS; `ca f1 3b 4c` son los 4 bytes de ZIP.

## 5. Hacerlo desde la ventana

Abre `Iniciar_PyWrap.cmd`. Pulsa **Examinar…**, selecciona `data/source/anita.txt` y pulsa **Comprimir**. Si seguiste la demostración de consola, ya existe el destino: puedes aceptar reemplazar esa salida de ejemplo o cancelar para demostrar la protección. Después examina `data/wrp/anita.txt.pkz` y pulsa **Descomprimir**. El resultado muestra la ruta y los tamaños. La barra indica actividad y la ventana sigue respondiendo mientras trabaja.

La ventana actual no incluye árbol visual ni pestañas de análisis. En macOS/Linux usa `.venv/bin/python` y compara los archivos mediante Python u otras herramientas del sistema.
