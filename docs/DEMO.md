# Demostración reproducible de PyWrap

Todo funciona **sin internet** y sin archivos personales. Los comandos se ejecutan desde la **carpeta raíz del proyecto**. Los resultados esperados se obtuvieron ejecutando estos mismos comandos en macOS con Python 3.15.2 y, para la consola, también con Python 3.9.6.

| Sistema | Ejecutar Python | Comparar archivos |
| --- | --- | --- |
| macOS / Linux | `python3` | `shasum -a 256`, `cmp` |
| Windows (no verificado) | `py` | `Get-FileHash`, `fc.exe /b` |

---

## 0. Preparación (antes de entrar a la sala)

1. **Comprueba Python y Tkinter.**

   ```bash
   python3 --version
   python3 -m tkinter
   ```

   El segundo comando debe abrir una ventana pequeña; ciérrala. En macOS se necesita Tk 8.6 o posterior (ver README).

2. **Ejecuta las pruebas.** Esta captura de pantalla es una buena evidencia si el jurado la pide.

   ```bash
   python3 -m unittest discover -s tests
   ```

   Resultado esperado: `Ran 59 tests` y `OK`, en unos 6 segundos. Las pruebas de interfaz abren y cierran ventanas reales, y Tk puede imprimir líneas como `invalid command name "…_check_events"`. Es un aviso de Tk sobre un temporizador de una ventana ya cerrada, no un fallo: lo que cuenta es el `OK` final. Con un Python que trae Tk 8.5, como el de Apple, verás `OK (skipped=5)`, porque se omiten las pruebas de GUI.

3. **Genera el archivo grande**: 7,7 MB de texto con semilla fija, siempre idéntico.

   ```bash
   python3 -c "import random; r=random.Random(2026); w='el algoritmo de Huffman asigna códigos más cortos a los símbolos más frecuentes del árbol ñandú'.split(); open('data/source/demo_grande.txt','w',encoding='utf-8').write('\n'.join(' '.join(r.choice(w) for _ in range(12)) for _ in range(100000)))"
   ```

   Comprobación: el archivo debe medir **7.723.775 bytes** y su SHA-256 debe empezar por `437d3a5d`.

   ```bash
   shasum -a 256 data/source/demo_grande.txt
   ```

   El archivo está excluido de Git (`.gitignore`), así que no se entregará por accidente.

4. **Opcional: empieza con las carpetas de salida vacías.** Así la aplicación no pedirá confirmación de reemplazo.

   ```bash
   rm -f data/wrp/anita.txt.pkz data/wrp/demo_grande.txt.pkz data/unwrp/anita.txt data/unwrp/demo_grande.txt
   ```

   Solo se borran salidas de la demostración; los marcadores `.gitkeep` se conservan. Si prefieres no limpiar, la aplicación preguntará «¿Deseas reemplazarlo?»; responde **Sí** y aprovecha para explicar que PyWrap nunca sobrescribe sin permiso.

5. **Abre la aplicación y una terminal** en la carpeta del proyecto.

   ```bash
   python3 main.py
   ```

**Plan B:** si la interfaz no abre en el equipo de la sala, todos los pasos tienen una alternativa por consola (indicada como *Consola*). Las capturas reales están en `docs/screenshots/`.

---

## 1. El ejemplo `anita patina`

1. Abre la pestaña **Análisis de Huffman**.
2. Pulsa **Ejemplo: anita patina**. No se crean archivos.

Resultado esperado: `Ejemplo: anita patina · 12 bytes · 6 símbolos.`

**Qué decir:** «Son 12 bytes contando el espacio. Huffman los representará con 30 bits en lugar de 96».

## 2. Visualización del árbol

1. Abre la subpestaña **Árbol binario**.
2. Señala la raíz `Σ f=12`, las ramas marcadas `0` (izquierda) y `1` (derecha), las hojas verdes y los nodos internos azules.
3. En la subpestaña **Frecuencias y códigos**, haz **doble clic en la fila `p`**. Volverás al árbol con su camino resaltado.

