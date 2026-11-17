# PyWrap · Huffman

Proyecto sencillo para comprimir cualquier archivo a `.pkz` y recuperar sus bytes originales. No necesita paquetes de pip.

## Abrir

En Windows, doble clic en **`Iniciar_PyWrap.cmd`**. También puedes ejecutar:

```powershell
.\.venv\Scripts\python.exe main.py
```

En otro computador necesitas Python 3.10 o posterior con Tkinter. Puedes ejecutar `python main.py` directamente o crear tu propio entorno con `python -m venv .venv`; no copies el entorno virtual de otro equipo.

## Usar

1. Pulsa **Examinar…** y elige un archivo.
2. Pulsa **Comprimir** o **Descomprimir**.
3. El resultado muestra dónde se guardó y los tamaños de entrada y salida.

Los comprimidos quedan en `data/wrp/`; los recuperados, en `data/unwrp/`. La ventana pregunta antes de reemplazar una salida existente. Descomprimir abre los `.pkz` de PyWrap.

## Explicarlo

**Cuenta los bytes, construye el árbol de Huffman, cambia cada byte por su código binario y guarda el árbol junto a los datos. Para recuperar, recorre ese árbol siguiendo los bits.**

- `main.py`: inicia el programa.
- `pywrap/gui.py`: ventana con dos botones.
- `pywrap/huffman.py`: algoritmo y lectura/escritura de archivos.
- `cli.py`: alternativa opcional por consola.

La explicación paso a paso está en [docs/EXPLICACION.md](docs/EXPLICACION.md).

Lee y escribe por bloques de 64 KiB: no carga todo el archivo en memoria ni impone un tamaño máximo. El límite práctico es el disco y el sistema de archivos. Huffman puede aumentar el tamaño de archivos pequeños o ya comprimidos. Mantén el original sin cambios mientras se comprime.

Los archivos de pruebas y documentos anteriores están apartados en `docs/historico/`: no forman parte de los pasos de instalación, ejecución o explicación de esta versión.
