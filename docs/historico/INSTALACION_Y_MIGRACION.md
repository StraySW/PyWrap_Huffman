# Instalación y migración de PyWrap

Guía de la versión simplificada, verificada en Windows el 17 de noviembre de 2026 con Python 3.13.17 y Tk 8.6.

## Requisitos

Python 3.10 o posterior con Tkinter/Tcl/Tk, una sesión gráfica para la interfaz y una carpeta con permiso de escritura. La aplicación y las pruebas usan únicamente la biblioteca estándar; no hay `requirements.txt` ni paquetes de `pip` que instalar. La consola funciona sin Tkinter.

## Windows

Instala Python con Tcl/Tk desde la distribución oficial y abre una terminal nueva. Desde la carpeta que contiene `main.py`:

```powershell
py -3 --version
py -3 -c "import tkinter; print('Tk', tkinter.TkVersion)"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

Si no tienes el lanzador `py`, usa `python` para los tres primeros comandos. También puedes abrir `Iniciar_PyWrap.cmd` con doble clic. Usa preferentemente el Python de `.venv`: así no dependes del PATH ni necesitas activar el entorno o cambiar la política de ejecución de PowerShell.

Si `python` abre Microsoft Store o dice que no se encontró Python, todavía no estás usando un intérprete operativo. Instala Python y comprueba de nuevo, o utiliza la ruta completa de la instalación. Si aparece `No module named tkinter`, instala una distribución con soporte Tcl/Tk; no se soluciona instalando un paquete llamado tkinter con pip.

## macOS y Linux

Usa un Python con Tkinter. En macOS la aplicación rechaza Tk anterior a 8.6 para evitar el problema conocido del Tk 8.5 de Apple. En Linux, instala el soporte Tk correspondiente a tu intérprete si no está incluido.

```bash
python3 --version
python3 -c "import tkinter; print('Tk', tkinter.TkVersion)"
python3 -m venv .venv
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py
```

Estas instrucciones corresponden al código multiplataforma; esta revisión se ejecutó en Windows. No se atribuye a esta entrega la evidencia de otras versiones descrita en documentos históricos.

## Llevarlo a otro equipo

Copia `main.py`, `cli.py`, `Iniciar_PyWrap.cmd`, `pywrap/`, `tests/`, `data/source/`, la documentación y los marcadores de las carpetas de salida. **Crea de nuevo `.venv` en el equipo receptor**: los entornos virtuales no son portátiles. No hacen falta `analysis.py`, `education.py`, `decoding.py` ni `benchmarks/`; no forman parte de esta versión.

Conserva aparte tus originales y salidas si quieres trasladarlos: Git excluye el contenido generado de `data/wrp/` y `data/unwrp/`. No es necesario borrar archivos para migrar.

## Validación

La suite debe indicar `Ran 24 tests` y `OK` con Tk disponible. Después sigue [DEMO.md](DEMO.md) para comprimir, recuperar y comparar SHA-256. La interfaz actual tiene dos botones y un resultado, sin pestañas educativas. Procesa cualquier tipo de archivo por bloques, sin tamaño máximo impuesto por la aplicación; el espacio y el sistema de archivos determinan el límite práctico.