Resultado esperado: `p · byte 112 · frecuencia 1 · código 1001 · 4 bits`.

4. Explica las uniones de la cola de prioridad:

   | Paso | Unión | Resultado |
   | --- | --- | ---: |
   | 1 | espacio + p | 2 |
   | 2 | (espacio, p) + i | 4 |
   | 3 | n + t | 4 |
   | 4 | (espacio, p, i) + a | 8 |
   | 5 | (n, t) + (espacio, p, i, a) | 12 |

Si el árbol no se ve completo, arrástralo con el ratón o usa las barras de desplazamiento.

## 3. Tabla de frecuencias y códigos

Abre la subpestaña **Frecuencias y códigos**. Valores esperados:

| Símbolo | Byte | Frecuencia | Código | Bits |
| --- | ---: | ---: | --- | ---: |
| ESPACIO | 32 | 1 | 1000 | 4 |
| a | 97 | 4 | 11 | 8 |
| i | 105 | 2 | 101 | 6 |
| n | 110 | 2 | 00 | 4 |
| p | 112 | 1 | 1001 | 4 |
| t | 116 | 2 | 01 | 4 |

La suma de la columna «Bits totales» es **30**.

Después abre **Bits y bytes** y señala:

- la secuencia `110010101111000100111011010011`;
- el relleno de 2 bits;
- los grupos MSB-first y los valores `[202, 241, 59, 76]`;
- `BS=6`;
- el TREE en hexadecimal.

Por último, abre la pestaña **Estadísticas** y muestra que ZIP mide 4 B, el encabezado 24 B y el total 28 B.

## 4. Compresión del archivo

**Interfaz:**

1. Abre la pestaña **Comprimir / Descomprimir** y elige **Comprimir (Wrap)**.
2. Pulsa **Examinar…** y selecciona `data/source/anita.txt`.
3. Pulsa **▶ Ejecutar**.

Resultado esperado en las tarjetas:

| Original | Archivo .pkz | Variación total | Símbolos | Nodos |
| --- | --- | --- | --- | --- |
| 12 B | 28 B | Crecimiento 133.33% (en ámbar) | 6 | 11 |

La consola de resultados muestra `NF: 5`, `TREE: 22 bytes`, `BS: 6` y `ZIP: 4 bytes`. El archivo queda en `data/wrp/anita.txt.pkz`.

*Consola:*

```bash
python3 cli.py compress data/source/anita.txt
```

Si el destino ya existe, la consola termina con `Error de PyWrap: El archivo ya existe … Confirma antes de sobrescribir.` Para reemplazarlo, añade `--overwrite`.

**Mostrar los bytes del `.pkz`** (funciona en cualquier sistema):

```bash
python3 -c "print(open('data/wrp/anita.txt.pkz','rb').read().hex(' '))"
```

Resultado esperado:

```text
05 00 00 00 00 01 6e 01 74 00 00 00 00 00 00 01 20 01 70 01 69 01 61 06 ca f1 3b 4c
```

Explícalo por partes: `05` es NF; los 22 bytes siguientes son TREE; `06` es BS; y `ca f1 3b 4c` es ZIP, es decir, 202, 241, 59 y 76.

## 5. Descompresión

**Interfaz:**

1. Elige **Descomprimir (UnWrap)**.
2. Pulsa **Examinar…** y selecciona `data/wrp/anita.txt.pkz`.
3. Pulsa **▶ Ejecutar**.

Resultado: `data/unwrp/anita.txt`. La consola indica `Decodificación completada`.

*Consola:*

```bash
python3 cli.py decompress data/wrp/anita.txt.pkz
```

**Qué decir:** «El descompresor no usa el original. Lee NF, reconstruye el árbol desde TREE y recorre los bits de ZIP desde la raíz hasta cada hoja».

## 6. Comparación de integridad

**macOS / Linux:**

```bash
shasum -a 256 data/source/anita.txt data/unwrp/anita.txt
cmp data/source/anita.txt data/unwrp/anita.txt && echo "Archivos idénticos"
```

Resultado esperado: dos líneas con el mismo hash, `6e07e9bbd00943f73c3379b39e61c07eafdf2f01cd4b5eb6ce60e0c33614d440`, y el mensaje `Archivos idénticos`.

**Cualquier sistema (solo Python):**

```bash
python3 -c "import hashlib,sys; h=[hashlib.sha256(open(p,'rb').read()).hexdigest() for p in sys.argv[1:]]; print(*h, sep='\n'); print('IDÉNTICOS' if h[0]==h[1] else 'DIFERENTES')" data/source/anita.txt data/unwrp/anita.txt
```

**Windows PowerShell** (no verificado):

```powershell
Get-FileHash data\source\anita.txt, data\unwrp\anita.txt -Algorithm SHA256
fc.exe /b data\source\anita.txt data\unwrp\anita.txt
```

## 7. Un archivo real de mayor tamaño

Usa `data/source/demo_grande.txt`, el archivo generado en la preparación.

1. **Análisis.** En **Análisis de Huffman → Analizar archivo original…**, selecciona `demo_grande.txt`. Resultado esperado: 7.723.775 bytes y **25 símbolos**. Comenta que la `ñ` y las vocales con tilde aparecen como bytes `\xC3`, `\xB1`… porque en UTF-8 cada una ocupa 2 bytes.
2. **Compresión.** En **Comprimir / Descomprimir**, comprime `data/source/demo_grande.txt`. Resultado esperado: **7,723,775 B → 4,152,648 B**, `Reducción 46.24%` en verde, 25 símbolos y 49 nodos.
3. **Descompresión.** Descomprime `data/wrp/demo_grande.txt.pkz`.

   *Consola para los pasos 2 y 3, con tiempos medidos:*

   ```bash
   time python3 cli.py compress data/source/demo_grande.txt
   time python3 cli.py decompress data/wrp/demo_grande.txt.pkz
   ```

   | Python | Comprimir | Descomprimir |
   | --- | ---: | ---: |
   | 3.15.2 | ≈ 1,1 s | ≈ 0,3 s |
   | 3.9.6 | ≈ 2,3 s | ≈ 0,5 s |

   Los tiempos dependen del equipo.

4. **Integridad.**

   ```bash
   shasum -a 256 data/source/demo_grande.txt data/unwrp/demo_grande.txt
   cmp data/source/demo_grande.txt data/unwrp/demo_grande.txt && echo "Archivos idénticos"
   ```

   Hash esperado en ambos: `437d3a5df9931bd066384722f15b8c199235346859c61e0ce4211fea9fe909ca`.

**Qué decir:** «Con 12 bytes el archivo crecía; con 7,7 MB se reduce casi a la mitad. El árbol cuesta lo mismo (98 bytes con 25 símbolos), pero el ahorro crece con el tamaño».

### Variante opcional: un archivo ya comprimido

Si llevas un PDF, una foto o un video **no personal** (por ejemplo, el programa de la asignatura), comprímelo y descomprímelo igual. El tamaño apenas cambiará; en las pruebas fueron +1,36 % para un PDF, −0,83 % para un JPG y +0,00 % para un MP4. La recuperación será idéntica. Sirve para explicar que Huffman no puede comprimir datos que ya no tienen redundancia.

---

## Después de la demostración: empaquetar una entrega limpia

`.gitignore` excluye `.DS_Store`, `__pycache__`, temporales, las salidas de `data/wrp` y `data/unwrp` y el archivo `demo_grande.txt`. La forma más segura de generar el ZIP de entrega es crear un commit y exportarlo con Git:

```bash
git add -A
git status            # revisa que no aparezcan archivos inesperados
git commit -m "Entrega PyWrap"
git archive --format=zip -o ../PyWrap_entrega.zip HEAD
```

Al comprobarlo sobre una copia del proyecto, el ZIP resultante contenía 55 entradas (archivos y carpetas): código, pruebas, fixtures, documentación, capturas y benchmarks, sin archivos del sistema ni salidas generadas. Si comprimes la carpeta con el explorador de archivos, se incluirán también `.DS_Store`, `__pycache__` y la carpeta `.git`.
