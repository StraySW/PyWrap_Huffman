# -*- coding: utf-8 -*-
"""Genera la Guía de estudio de Huffman (PDF) a partir de su fuente Markdown.

Uso, desde la carpeta del proyecto:
    python output/guia_estudio/generar_guia_estudio.py            genera el PDF
    python output/guia_estudio/generar_guia_estudio.py --tablas   muestra las tablas esperadas

Entrada:  output/guia_estudio/Guia_Estudio_Huffman_Definitiva.md   (texto editable)
Salida:   output/pdf/Guia_Estudio_Huffman_Definitiva.pdf

Requisitos: Windows (fuentes Segoe UI y Consolas), ReportLab y pypdf.
Los programas comprimir.py y descomprimir.py solo usan la biblioteca estándar; este
generador es una herramienta aparte para producir la documentación.

Antes de dibujar, el generador comprueba que la guía coincide con el código real.
Si algo no coincide, se detiene y dice qué línea del Markdown hay que corregir:
  1. ```python archivo.py:a-b```   debe ser idéntico a esas líneas del archivo;
  2. ```python ejecutar```         se ejecuta y su salida debe coincidir con ```salida```;
  3. ```terminal```                cada "> python ..." se ejecuta con los programas reales;
  4. <!-- comprobar: expresión --> debe ser verdadera; usa la traza T de AAAAABBC;
  5. <!-- tabla: nombre -->        la tabla siguiente se compara con la traza.

Extensiones de Markdown que entiende:
  # Capítulo  /  # Título {-}     capítulo numerado / sin número (nueva página)
  ## Sección                      numerada automáticamente (N.M) y en el índice
  ### Concepto, ### En palabras sencillas, ### Código real,
  ### Ejecución con AAAAABBC, ### Resultado, ### Conclusión   etiquetas de aprendizaje
  > [!IDEA] / [!CLAVE] / [!ATENCION] / [!EJERCICIO] / [!SOLUCION] / [!PREGUNTA] / [!NOTA] Título
  ```calculo```  cálculo paso a paso (líneas que empiezan con "!" se resaltan)
  ```texto```    texto monoespaciado
  ```diagrama nombre```   diagrama dibujado con los datos reales (el contenido es solo texto de apoyo)
  <!-- anchos: 20, 50, 30 -->     proporción de columnas de la tabla siguiente
  <!-- salto -->                  salto de página
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import html
import importlib.util
import io
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True  # No crear __pycache__ en el proyecto al importar los programas.

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1]
FUENTE_MD = AQUI / "Guia_Estudio_Huffman_Definitiva.md"
SALIDA_PDF = PROYECTO / "output" / "pdf" / "Guia_Estudio_Huffman_Definitiva.pdf"
PROGRAMAS = ("comprimir.py", "descomprimir.py")


class ErrorGuia(Exception):
    """La guía no coincide con el código real."""


# =====================================================================
# 1. Código real, git y huellas
# =====================================================================
CODIGO = {n: (PROYECTO / n).read_text(encoding="utf-8").splitlines() for n in PROGRAMAS}
SHA = {n: hashlib.sha256((PROYECTO / n).read_bytes()).hexdigest() for n in PROGRAMAS}
NLINEAS = {n: len(CODIGO[n]) for n in PROGRAMAS}


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=PROYECTO, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


COMMIT = git("rev-parse", "--short", "HEAD")
SIN_CONFIRMAR = git("status", "--porcelain", "--", *PROGRAMAS)


def linea(archivo, texto):
    """Número de la única línea del archivo que contiene `texto`."""
    hallado = [i for i, l in enumerate(CODIGO[archivo], 1) if texto in l]
    if len(hallado) != 1:
        raise ErrorGuia(f"'{texto}' aparece {len(hallado)} veces en {archivo}")
    return hallado[0]


def lc(texto):
    return linea("comprimir.py", texto)


def ld(texto):
    return linea("descomprimir.py", texto)


# =====================================================================
# 2. Ejecutar los programas reales con un trazador
# =====================================================================
def cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, PROYECTO / archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


COMP = cargar("comprimir_guia_estudio", "comprimir.py")
DESC = cargar("descomprimir_guia_estudio", "descomprimir.py")


def foto(f_locals):
    r = {}
    for k, v in dict(f_locals).items():
        if isinstance(v, bytearray):
            r[k] = bytes(v)
        elif isinstance(v, (list, dict, set)):
            r[k] = copy.copy(v)
        elif isinstance(v, (int, str, bytes, tuple, type(None))):
            r[k] = v
    return r


class Traza:
    """Valores reales de una ejecución de comprimir() y descomprimir()."""


def trazar(datos, nombre):
    eventos, pila = [], []
    de_archivo = {COMP.__file__: "comprimir.py", DESC.__file__: "descomprimir.py"}

    def trazador(frame, evento, arg):
        archivo = de_archivo.get(frame.f_code.co_filename)
        if archivo is None:
            return None
        func = frame.f_code.co_name
        if evento == "call":
            pila.append(func)
        eventos.append({"archivo": archivo, "func": func, "evento": evento, "linea": frame.f_lineno,
                        "loc": foto(frame.f_locals), "marco": id(frame), "prof": pila.count(func) - 1,
                        "ret": arg if evento == "return" else None})
        if evento == "return":
            pila.pop()
        return trazador

    T = Traza()
    with tempfile.TemporaryDirectory() as tmp:
        original = Path(tmp) / nombre
        original.write_bytes(datos)
        consola = io.StringIO()
        sys.settrace(trazador)
        try:
            with contextlib.redirect_stdout(consola):
                ruta_pkz = COMP.comprimir(str(original))
                ruta_rec = DESC.descomprimir(str(ruta_pkz))
        finally:
            sys.settrace(None)
        T.pkz, T.recuperado = Path(ruta_pkz).read_bytes(), Path(ruta_rec).read_bytes()
    T.datos, T.consola = datos, consola.getvalue()

    # ---- Compresión ----
    ev = [e for e in eventos if e["archivo"] == "comprimir.py"]
    T.nodos_inicio, T.vueltas = None, []
    for e in ev:
        if e["func"] != "comprimir" or e["evento"] != "line":
            continue
        loc, n = e["loc"], e["linea"]
        if n == lc("while len(nodos) > 1:"):
            if T.nodos_inicio is None:
                T.nodos_inicio = list(loc["nodos"])
            else:
                T.vueltas[-1]["despues"] = list(loc["nodos"])
        elif n == lc("peso_izq, minimo_izq, izquierda = nodos.pop(0)"):
            antes = T.vueltas[-1]["despues"] if T.vueltas else T.nodos_inicio
            T.vueltas.append({"antes": antes, "ordenada": list(loc["nodos"])})
        elif n == lc("minimo = min(minimo_izq, minimo_der)"):
            T.vueltas[-1]["izq"] = (loc["peso_izq"], loc["minimo_izq"], loc["izquierda"])
            T.vueltas[-1]["der"] = (loc["peso_der"], loc["minimo_der"], loc["derecha"])
        elif n == lc("nodos.append((peso_izq + peso_der, minimo"):
            v = T.vueltas[-1]
            v["minimo"] = loc["minimo"]
            v["nuevo"] = (loc["peso_izq"] + loc["peso_der"], loc["minimo"], (loc["izquierda"], loc["derecha"]))
        elif n == lc("codigos = {}"):
            T.nodos_fin = list(loc["nodos"])
        elif n == lc('bits += "0" * (8 - bs)'):
            T.bits_datos, T.bs = loc["bits"], loc["bs"]
    fin = next(e for e in ev if e["func"] == "comprimir" and e["evento"] == "return")["loc"]
    T.frecuencias, T.codigos, T.arbol = fin["frecuencias"], fin["codigos"], fin["arbol"]
    T.bits_relleno, T.zip, T.nf, T.contenido = fin["bits"], fin["zip_bytes"], fin["nf"], fin["contenido"]
    T.raiz = T.nodos_fin[0][2] if T.nodos_fin else None
    if not getattr(T, "bits_datos", None):
        T.bits_datos, T.bs = "", fin["bs"]
    T.recorrer = [{"nodo": e["loc"]["nodo"], "codigo": e["loc"]["codigo"], "prof": e["prof"]}
                  for e in ev if e["func"] == "recorrer" and e["evento"] == "call"]

    # ---- Descompresión ----
    ev = [e for e in eventos if e["archivo"] == "descomprimir.py"]
    T.lecturas, abiertas, T.pasos = [], {}, []
    for e in ev:
        loc, n = e["loc"], e["linea"]
        if e["func"] == "leer_arbol":
            if e["evento"] == "call":
                d = {"prof": e["prof"]}
                abiertas.setdefault(e["marco"], []).append(d)
                T.lecturas.append(d)
            elif e["evento"] == "line" and n == ld("posicion += 2"):
                abiertas[e["marco"]][-1].update(posicion=loc["posicion"], tipo=loc["tipo"], valor=loc["valor"])
            elif e["evento"] == "return":
                d = abiertas[e["marco"]].pop()
                d.update(devuelve=e["ret"], despues=loc.get("posicion"))
        elif e["func"] == "descomprimir" and e["evento"] == "line":
            if n == ld("posicion = 1"):
                T.d_nf, T.fin_arbol = loc["nf"], loc["fin_arbol"]
            elif n == ld("if posicion != fin_arbol:"):
                T.raiz_d, T.pos_final = loc["raiz"], loc["posicion"]
            elif n == ld('if "1" in f"{zip_bytes[-1]:08b}"[bs:]'):
                T.d_bs, T.d_zip = loc["bs"], loc["zip_bytes"]
            elif n == ld("nodo = nodo[int(bit)]"):
                T.pasos.append({"indice": loc["indice"], "byte": loc["byte"], "validos": loc["validos"],
                                "bit": loc["bit"], "antes": loc["nodo"], "emite": None})
            elif n == ld("nodo = nodo[int(bit)]") + 1:
                T.pasos[-1]["despues"] = loc["nodo"]
            elif n == ld("recuperado.append(nodo)"):
                T.pasos[-1]["emite"] = loc["nodo"]
    return T


def hexa(b):
    return " ".join(f"{x:02X}" for x in b)


def comprimir_bytes(datos, nombre="entrada.bin"):
    """Ejecuta el comprimir() real y devuelve los bytes del .pkz."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / nombre
        p.write_bytes(datos)
        with contextlib.redirect_stdout(io.StringIO()):
            return Path(COMP.comprimir(str(p))).read_bytes()


def descomprimir_bytes(pkz, nombre="caso.pkz", salida=None):
    """Ejecuta el descomprimir() real. Devuelve los bytes recuperados o el mensaje de error."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / nombre
        p.write_bytes(pkz)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                destino = DESC.descomprimir(str(p), None if salida is None else str(Path(tmp) / salida))
            return Path(destino).read_bytes()
        except (OSError, ValueError) as error:
            return str(error)


def error_sin_linea(texto):
    """Ejecuta, sobre el .pkz de AAAAABBC, una copia en memoria de descomprimir.py sin la línea que
    contiene `texto` (el archivo real no se toca). Devuelve (excepción, línea del archivo real donde ocurre)."""
    quitada = ld(texto)
    copia = CODIGO["descomprimir.py"][:quitada - 1] + CODIGO["descomprimir.py"][quitada:]
    espacio = {"__name__": "copia_de_descomprimir"}
    exec(compile("\n".join(copia), "copia_de_descomprimir.py", "exec"), espacio)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "aaaaabbc.txt.pkz"
        p.write_bytes(T.pkz)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                espacio["descomprimir"](str(p))
        except Exception as error:  # noqa: BLE001
            marcos = [m for m in traceback.extract_tb(error.__traceback__)
                      if m.filename == "copia_de_descomprimir.py"]
            n = marcos[-1].lineno
            return type(error).__name__, n + 1 if n >= quitada else n
    return None, None


def recomprimir_demo(nombre):
    """Descomprime un .pkz de la carpeta de demostración y vuelve a comprimir el resultado con el código real.
    Devuelve (.pkz de la carpeta, .pkz nuevo, ¿el nuevo recupera el mismo contenido?)."""
    original = (PROYECTO / "Descomprimir estos archivos" / nombre).read_bytes()
    datos = descomprimir_bytes(original, nombre)
    nuevo = comprimir_bytes(datos, nombre[:-4])
    return original, nuevo, descomprimir_bytes(nuevo, nombre) == datos


def peso(arbol, frec):
    return frec[arbol] if isinstance(arbol, int) else peso(arbol[0], frec) + peso(arbol[1], frec)


def camino_de(arbol, buscado, camino=""):
    if arbol is buscado or (isinstance(arbol, int) and arbol == buscado):
        return camino
    if isinstance(arbol, tuple):
        for bit in "01":
            r = camino_de(arbol[int(bit)], buscado, camino + bit)
            if r is not None:
                return r
    return None


def leer_codigos(T):
    """Agrupa el recorrido bit a bit de descomprimir() en códigos completos."""
    codigos, actual = [], None
    for p in T.pasos:
        if actual is None:
            actual = {"bits": "", "bytes": []}
        actual["bits"] += p["bit"]
        actual["bytes"].append(p["indice"])
        if p["emite"] is not None:
            actual["simbolo"] = chr(p["emite"])
            codigos.append(actual)
            actual = None
    return codigos


T = trazar(b"AAAAABBC", "aaaaabbc.txt")
T2 = trazar(b"ABBCCC", "abbccc.txt")
if T.recuperado != T.datos or T2.recuperado != T2.datos:
    raise ErrorGuia("La ejecución real no recuperó los datos")


# =====================================================================
# 3. Lectura del Markdown
# =====================================================================
def dividir_fila(fila):
    """Separa una fila de tabla por '|' sin romper `código` ni '\\|'."""
    s = fila.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    celdas, actual, en_codigo, i = [], "", False, 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and s[i + 1:i + 2] == "|":
            actual += "|"
            i += 2
            continue
        if ch == "`":
            en_codigo = not en_codigo
        if ch == "|" and not en_codigo:
            celdas.append(actual.strip())
            actual = ""
        else:
            actual += ch
        i += 1
    celdas.append(actual.strip())
    return celdas


INICIO_BLOQUE = re.compile(r"^(```|#{1,3}\s|>|\s*\||<!--|\s*(?:[-*]|\d+\.)\s)")


def parsear(lineas, base=0):
    bloques, i = [], 0
    while i < len(lineas):
        l, num = lineas[i], base + i + 1
        if not l.strip():
            i += 1
        elif l.lstrip().startswith("<!--"):
            buf = [l]
            while "-->" not in buf[-1] and i + 1 < len(lineas):
                i += 1
                buf.append(lineas[i])
            texto = "\n".join(buf).strip()
            bloques.append({"tipo": "comentario", "texto": texto[4:-3].strip(), "linea": num})
            i += 1
        elif l.startswith("```"):
            info, cuerpo = l[3:].strip(), []
            i += 1
            while i < len(lineas) and not lineas[i].startswith("```"):
                cuerpo.append(lineas[i])
                i += 1
            bloques.append({"tipo": "codigo", "info": info, "lineas": cuerpo, "linea": num})
            i += 1
        elif re.match(r"^#{1,3}\s", l):
            m = re.match(r"^(#{1,3})\s+(.*?)\s*(\{-\})?\s*$", l)
            bloques.append({"tipo": "h", "nivel": len(m.group(1)), "texto": m.group(2),
                            "numerado": not m.group(3), "linea": num})
            i += 1
        elif l.startswith(">"):
            buf = []
            while i < len(lineas) and lineas[i].startswith(">"):
                t = lineas[i][1:]
                buf.append(t[1:] if t.startswith(" ") else t)
                i += 1
            m = re.match(r"^\[!(\w+)\]\s*(.*)$", buf[0])
            clase, titulo, cuerpo = (m.group(1).upper(), m.group(2), buf[1:]) if m else ("NOTA", "", buf)
            bloques.append({"tipo": "aviso", "clase": clase, "titulo": titulo,
                            "bloques": parsear(cuerpo, num), "linea": num})
        elif l.lstrip().startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                filas.append(dividir_fila(lineas[i]))
                i += 1
            if len(filas) < 2 or not all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in filas[1]):
                raise ErrorGuia(f"Línea {num}: a la tabla le falta la fila |---|")
            bloques.append({"tipo": "tabla", "encabezado": filas[0], "filas": filas[2:], "linea": num})
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s", l):
            ordenada = bool(re.match(r"^\s*\d+\.", l))
            items = []
            while i < len(lineas):
                m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", lineas[i])
                if m and m.group(1)[0].isdigit() == ordenada:
                    items.append(m.group(2))
                elif items and lineas[i].startswith("  ") and lineas[i].strip():
                    items[-1] += " " + lineas[i].strip()
                else:
                    break
                i += 1
            bloques.append({"tipo": "lista", "ordenada": ordenada, "items": items, "linea": num})
        else:
            buf = []
            while i < len(lineas) and lineas[i].strip() and not INICIO_BLOQUE.match(lineas[i]):
                buf.append(lineas[i].strip())
                i += 1
            bloques.append({"tipo": "p", "texto": " ".join(buf), "linea": num})
    return bloques


def leer_fuente():
    lineas = FUENTE_MD.read_text(encoding="utf-8").splitlines()
    meta, inicio = {}, 0
    if lineas and lineas[0].strip() == "---":
        j = 1
        while lineas[j].strip() != "---":
            clave, valor = lineas[j].split(":", 1)
            meta[clave.strip()] = valor.strip()
            j += 1
        inicio = j + 1
    return meta, parsear(lineas[inicio:], inicio)


def todos(bloques):
    """Recorre los bloques, incluidos los que están dentro de avisos, en orden."""
    for b in bloques:
        yield b
        if b["tipo"] == "aviso":
            yield from todos(b["bloques"])


# =====================================================================
# 4. Verificación de la guía contra el código real
# =====================================================================
def norm(s):
    s = re.sub(r"\*\*|`", "", s)
    return re.sub(r"\s+", " ", s).strip()


def ejecutar_fragmento(codigo):
    with tempfile.TemporaryDirectory() as tmp, contextlib.chdir(tmp):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(codigo, "<guía>", "exec"), {"__name__": "__guia__"})
        return buf.getvalue()


class Terminal:
    """Carpeta temporal donde se ejecutan los comandos de los bloques ```terminal```."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="guia_terminal_"))
        for n in PROGRAMAS:
            shutil.copy2(PROYECTO / n, self.dir / n)
        for nombre, contenido in (("aaaaabbc.txt", b"AAAAABBC"), ("abbccc.txt", b"ABBCCC"),
                                  ("equis.txt", b"X" * 17), ("vacio.txt", b"")):
            (self.dir / nombre).write_bytes(contenido)

    def ejecutar(self, comando):
        partes = [p.strip('"') for p in shlex.split(comando, posix=False)]
        if partes[0] != "python" or partes[1] not in PROGRAMAS:
            raise ErrorGuia(f"Comando no admitido en la guía: {comando}")
        r = subprocess.run([sys.executable, *partes[1:]], cwd=self.dir, capture_output=True,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        return (r.stdout + r.stderr).decode("utf-8").replace("\r\n", "\n").strip("\n")

    def cerrar(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def camino_texto(codigo):
    return ", ".join("izquierda" if b == "0" else "derecha" for b in codigo)


def nombre_nodo(n):
    return chr(n) if isinstance(n, int) else ("raíz" if n == T.raiz else "interno")


def tabla_esperada(nombre):
    """Filas esperadas (texto normalizado; None = columna libre)."""
    simb = {b: chr(b) for b in T.frecuencias}
    if nombre == "mensaje":
        return [[str(i), chr(b), str(b), f"{b:08b}"] for i, b in enumerate(T.datos)]
    if nombre == "frecuencias":
        return [[chr(b), str(b), str(f)] for b, f in T.frecuencias.items()]
    if nombre == "vueltas":
        return [[str(i), repr(v["ordenada"]), repr(v["izq"]), repr(v["der"]), str(v["minimo"]), repr(v["nuevo"])]
                for i, v in enumerate(T.vueltas, 1)]
    if nombre == "codigos":
        return [[simb[b], camino_texto(c), c, str(T.frecuencias[b]),
                 f"{T.frecuencias[b]} × {len(c)} = {T.frecuencias[b] * len(c)}"] for b, c in T.codigos.items()]
    if nombre == "recorrer":
        filas = []
        for i, r in enumerate(T.recorrer, 1):
            hoja = isinstance(r["nodo"], int)
            filas.append([str(i), str(r["prof"]), repr(r["nodo"]), f'"{r["codigo"]}"',
                          f"01 {r['nodo']:02X}" if hoja else "00 00",
                          f"{simb[r['nodo']]} = {r['codigo'] or '0'}" if hoja else "-"])
        return filas
    if nombre == "pkz":
        campos = ["NF"] + ["TREE"] * len(T.arbol) + ["BS"] + ["ZIP"] * len(T.zip)
        return [[str(i), f"{b:02X}", campos[i], None] for i, b in enumerate(T.pkz)]
    if nombre == "leer_arbol":
        return [[str(i), str(d["prof"]), str(d["posicion"]), f"{d['tipo']:02X} {d['valor']:02X}",
                 "hoja" if d["tipo"] == 1 else "interno", repr(d["devuelve"]), str(d["despues"])]
                for i, d in enumerate(T.lecturas, 1)]
    if nombre == "pasos":
        filas, cuenta = [], {}
        for i, p in enumerate(T.pasos, 1):
            cuenta[p["indice"]] = cuenta.get(p["indice"], 0) + 1
            llega = p["despues"]
            filas.append([str(i), f"{p['indice']} ({p['byte']:02X})", str(cuenta[p["indice"]]), p["bit"],
                          "izquierda" if p["bit"] == "0" else "derecha",
                          f"hoja {chr(llega)}" if isinstance(llega, int) else "interno",
                          chr(p["emite"]) if p["emite"] is not None else "-"])
        return filas
    if nombre == "bs":
        return [[str(n), None, str(comprimir_bytes(b"X" * n)[3])] for n in (1, 7, 8, 9, 16, 17)]
    raise ErrorGuia(f"Tabla desconocida: {nombre}")


def verificar_tabla(nombre, bloque, errores):
    if nombre == "errores":  # Ejecuta el descompresor real con cada caso de la tabla.
        for fila in bloque["filas"]:
            archivo, contenido, mensaje = norm(fila[0]), norm(fila[1]), norm(fila[-1])
            datos = b"" if contenido.startswith("(") else bytes.fromhex(contenido)
            real = descomprimir_bytes(datos, nombre=archivo)
            if isinstance(real, bytes) or norm(real) != mensaje:
                errores.append(f"Línea {bloque['linea']}: con {archivo} [{contenido}] el mensaje real es «{real}»")
        return
    esperado = tabla_esperada(nombre)
    filas = [[norm(c) for c in f] for f in bloque["filas"]]
    if len(filas) != len(esperado):
        errores.append(f"Línea {bloque['linea']}: la tabla '{nombre}' tiene {len(filas)} filas; "
                       f"la ejecución real da {len(esperado)}")
        return
    for k, (fila, esp) in enumerate(zip(filas, esperado), 1):
        for j, valor in enumerate(esp):
            if valor is not None and (j >= len(fila) or fila[j] != norm(valor)):
                errores.append(f"Línea {bloque['linea']}: tabla '{nombre}', fila {k}, columna {j + 1}: "
                               f"dice «{fila[j] if j < len(fila) else ''}» y la ejecución real da «{valor}»")


ESPACIO = {"T": T, "T2": T2, "hexa": hexa, "comprimir_bytes": comprimir_bytes,
           "descomprimir_bytes": descomprimir_bytes, "lc": lc, "ld": ld, "math": math, "Counter": Counter,
           "COMMIT": COMMIT, "NLINEAS": NLINEAS, "SHA": SHA, "leer_codigos": leer_codigos, "peso": peso,
           "CODIGO": CODIGO, "error_sin_linea": error_sin_linea, "recomprimir_demo": recomprimir_demo,
           "demo": lambda n: (PROYECTO / "Descomprimir estos archivos" / n).read_bytes()}


def verificar(meta, bloques):
    errores, terminal = [], Terminal()
    lista = list(todos(bloques))
    try:
        for k, b in enumerate(lista):
            if b["tipo"] == "comentario":
                texto = b["texto"]
                if texto.startswith("comprobar:"):
                    expr = texto[len("comprobar:"):].strip()
                    try:
                        if not eval(expr, dict(ESPACIO)):
                            errores.append(f"Línea {b['linea']}: no se cumple: {expr}")
                    except Exception as error:  # noqa: BLE001
                        errores.append(f"Línea {b['linea']}: error al evaluar {expr}: {error!r}")
                elif texto.startswith("tabla:"):
                    siguiente = next((x for x in lista[k + 1:] if x["tipo"] == "tabla"), None)
                    verificar_tabla(texto[len("tabla:"):].strip(), siguiente, errores)
            elif b["tipo"] == "codigo":
                info = b["info"]
                m = re.fullmatch(r"python\s+(\w+\.py):(\d+)-(\d+)", info)
                if m:
                    archivo, a, z = m.group(1), int(m.group(2)), int(m.group(3))
                    real = CODIGO[archivo][a - 1:z]
                    if b["lineas"] != real:
                        dif = next((i for i, (x, y) in enumerate(zip(b["lineas"], real)) if x != y),
                                   min(len(b["lineas"]), len(real)))
                        errores.append(f"Línea {b['linea']}: el fragmento {archivo}:{a}-{z} no coincide con el "
                                       f"código real (línea {a + dif} del archivo)")
                elif info == "python ejecutar":
                    salida = lista[k + 1] if k + 1 < len(lista) else None
                    if not salida or salida["tipo"] != "codigo" or salida["info"] != "salida":
                        errores.append(f"Línea {b['linea']}: falta el bloque ```salida``` después del ejemplo")
                        continue
                    try:
                        obtenida = ejecutar_fragmento("\n".join(b["lineas"])).rstrip("\n").split("\n")
                    except Exception as error:  # noqa: BLE001
                        errores.append(f"Línea {b['linea']}: el ejemplo falla al ejecutarse: {error!r}")
                        continue
                    if obtenida != salida["lineas"]:
                        errores.append(f"Línea {salida['linea']}: la salida real es {obtenida}")
                elif info == "terminal":
                    comando, esperado = None, []

                    def cerrar_comando():
                        if comando is not None:
                            real = terminal.ejecutar(comando)
                            if real != "\n".join(esperado):
                                errores.append(f"Línea {b['linea']}: «{comando}» muestra en realidad:\n{real}")
                    for l in b["lineas"]:
                        if l.startswith("> "):
                            cerrar_comando()
                            comando, esperado = l[2:], []
                        else:
                            esperado.append(l)
                    cerrar_comando()
                elif info.startswith("diagrama "):
                    if info.split()[1] not in DIAGRAMAS:
                        errores.append(f"Línea {b['linea']}: diagrama desconocido {info}")
        for clave, esperado in (("commit", COMMIT), ("comprimir", f"{NLINEAS['comprimir.py']} líneas"),
                                ("descomprimir", f"{NLINEAS['descomprimir.py']} líneas")):
            if meta.get(clave) != esperado:
                errores.append(f"Encabezado: '{clave}' dice «{meta.get(clave)}» y el valor real es «{esperado}»")
    finally:
        terminal.cerrar()
    return errores


# =====================================================================
# 5. Estilo: fuentes, colores y párrafos
# =====================================================================
from reportlab.lib.colors import HexColor, white  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether,  # noqa: E402
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

FUENTES = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
for nombre, archivo in (("Segoe", "segoeui.ttf"), ("Segoe-Bold", "segoeuib.ttf"), ("Segoe-Italic", "segoeuii.ttf"),
                        ("Segoe-BoldItalic", "segoeuiz.ttf"), ("Segoe-Semibold", "seguisb.ttf"),
                        ("Segoe-Light", "segoeuil.ttf"), ("Segoe-Black", "seguibl.ttf"),
                        ("Consolas", "consola.ttf"), ("Consolas-Bold", "consolab.ttf"),
                        ("Consolas-Italic", "consolai.ttf"), ("Consolas-BoldItalic", "consolaz.ttf")):
    pdfmetrics.registerFont(TTFont(nombre, str(FUENTES / archivo)))
registerFontFamily("Segoe", normal="Segoe", bold="Segoe-Bold", italic="Segoe-Italic", boldItalic="Segoe-BoldItalic")
registerFontFamily("Consolas", normal="Consolas", bold="Consolas-Bold", italic="Consolas-Italic",
                   boldItalic="Consolas-BoldItalic")

TINTA, TEXTO, GRIS = HexColor("#1f2a44"), HexColor("#27324a"), HexColor("#5b6678")
GRIS_CLARO, BORDE, FONDO = HexColor("#9aa4b3"), HexColor("#d8dee8"), HexColor("#f5f7fa")
TEAL, TEAL_CLARO, TEAL_VIVO = HexColor("#0f8b8d"), HexColor("#e5f3f3"), HexColor("#7fd6d4")
NARANJA, NARANJA_CLARO = HexColor("#d4652a"), HexColor("#fcefe5")
VIOLETA, VIOLETA_CLARO = HexColor("#6a4cb8"), HexColor("#efebf9")
VERDE, VERDE_CLARO = HexColor("#2c8650"), HexColor("#e8f4ec")
AMBAR, AMBAR_CLARO = HexColor("#b07613"), HexColor("#fcf3df")
TINTA_CLARO = HexColor("#edf0f6")


def hexcolor(c):
    return "#" + c.hexval()[2:]


ANCHO_PAG, ALTO_PAG = A4
MARGEN_I = MARGEN_D = 56
MARGEN_S, MARGEN_INF = 64, 58
ANCHO = ANCHO_PAG - MARGEN_I - MARGEN_D

CUERPO = ParagraphStyle("cuerpo", fontName="Segoe", fontSize=10.2, leading=15.4, textColor=TEXTO, spaceAfter=6.5)
H2 = ParagraphStyle("h2", fontName="Segoe-Semibold", fontSize=15, leading=19.5, textColor=TINTA,
                    spaceBefore=15, spaceAfter=7, keepWithNext=1)
H3 = ParagraphStyle("h3", fontName="Segoe-Semibold", fontSize=11.3, leading=15, textColor=TEAL,
                    spaceBefore=9, spaceAfter=4, keepWithNext=1)
LISTA = ParagraphStyle("lista", parent=CUERPO, leftIndent=17, bulletIndent=5, spaceAfter=3.2,
                       bulletFontName="Segoe-Bold", bulletColor=TEAL)
PREGUNTA = ParagraphStyle("pregunta", parent=CUERPO, fontName="Segoe-Semibold", textColor=TINTA,
                          spaceBefore=7, spaceAfter=2.5, keepWithNext=1)
TD = ParagraphStyle("td", fontName="Segoe", fontSize=8.9, leading=12.2, textColor=TEXTO)
TH = ParagraphStyle("th", fontName="Segoe-Semibold", fontSize=8.9, leading=12.2, textColor=white)
EN_AVISO = ParagraphStyle("aviso", parent=CUERPO, fontSize=9.8, leading=14.6, spaceAfter=4.5)
LISTA_AVISO = ParagraphStyle("lista_aviso", parent=EN_AVISO, leftIndent=15, bulletIndent=4, spaceAfter=2.5,
                             bulletFontName="Segoe-Bold", bulletColor=TEAL)
TOC0 = ParagraphStyle("toc0", fontName="Segoe-Semibold", fontSize=10.8, leading=15, textColor=TINTA,
                      spaceBefore=6.5)
TOC1 = ParagraphStyle("toc1", fontName="Segoe", fontSize=9.3, leading=12.6, textColor=TEXTO, leftIndent=20)

PASOS = {"Concepto": TEAL, "En palabras sencillas": AMBAR, "Código real": TINTA, "Ejecución con": NARANJA,
         "Resultado": VERDE, "Conclusión": VIOLETA}  # Un ### que empieza así se muestra como etiqueta.
AVISOS = {"IDEA": ("IDEA", TEAL, TEAL_CLARO), "CLAVE": ("PUNTO CLAVE", TINTA, TINTA_CLARO),
          "ATENCION": ("ATENCIÓN", NARANJA, NARANJA_CLARO), "EJERCICIO": ("EJERCICIO", VIOLETA, VIOLETA_CLARO),
          "SOLUCION": ("SOLUCIÓN", VERDE, VERDE_CLARO), "PREGUNTA": ("PREGUNTA DE EXPOSICIÓN", AMBAR, AMBAR_CLARO),
          "NOTA": ("NOTA", GRIS, FONDO), "RESUMEN": ("RESUMEN", TINTA, TINTA_CLARO)}


def inline(texto, tam_codigo=9.1, color_codigo="#a63d17"):
    """Convierte **negrita**, *cursiva* y `código` en el marcado de ReportLab."""
    codigos = []

    def guardar(m):
        codigos.append(m.group(1))
        return f"\x00{len(codigos) - 1}\x00"

    t = re.sub(r"`([^`]+)`", guardar, texto)
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub(r"\x00(\d+)\x00", lambda m: f'<font name="Consolas" size="{tam_codigo}" color="{color_codigo}">'
                  f'{html.escape(codigos[int(m.group(1))], quote=False)}</font>', t)


# =====================================================================
# 6. Piezas gráficas
# =====================================================================
class Apertura(Flowable):
    """Banda de inicio de capítulo."""

    def __init__(self, numero, etiqueta, titulo, clave, texto_toc=None):
        super().__init__()
        self.numero, self.etiqueta, self.titulo = numero, etiqueta, titulo
        texto_toc = texto_toc or (f"{numero}. {titulo}" if numero else titulo)
        self._toc = (0, texto_toc, clave)
        self._capitulo = f"Capítulo {numero} · {titulo}" if numero else texto_toc

    def wrap(self, aw, ah):
        self.ancho = aw
        self.x_texto = 112 if self.numero else 30
        estilo = ParagraphStyle("apertura", fontName="Segoe-Semibold", fontSize=23, leading=28, textColor=white)
        self.p = Paragraph(inline(self.titulo, 21, "#7fd6d4"), estilo)
        _, h = self.p.wrap(aw - self.x_texto - 26, ah)
        self.alto = max(108, h + 62)
        return aw, self.alto + 20

    def draw(self):
        c = self.canv
        y0 = 20
        c.setFillColor(TINTA)
        c.roundRect(0, y0, self.ancho, self.alto, 10, stroke=0, fill=1)
        c.setFont("Consolas-Bold", 8)
        c.setFillColor(HexColor("#33456b"))
        c.drawRightString(self.ancho - 18, y0 + 14, "02 00 00 00 00 01 43 01 42 01 41 03 FA 80")
        if self.numero:
            c.setFillColor(TEAL_VIVO)
            c.setFont("Segoe-Black", 62)
            c.drawCentredString(56, y0 + self.alto / 2 - 22, self.numero)
            c.setStrokeColor(HexColor("#3a4a70"))
            c.setLineWidth(1)
            c.line(98, y0 + 18, 98, y0 + self.alto - 18)
        c.setFillColor(TEAL_VIVO)
        c.setFont("Segoe-Bold", 8.6)
        c.drawString(self.x_texto, y0 + self.alto - 30, self.etiqueta, charSpace=1.6)
        self.p.drawOn(c, self.x_texto, y0 + 26)


class Paso(Flowable):
    """Etiqueta de color para cada paso de aprendizaje."""

    def __init__(self, nombre):
        super().__init__()
        base = next(p for p in PASOS if nombre.startswith(p))
        self.texto, self.color = nombre.upper(), PASOS[base]
        self.keepWithNext = 1
        self.spaceBefore, self.spaceAfter = 7, 3

    def wrap(self, aw, ah):
        self.w = stringWidth(self.texto, "Segoe-Bold", 7.4) * 1 + len(self.texto) * 0.9 + 22
        return aw, 18

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 1, self.w, 15, 7.5, stroke=0, fill=1)
        c.setFillColor(white)
        c.circle(9, 8.5, 2.2, stroke=0, fill=1)
        c.setFont("Segoe-Bold", 7.4)
        c.drawString(16, 5.4, self.texto, charSpace=0.9)


TOKENS = re.compile(r'(?P<cadena>\b[fbr]?("""|"|\')(?:\\.|(?!\2).)*\2)|(?P<comentario>#.*$)|'
                    r'(?P<palabra>[A-Za-z_][A-Za-z_0-9]*)|(?P<numero>\d+)|(?P<otro>[^\w"\'#]+|.)')
PALABRAS = {"def", "if", "else", "elif", "while", "for", "in", "return", "import", "from", "try", "except", "as",
            "with", "not", "and", "or", "is", "nonlocal", "raise", "None", "True", "False", "print"}
INTERNAS = {"len", "isinstance", "min", "bytes", "bytearray", "int", "any", "set", "enumerate", "Counter",
            "Path", "ValueError", "OSError", "FileExistsError", "sys", "list", "str", "range", "dict", "tuple"}


def colorear(linea_codigo):
    """Divide una línea de Python en (texto, fuente, color) para dibujarla con colores."""
    piezas = []
    for m in TOKENS.finditer(linea_codigo):
        texto = m.group(0)
        if m.group("cadena"):
            piezas.append((texto, "Consolas", HexColor("#2b7a3d")))
        elif m.group("comentario"):
            piezas.append((texto, "Consolas-Italic", HexColor("#7b8597")))
        elif m.group("palabra"):
            if texto in PALABRAS:
                piezas.append((texto, "Consolas-Bold", HexColor("#7a2f99")))
            elif texto in INTERNAS:
                piezas.append((texto, "Consolas", TEAL))
            else:
                piezas.append((texto, "Consolas", TINTA))
        elif m.group("numero"):
            piezas.append((texto, "Consolas", HexColor("#c2501a")))
        else:
            piezas.append((texto, "Consolas", TINTA))
    return piezas


class Listado(Flowable):
    """Bloque de código con números de línea y colores; se puede partir entre páginas."""

    TAM, PASO, CAB = 8.45, 12.1, 18

    def __init__(self, lineas, inicio=1, etiqueta="", numerar=True, derecha="Python"):
        super().__init__()
        self.lineas, self.inicio, self.etiqueta = lineas, inicio, etiqueta
        self.numerar, self.derecha = numerar, derecha
        self.spaceBefore, self.spaceAfter = 3, 9

    def wrap(self, aw, ah):
        self.ancho = aw
        self.alto = self.CAB + 7 + len(self.lineas) * self.PASO + 3
        return aw, self.alto

    def split(self, aw, ah):
        cabe = int((ah - self.CAB - 10) // self.PASO)
        if cabe < 4 or cabe >= len(self.lineas) or len(self.lineas) - cabe < 3:
            return []
        resto = Listado(self.lineas[cabe:], self.inicio + cabe, self.etiqueta + " (continuación)", self.numerar,
                        self.derecha)
        return [Listado(self.lineas[:cabe], self.inicio, self.etiqueta, self.numerar, self.derecha), resto]

    def draw(self):
        c, w, h = self.canv, self.ancho, self.alto
        c.setFillColor(HexColor("#fbfcfe"))
        c.setStrokeColor(BORDE)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, w, h, 5, stroke=1, fill=1)
        c.setFillColor(TINTA_CLARO)
        c.roundRect(0, h - self.CAB, w, self.CAB, 5, stroke=0, fill=1)
        c.rect(0, h - self.CAB, w, 5, stroke=0, fill=1)
        c.setFillColor(TINTA)
        c.setFont("Consolas-Bold", 8.3)
        c.drawString(10, h - 12.4, self.etiqueta)
        c.setFillColor(GRIS)
        c.setFont("Segoe", 7.6)
        c.drawRightString(w - 10, h - 12.4, self.derecha)
        gutter = 30 if self.numerar else 0
        if self.numerar:
            c.setStrokeColor(BORDE)
            c.line(gutter, 4, gutter, h - self.CAB - 3)
        ancho_letra = stringWidth("M", "Consolas", self.TAM)
        y = h - self.CAB - 4 - self.TAM
        for k, texto in enumerate(self.lineas):
            if self.numerar:
                c.setFillColor(GRIS_CLARO)
                c.setFont("Consolas", 7.4)
                c.drawRightString(gutter - 6, y, str(self.inicio + k))
            # Una sola línea de texto PDF con cambios de color: así se puede copiar y buscar.
            linea_pdf = c.beginText(gutter + 9, y)
            for pieza, fuente, color in colorear(texto):
                linea_pdf.setFont(fuente, self.TAM)
                linea_pdf.setFillColor(color)
                linea_pdf.textOut(pieza)
            c.drawText(linea_pdf)
            y -= self.PASO


class CajaTexto(Flowable):
    """Caja monoespaciada: cálculos, texto plano o salida de un ejemplo."""

    def __init__(self, lineas, estilo="texto", titulo=None):
        super().__init__()
        self.lineas, self.estilo, self.titulo = lineas, estilo, titulo
        self.spaceBefore, self.spaceAfter = 2, 9

    def wrap(self, aw, ah):
        self.ancho = aw
        mayor = max([stringWidth(l.lstrip("!"), "Consolas", 1) for l in self.lineas] or [1])
        self.tam = min(9.2 if self.estilo == "calculo" else 8.8, (aw - 30) / max(mayor, 1))
        self.paso = self.tam * (1.52 if self.estilo == "calculo" else 1.42)
        self.cab = 16 if self.titulo else 0
        self.alto = self.cab + 9 + len(self.lineas) * self.paso + 4
        return aw, self.alto

    def draw(self):
        c, w, h = self.canv, self.ancho, self.alto
        if self.estilo == "calculo":
            fondo, borde, acento = white, BORDE, TEAL
        elif self.estilo == "salida":
            fondo, borde, acento = HexColor("#f2f6f2"), HexColor("#cfe0d3"), VERDE
        else:
            fondo, borde, acento = FONDO, BORDE, GRIS_CLARO
        c.setFillColor(fondo)
        c.setStrokeColor(borde)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, w, h, 5, stroke=1, fill=1)
        c.setFillColor(acento)
        c.roundRect(0, 0, 3.2, h, 1.6, stroke=0, fill=1)
        if self.titulo:
            c.setFont("Segoe-Bold", 7.6)
            c.drawString(13, h - 12, self.titulo.upper(), charSpace=0.8)
        y = h - self.cab - 7 - self.tam * 0.8
        for l in self.lineas:
            resaltar = l.startswith("!")
            c.setFillColor(TEAL if resaltar and self.estilo == "calculo" else TINTA)
            c.setFont("Consolas-Bold" if resaltar else "Consolas", self.tam)
            c.drawString(13, y, l[1:] if resaltar else l)
            y -= self.paso


class TerminalCaja(Flowable):
    """Ventana de terminal con los comandos reales y su salida."""

    PASO, TAM = 12.6, 8.5

    def __init__(self, lineas):
        super().__init__()
        self.lineas = lineas
        self.spaceBefore, self.spaceAfter = 3, 10

    def wrap(self, aw, ah):
        self.ancho = aw
        self.alto = 20 + 9 + len(self.lineas) * self.PASO + 3
        return aw, self.alto

    def draw(self):
        c, w, h = self.canv, self.ancho, self.alto
        c.setFillColor(HexColor("#1c2333"))
        c.roundRect(0, 0, w, h, 6, stroke=0, fill=1)
        c.setFillColor(HexColor("#2a3346"))
        c.roundRect(0, h - 20, w, 20, 6, stroke=0, fill=1)
        c.rect(0, h - 20, w, 6, stroke=0, fill=1)
        for k, color in enumerate(("#ff6b5f", "#f6c343", "#3fc56b")):
            c.setFillColor(HexColor(color))
            c.circle(13 + k * 11, h - 10, 3.1, stroke=0, fill=1)
        c.setFillColor(HexColor("#aab6c8"))
        c.setFont("Segoe", 7.8)
        c.drawCentredString(w / 2, h - 13.2, "Terminal (CMD) · salida real de los programas")
        y = h - 20 - 7 - self.TAM
        for l in self.lineas:
            if l.startswith("> "):
                linea_pdf = c.beginText(12, y)
                linea_pdf.setFont("Consolas-Bold", self.TAM)
                linea_pdf.setFillColor(HexColor("#5fd3c6"))
                linea_pdf.textOut("> ")
                linea_pdf.setFillColor(HexColor("#f1f5fb"))
                linea_pdf.textOut(l[2:])
                c.drawText(linea_pdf)
            else:
                error = l.startswith(("No se pudo", "Uso:"))
                c.setFillColor(HexColor("#f6ad6b") if error else HexColor("#c8d2df"))
                c.setFont("Consolas", self.TAM)
                c.drawString(12, y, l)
            y -= self.PASO


# ----- Diagramas -----
def caja(c, x, y, w, h, relleno, borde=None, radio=5, grosor=1):
    c.setFillColor(relleno)
    if borde is not None:
        c.setStrokeColor(borde)
        c.setLineWidth(grosor)
    c.roundRect(x, y, w, h, radio, stroke=1 if borde is not None else 0, fill=1)


def disponer(arboles, ancho, x0):
    """Posición de cada nodo de un bosque: {(k, camino): (x, profundidad, nodo)}."""
    hojas = []

    def recoger(k, n, cam):
        if isinstance(n, tuple):
            recoger(k, n[0], cam + "0")
            recoger(k, n[1], cam + "1")
        else:
            hojas.append((k, cam))

    for k, a in enumerate(arboles):
        recoger(k, a, "")
    paso = ancho / max(len(hojas), 1)
    pos = {}

    def ubicar(k, n, cam, prof):
        if isinstance(n, tuple):
            x = (ubicar(k, n[0], cam + "0", prof + 1) + ubicar(k, n[1], cam + "1", prof + 1)) / 2
        else:
            x = x0 + paso * (hojas.index((k, cam)) + 0.5)
        pos[(k, cam)] = (x, prof, n)
        return x

    for k, a in enumerate(arboles):
        ubicar(k, a, "", 0)
    return pos


class DiagramaArboles(Flowable):
    """Uno o varios paneles con árboles; cada panel puede ser un bosque."""

    def __init__(self, paneles, nodo=(54, 23), nivel=48, tam=9, alto_extra=0):
        super().__init__()
        self.paneles, self.nodo, self.nivel, self.tam, self.extra = paneles, nodo, nivel, tam, alto_extra
        self.spaceBefore, self.spaceAfter = 4, 10

    def wrap(self, aw, ah):
        self.ancho = aw
        prof = 0
        for p in self.paneles:
            pos = disponer(p["arboles"], 100, 0)
            prof = max(prof, max(v[1] for v in pos.values()))
        hay_notas = any(p.get("nota") for p in self.paneles)
        hay_pie = any(p.get("pie") for p in self.paneles)
        alto_nodo = max(p.get("nodo", self.nodo)[1] for p in self.paneles)
        self.alto = 6 + prof * self.nivel + alto_nodo + (16 if hay_notas else 0) + (26 if hay_pie else 4) + self.extra
        return aw, self.alto

    def draw(self):
        c = self.canv
        total = sum(p.get("ancho", 1) for p in self.paneles)
        x0 = 0
        for p in self.paneles:
            w = self.ancho * p.get("ancho", 1) / total
            nw, nh = p.get("nodo", self.nodo)
            pos = disponer(p["arboles"], w, x0)
            arriba = self.alto - 6
            resaltar = p.get("resaltar", set())
            if p.get("fondo"):
                caja(c, x0 + 4, 0, w - 8, self.alto, p["fondo"], None, 7)
            for (k, cam), (x, prof, n) in pos.items():
                if not isinstance(n, tuple):
                    continue
                for bit in "01":
                    hx, hp, _ = pos[(k, cam + bit)]
                    y1, y2 = arriba - prof * self.nivel - nh, arriba - hp * self.nivel
                    activo = (k, cam + bit) in resaltar
                    c.setStrokeColor(NARANJA if activo else HexColor("#7d889a"))
                    c.setLineWidth(2.6 if activo else 1.1)
                    c.line(x, y1, hx, y2)
                    mx, my = (x + hx) / 2, (y1 + y2) / 2
                    c.setFillColor(NARANJA if activo else TEAL)
                    c.setFont("Segoe-Bold", 9.5)
                    if bit == "0":
                        c.drawRightString(mx - 5, my + 1, "0")
                    else:
                        c.drawString(mx + 5, my + 1, "1")
            for (k, cam), (x, prof, n) in pos.items():
                y = arriba - prof * self.nivel - nh
                estilo = p["estilo"](k, cam, n) if p.get("estilo") else ("interno" if isinstance(n, tuple) else "hoja")
                relleno, borde, color = {
                    "interno": (TINTA, TINTA, white), "hoja": (TEAL_CLARO, TEAL, TINTA),
                    "nuevo": (NARANJA, NARANJA, white), "hoja_nueva": (NARANJA_CLARO, NARANJA, TINTA),
                    "llamada": (white, TINTA, TINTA), "llamada_hoja": (TEAL_CLARO, TEAL, TINTA),
                    "activo": (NARANJA_CLARO, NARANJA, TINTA), "punto": (TINTA, TINTA, white)}[estilo]
                caja(c, x - nw / 2, y, nw, nh, relleno, borde, 6 if nh < 30 else 7, 1.1)
                texto = p["texto"](k, cam, n)
                lineas = texto if isinstance(texto, list) else [texto]
                tam = p.get("tam", self.tam)
                alto_txt = len(lineas) * tam * 1.25
                ty = y + nh / 2 + alto_txt / 2 - tam * 0.95
                for i, t in enumerate(lineas):
                    negrita = i == 0
                    c.setFillColor(color)
                    c.setFont("Segoe-Bold" if negrita else "Segoe", tam)
                    c.drawCentredString(x, ty - i * tam * 1.25, t)
                if p.get("insignia") and p["insignia"](k, cam, n):
                    c.setFillColor(NARANJA)
                    c.circle(x - nw / 2 + 1, y + nh - 1, 7.5, stroke=0, fill=1)
                    c.setFillColor(white)
                    c.setFont("Segoe-Bold", 8)
                    c.drawCentredString(x - nw / 2 + 1, y + nh - 3.8, p["insignia"](k, cam, n))
                if p.get("nota"):
                    nota = p["nota"](k, cam, n)
                    if nota:
                        c.setFillColor(GRIS)
                        c.setFont("Consolas", 7.9)
                        if isinstance(n, tuple):  # Al costado: debajo pasan las aristas.
                            c.drawString(x + nw / 2 + 6, y + nh / 2 - 3, nota)
                        else:
                            c.drawCentredString(x, y - 11, nota)
            if p.get("pie"):
                c.setFillColor(TEXTO)
                c.setFont("Segoe-Semibold", 8.6)
                c.drawCentredString(x0 + w / 2, 7, p["pie"])
            x0 += w


class Celdas(Flowable):
    """Fila de celdas con etiquetas arriba y abajo (bytes, bits o campos)."""

    def __init__(self, celdas, alto_celda=26, grupos=(), filas_abajo=(), tam=10, fuente="Consolas-Bold",
                 llaves=(), arriba=()):
        super().__init__()
        self.celdas, self.alto_celda, self.grupos, self.filas_abajo = celdas, alto_celda, grupos, filas_abajo
        self.tam, self.fuente, self.llaves, self.arriba = tam, fuente, llaves, arriba
        self.spaceBefore, self.spaceAfter = 4, 10

    def wrap(self, aw, ah):
        self.ancho = aw
        self.alto = (18 if self.grupos or self.arriba else 4) + self.alto_celda + 13 * len(self.filas_abajo) + \
            (30 if self.llaves else 4)
        return aw, self.alto

    def draw(self):
        c = self.canv
        n = len(self.celdas)
        w = self.ancho / n
        yc = self.alto - (18 if self.grupos or self.arriba else 4) - self.alto_celda
        for i, (texto, relleno, borde, color) in enumerate(self.celdas):
            caja(c, i * w + 1.2, yc, w - 2.4, self.alto_celda, relleno, borde, 3.5, 0.9)
            c.setFillColor(color)
            c.setFont(self.fuente, self.tam)
            c.drawCentredString(i * w + w / 2, yc + self.alto_celda / 2 - self.tam * 0.35, texto)
        for a, z, texto, color in self.grupos:  # Etiquetas de grupo arriba
            x1, x2 = a * w + 2, (z + 1) * w - 2
            c.setStrokeColor(color)
            c.setLineWidth(1.4)
            c.line(x1, yc + self.alto_celda + 4, x2, yc + self.alto_celda + 4)
            c.setFillColor(color)
            c.setFont("Segoe-Bold", 8.2)
            c.drawCentredString((x1 + x2) / 2, yc + self.alto_celda + 8, texto)
        for i, texto in self.arriba:
            c.setFillColor(GRIS)
            c.setFont("Segoe-Semibold", 8)
            c.drawCentredString(i * w + w / 2, yc + self.alto_celda + 7, texto)
        for f, fila in enumerate(self.filas_abajo):
            c.setFont("Consolas" if f else "Segoe", 7.8)
            c.setFillColor(GRIS)
            for i, texto in enumerate(fila):
                c.drawCentredString(i * w + w / 2, yc - 11 - f * 13, texto)
        for a, z, texto, color in self.llaves:  # Llaves abajo
            x1, x2 = a * w + 3, (z + 1) * w - 3
            y = yc - 13 * len(self.filas_abajo) - 6
            c.setStrokeColor(color)
            c.setLineWidth(1.2)
            c.line(x1, y, x2, y)
            c.line(x1, y, x1, y + 4)
            c.line(x2, y, x2, y + 4)
            c.setFillColor(color)
            c.setFont("Segoe-Semibold", 8.2)
            c.drawCentredString((x1 + x2) / 2, y - 11, texto)


class Flujo(Flowable):
    """Cadena de etapas de un programa con flechas."""

    def __init__(self, etapas):
        super().__init__()
        self.etapas = etapas  # (titulo, lineas, resultado)
        self.spaceBefore, self.spaceAfter = 4, 10

    def wrap(self, aw, ah):
        self.ancho, self.alto = aw, 112
        return aw, self.alto

    def draw(self):
        c, n = self.canv, len(self.etapas)
        flecha = 14
        w = (self.ancho - flecha * (n - 1)) / n
        for i, (titulo, lineas, resultado) in enumerate(self.etapas):
            x = i * (w + flecha)
            caja(c, x, 40, w, 66, TINTA, None, 7)
            c.setFillColor(TEAL_VIVO)
            c.setFont("Segoe-Bold", 7.6)
            c.drawString(x + 8, 92, f"ETAPA {i + 1}", charSpace=0.8)
            c.setFillColor(white)
            c.setFont("Segoe-Semibold", 9)
            for k, parte in enumerate(titulo.split("\n")):
                c.drawString(x + 8, 78 - k * 11.5, parte)
            c.setFillColor(HexColor("#b9c4d6"))
            c.setFont("Segoe", 7.6)
            c.drawString(x + 8, 47, lineas)
            caja(c, x, 2, w, 32, TEAL_CLARO, TEAL, 6, 0.8)
            c.setFillColor(TINTA)
            for k, parte in enumerate(resultado.split("\n")):
                c.setFont("Consolas", 7.6)
                c.drawCentredString(x + w / 2, 21 - k * 10, parte)
            if i < n - 1:
                c.setStrokeColor(NARANJA)
                c.setFillColor(NARANJA)
                c.setLineWidth(1.6)
                c.line(x + w + 2, 73, x + w + flecha - 4, 73)
                p = c.beginPath()
                p.moveTo(x + w + flecha - 2, 73)
                p.lineTo(x + w + flecha - 7, 76.5)
                p.lineTo(x + w + flecha - 7, 69.5)
                p.close()
                c.drawPath(p, stroke=0, fill=1)


# ----- Constructores de diagramas a partir de la traza -----
def d_mensaje():
    celdas = [(chr(b), TEAL_CLARO, TEAL, TINTA) for b in T.datos]
    return Celdas(celdas, 30, filas_abajo=[[str(b) for b in T.datos], [f"{b:08b}" for b in T.datos]], tam=13,
                  fuente="Segoe-Bold", arriba=[(i, f"posición {i}") for i in range(len(T.datos))])


def d_arbol_codigos():
    return DiagramaArboles([{
        "arboles": [T.raiz],
        "texto": lambda k, cam, n: str(peso(n, T.frecuencias)) if isinstance(n, tuple)
        else f"{chr(n)} · {T.frecuencias[n]}",
        "nota": lambda k, cam, n: None if isinstance(n, tuple) else f"código {cam}"}],
        nodo=(62, 25), nivel=56)


def d_construccion():
    def etiqueta(k, cam, n):
        return str(peso(n, T.frecuencias)) if isinstance(n, tuple) else f"{chr(n)} · {T.frecuencias[n]}"

    paneles = [{"arboles": [x[2] for x in T.vueltas[0]["ordenada"]], "texto": etiqueta,
                "pie": "Inicio: hojas ordenadas por sort()", "fondo": FONDO}]
    for i, v in enumerate(T.vueltas, 1):
        nuevos = [x[2] for x in sorted(v["despues"])]
        nuevo = v["nuevo"][2]
        a, b = v["izq"], v["der"]

        def nombre(t):
            return chr(t[2]) if isinstance(t[2], int) else str(t[0])

        def estilo(k, cam, n, nuevo=nuevo):
            if cam == "" and n == nuevo:
                return "nuevo"
            return "interno" if isinstance(n, tuple) else "hoja"

        paneles.append({"arboles": nuevos, "texto": etiqueta, "fondo": FONDO, "estilo": estilo,
                        "pie": f"Vuelta {i}: {nombre(a)} + {nombre(b)} = {v['nuevo'][0]}"})
    return DiagramaArboles(paneles, nodo=(46, 22), nivel=44, tam=8.6)


def d_bits_zip():
    colores = {}
    paleta = [(TEAL_CLARO, TEAL), (NARANJA_CLARO, NARANJA), (VIOLETA_CLARO, VIOLETA)]
    for k, b in enumerate(T.frecuencias):
        colores[b] = paleta[k % 3]
    celdas, grupos, i = [], [], 0
    for b in T.datos:
        cod = T.codigos[b]
        fondo, borde = colores[b]
        for bit in cod:
            celdas.append((bit, fondo, borde, TINTA))
        grupos.append((i, i + len(cod) - 1, chr(b), borde))
        i += len(cod)
    for bit in T.bits_relleno[len(T.bits_datos):]:
        celdas.append((bit, HexColor("#e9ecf1"), GRIS_CLARO, GRIS))
    n = len(T.bits_relleno)
    llaves = [(0, 7, f"byte 1 = {T.bits_relleno[:8]} = {T.zip[0]:02X}", TINTA),
              (8, n - 1, f"byte 2 = {T.bits_relleno[8:16]} = {T.zip[1]:02X}", TINTA)]
    fila = [str(k) for k in range(1, n + 1)]
    return Celdas(celdas, 24, grupos=grupos, filas_abajo=[fila], tam=11, llaves=llaves)


def d_formato():
    celdas = []
    colores = {"NF": (VIOLETA_CLARO, VIOLETA), "TREE": (TEAL_CLARO, TEAL), "BS": (NARANJA_CLARO, NARANJA),
               "ZIP": (VERDE_CLARO, VERDE)}
    campos = ["NF"] + ["TREE"] * len(T.arbol) + ["BS"] + ["ZIP"] * len(T.zip)
    for b, campo in zip(T.pkz, campos):
        fondo, borde = colores[campo]
        celdas.append((f"{b:02X}", fondo, borde, TINTA))
    fin = 1 + len(T.arbol)
    grupos = [(0, 0, "NF", VIOLETA), (1, fin - 1, "TREE (preorden, 2 bytes por nodo)", TEAL),
              (fin, fin, "BS", NARANJA), (fin + 1, len(T.pkz) - 1, "ZIP", VERDE)]
    significado = [""] * len(T.pkz)
    for k, r in enumerate(T.recorrer):
        significado[1 + 2 * k] = nombre_nodo(r["nodo"])
    indices = [str(i) for i in range(len(T.pkz))]
    llaves = [(1 + 2 * k, 2 + 2 * k, nombre_nodo(r["nodo"]), TEAL) for k, r in enumerate(T.recorrer)]
    return Celdas(celdas, 28, grupos=grupos, filas_abajo=[indices], tam=10.5, llaves=llaves)


def d_preorden():
    orden = {r["codigo"]: k for k, r in enumerate(T.recorrer, 1)}
    escribe = {r["codigo"]: f"01 {r['nodo']:02X}" if isinstance(r["nodo"], int) else "00 00"
               for r in T.recorrer}
    return DiagramaArboles([{
        "arboles": [T.raiz],
        "texto": lambda k, cam, n: "interno" if isinstance(n, tuple) else f"hoja {chr(n)}",
        "insignia": lambda k, cam, n: str(orden[cam]),
        "nota": lambda k, cam, n: f"TREE: {escribe[cam]}"}], nodo=(66, 24), nivel=58)


def d_recorrer():
    datos = {r["codigo"]: (k, r) for k, r in enumerate(T.recorrer, 1)}

    def texto(k, cam, n):
        i, r = datos[cam]
        hoja = isinstance(n, int)
        return [f"llamada {i}", f'codigo = "{r["codigo"]}"',
                f"TREE += 01 {n:02X}" if hoja else "TREE += 00 00",
                f"codigos[{n}] = \"{cam or '0'}\"" if hoja else "baja a izquierda y derecha"]

    return DiagramaArboles([{"arboles": [T.raiz], "texto": texto,
                             "estilo": lambda k, cam, n: "llamada_hoja" if isinstance(n, int) else "llamada"}],
                           nodo=(124, 54), nivel=74, tam=7.8)


def d_leer_arbol():
    por_camino = {}
    for i, d in enumerate(T.lecturas, 1):
        por_camino[camino_de(T.raiz_d, d["devuelve"])] = (i, d)

    def texto(k, cam, n):
        i, d = por_camino[cam]
        return [f"llamada {i}", f"posicion = {d['posicion']}", f"lee {d['tipo']:02X} {d['valor']:02X}",
                f"devuelve {d['devuelve']!r}"]

    return DiagramaArboles([{"arboles": [T.raiz_d], "texto": texto,
                             "estilo": lambda k, cam, n: "llamada_hoja" if isinstance(n, int) else "llamada"}],
                           nodo=(128, 54), nivel=74, tam=7.8)


def d_reconstruccion():
    hoja = {67: "C (67)", 66: "B (66)", 65: "A (65)"}

    def texto(k, cam, n):
        return hoja[n] if isinstance(n, int) else repr(n) if n != T.raiz_d else "raíz"

    izq = T.raiz_d[0]
    return DiagramaArboles([
        {"arboles": list(izq), "texto": texto, "fondo": FONDO, "pie": "Llamadas 3 y 4: devuelven 67 y 66",
         "estilo": lambda k, cam, n: "hoja_nueva", "ancho": 0.85},
        {"arboles": [izq], "texto": texto, "fondo": FONDO, "pie": "Llamada 2: arma (67, 66)",
         "estilo": lambda k, cam, n: "nuevo" if cam == "" else "hoja", "ancho": 0.95},
        {"arboles": [T.raiz_d], "texto": texto, "fondo": FONDO, "pie": "Llamadas 5 y 1: la raíz completa",
         "estilo": lambda k, cam, n: "nuevo" if cam == "" else ("hoja_nueva" if cam == "1" else
                                                                ("interno" if isinstance(n, tuple) else "hoja")),
         "ancho": 1.4},
    ], nodo=(56, 24), nivel=46, tam=8.2)


def d_recorrido_bits():
    grupos = []
    for cod in leer_codigos(T):
        clave = (cod["bits"], tuple(sorted(set(cod["bytes"]))))
        if grupos and grupos[-1]["clave"] == clave:
            grupos[-1]["veces"] += 1
        else:
            grupos.append({"clave": clave, "veces": 1, "simbolo": cod["simbolo"]})
    paneles = []
    for g in grupos:
        bits, origen = g["clave"]
        resaltar = {(0, bits[:i + 1]) for i in range(len(bits))}
        cruza = len(origen) > 1
        bits_txt = " | ".join(bits) if cruza else " ".join(bits)
        veces = f" (×{g['veces']})" if g["veces"] > 1 else ""
        paneles.append({"arboles": [T.raiz_d], "resaltar": resaltar, "fondo": FONDO,
                        "texto": lambda k, cam, n: "" if isinstance(n, tuple) else chr(n),
                        "estilo": lambda k, cam, n, b=bits: ("activo" if cam == b else "hoja")
                        if isinstance(n, int) else "punto",
                        "pie": f"{bits_txt} → {g['simbolo']}{veces}" + ("  (cruza bytes)" if cruza else "")})
    return DiagramaArboles(paneles, nodo=(30, 19), nivel=36, tam=9)


def d_flujo_comprimir():
    r = lambda a, b: f"líneas {lc(a)}-{lc(b)}"
    frec = "  ".join(f"{chr(b)}·{f}" for b, f in T.frecuencias.items())
    codigos = " ".join(f"{chr(b)}={c}" for b, c in T.codigos.items())
    return Flujo([
        ("Leer y\ncontar", r("ruta = Path(archivo)", "frecuencias = Counter(datos)"), frec),
        ("Construir\nel árbol", r("# 1. Construir", "nodos.append((peso_izq"), repr(T.raiz)),
        ("Códigos\ny TREE", r("# 2. Crear códigos", "recorrer(nodos[0][2])"), codigos),
        ("Bits, BS\ny ZIP", r("# 3. Empaquetar", "zip_bytes = int(bits, 2)"), f"BS={T.bs}\nZIP={hexa(T.zip)}"),
        ("Guardar\nel .pkz", r("# 4. Guardar", "return destino"), f"{len(T.pkz)} bytes"),
    ])


def d_flujo_descomprimir():
    r = lambda a, b: f"líneas {ld(a)}-{ld(b)}"
    return Flujo([
        ("Leer y\nrevisar", r("ruta = Path(archivo)", 'raise ValueError("Faltan datos'),
         f"NF={T.d_nf}\nfin_arbol={T.fin_arbol}"),
        ("Reconstruir\nel árbol", r("# 2. Leer TREE", 'raise ValueError("TREE no coincide'), repr(T.raiz_d)),
        ("BS y\nrelleno", r("# 3. Leer los bits", 'raise ValueError("Los bits de relleno'),
         f"BS={T.d_bs}\nrelleno={f'{T.d_zip[-1]:08b}'[T.d_bs:]}"),
        ("Decodificar\nlos bits", r("# 4. Decodificar", 'raise ValueError("ZIP termina'), T.recuperado.decode()),
        ("Guardar\nsin pisar", r("# 5. Guardar", "return destino"), "recuperados\\\n" + "aaaaabbc.txt"),
    ])


DIAGRAMAS = {"mensaje": d_mensaje, "arbol-codigos": d_arbol_codigos, "construccion": d_construccion,
             "bits-zip": d_bits_zip, "formato-pkz": d_formato, "preorden": d_preorden,
             "llamadas-recorrer": d_recorrer, "llamadas-leer-arbol": d_leer_arbol,
             "reconstruccion": d_reconstruccion, "recorrido-bits": d_recorrido_bits,
             "flujo-comprimir": d_flujo_comprimir, "flujo-descomprimir": d_flujo_descomprimir}


# =====================================================================
# 7. De bloques a piezas del PDF
# =====================================================================
def tabla_pdf(bloque, ancho, anchos=None):
    enc, filas = bloque["encabezado"], bloque["filas"]
    n = len(enc)
    if anchos:
        proporcion = anchos
    else:
        proporcion = []
        for j in range(n):
            largo = max([len(norm(enc[j]))] + [len(norm(f[j])) for f in filas if j < len(f)])
            proporcion.append(min(max(largo, 6), 46))
    cols = [ancho * p / sum(proporcion) for p in proporcion]
    datos = [[Paragraph(inline(h, 8.3, "#bff0ee"), TH) for h in enc]]
    for f in filas:
        datos.append([Paragraph(inline(f[j] if j < len(f) else "", 8.3), TD) for j in range(n)])
    t = Table(datos, colWidths=cols, repeatRows=1, hAlign="LEFT")
    reglas = [("BACKGROUND", (0, 0), (-1, 0), TINTA), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
              ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDE), ("BOX", (0, 0), (-1, -1), 0.6, BORDE)]
    for i in range(1, len(datos)):
        if i % 2 == 0:
            reglas.append(("BACKGROUND", (0, i), (-1, i), FONDO))
    t.setStyle(TableStyle(reglas))
    t.spaceBefore, t.spaceAfter = 3, 10
    return t


def aviso_pdf(b, ancho, estado):
    etiqueta, color, fondo = AVISOS.get(b["clase"], AVISOS["NOTA"])
    cab = f'<font name="Segoe-Bold" size="7.4" color="{hexcolor(color)}">{etiqueta}</font>'
    if b["titulo"]:
        cab += f'<br/><font name="Segoe-Semibold" size="10.6" color="{hexcolor(TINTA)}">{inline(b["titulo"])}</font>'
    estilo_cab = ParagraphStyle("cab_aviso", parent=EN_AVISO, leading=14.5, spaceAfter=4)
    interior = [Paragraph(cab, estilo_cab)] + convertir(b["bloques"], ancho - 26, estado, dentro=True)
    t = Table([[interior]], colWidths=[ancho])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("LINEBEFORE", (0, 0), (0, -1), 3.2, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                           ("ROUNDEDCORNERS", [3, 6, 6, 3])]))
    t.spaceBefore, t.spaceAfter = 4, 10
    return t


def unido_a_lo_siguiente(f):
    return bool(getattr(f, "keepWithNext", 0) or getattr(getattr(f, "style", None), "keepWithNext", 0))


def agregar(piezas, nuevos, dividir=False, dentro=False):
    """Agrega un bloque y lo mantiene en la misma página que su etiqueta, título o frase de entrada.

    Dentro de un recuadro (una celda de tabla) no se agrupa: la celda nunca se parte entre páginas
    y KeepTogether solo funciona en el marco de la página."""
    if dentro:
        piezas.extend(nuevos)
        return
    previas = []
    while piezas and unido_a_lo_siguiente(piezas[-1]) and not isinstance(piezas[-1], (PageBreak, Apertura)):
        previas.insert(0, piezas.pop())
    for p in previas:
        p.keepWithNext = 0
    if dividir:
        # Bloques largos (tablas extensas, apéndices) se parten entre páginas; su título solo exige
        # que quede sitio para el título y las primeras filas.
        if previas:
            alto_previas = sum(p.wrap(ANCHO, ALTO_PAG)[1] + p.getSpaceBefore() + p.getSpaceAfter()
                               for p in previas)
            piezas.append(CondPageBreak(alto_previas + 110))
        piezas.extend(previas + nuevos)
        return
    piezas.append(KeepTogether(previas + nuevos))


def convertir(bloques, ancho, estado, dentro=False):
    piezas, k = [], 0
    estilo_p = EN_AVISO if dentro else CUERPO
    estilo_l = LISTA_AVISO if dentro else LISTA
    estilo_entrada = ParagraphStyle("entrada", parent=estilo_p, keepWithNext=1)  # Frases que terminan en ":".
    while k < len(bloques):
        b = bloques[k]
        t = b["tipo"]
        if t == "h" and b["nivel"] == 1:
            if estado["capitulos"] or estado["previas"]:
                piezas.append(PageBreak())
            estado["previas"] = True
            estado["numerar"] = b["numerado"]
            estado["seccion"] = 0
            if b["numerado"]:
                estado["capitulos"] += 1
                n = str(estado["capitulos"])
                piezas.append(Apertura(n, f"CAPÍTULO {n}", b["texto"], f"cap{n}"))
            elif b["texto"].startswith("Apéndice"):
                etiqueta, _, titulo = b["texto"].partition(". ")
                piezas.append(Apertura(None, etiqueta.upper(), titulo, f"ap{b['linea']}", b["texto"]))
            else:
                piezas.append(Apertura(None, "GUÍA DE ESTUDIO", b["texto"], f"x{b['linea']}"))
        elif t == "h" and b["nivel"] == 2:
            estado["seccion"] += 1
            num = f"{estado['capitulos']}.{estado['seccion']}" if estado.get("numerar") else ""
            texto = (f'<font color="{hexcolor(TEAL)}">{num}</font>&nbsp;&nbsp;' if num else "") + inline(b["texto"])
            p = Paragraph(texto, H2)
            p._toc = (1, f"{num}  {b['texto']}".strip().replace("`", ""), f"s{estado['capitulos']}_{estado['seccion']}"
                      f"_{len(piezas)}")
            piezas.append(p)
        elif t == "h":
            paso = next((p for p in PASOS if b["texto"].startswith(p)), None)
            piezas.append(Paso(b["texto"]) if paso else Paragraph(inline(b["texto"]), H3))
        elif t == "p" and re.fullmatch(r"\*\*¿.+\?\*\*", b["texto"]):
            piezas.append(Paragraph(inline(b["texto"][2:-2]), PREGUNTA))
        elif t == "p":
            piezas.append(Paragraph(inline(b["texto"]), estilo_entrada if b["texto"].endswith(":") else estilo_p))
        elif t == "lista":
            items = [Paragraph(inline(item), estilo_l, bulletText=f"{i}." if b["ordenada"] else "•")
                     for i, item in enumerate(b["items"], 1)]
            agregar(piezas, items[:2], dentro=dentro)  # La frase de entrada no queda sola al pie de la página.
            piezas.extend(items[2:] + [Spacer(1, 3)])
        elif t == "tabla":
            tabla = tabla_pdf(b, ancho, estado.pop("anchos", None))
            agregar(piezas, [tabla], dividir=len(b["filas"]) > 10, dentro=dentro)
        elif t == "aviso":
            agregar(piezas, [aviso_pdf(b, ancho, estado)], dentro=dentro)
        elif t == "comentario":
            texto = b["texto"]
            if texto.startswith("anchos:"):
                estado["anchos"] = [float(x) for x in texto[len("anchos:"):].split(",")]
            elif texto == "salto":
                piezas.append(PageBreak())
        elif t == "codigo":
            info = b["info"]
            m = re.fullmatch(r"python\s+(\w+\.py):(\d+)-(\d+)", info)
            if m:
                a, z = int(m.group(2)), int(m.group(3))
                rango = f"línea {a}" if a == z else f"líneas {a}-{z}"
                listado = Listado(b["lineas"], a, f"{m.group(1)} · {rango}", True, "código real")
                agregar(piezas, [listado], dividir=len(b["lineas"]) > 30, dentro=dentro)
            elif info == "python ejecutar":
                salida = bloques[k + 1]
                codigo = Listado(b["lineas"], 1, "Ejemplo en Python", False, "se ejecutó al generar la guía")
                codigo.spaceAfter = 0
                agregar(piezas, [codigo, CajaTexto(salida["lineas"], "salida", "Salida")], dentro=dentro)
                k += 1
            elif info == "terminal":
                agregar(piezas, [TerminalCaja(b["lineas"])], dentro=dentro)
            elif info == "calculo":
                agregar(piezas, [CajaTexto(b["lineas"], "calculo", "Cálculo paso a paso")], dentro=dentro)
            elif info.startswith("diagrama "):
                agregar(piezas, [DIAGRAMAS[info.split()[1]]()], dentro=dentro)
            else:
                agregar(piezas, [CajaTexto(b["lineas"], "texto")], dentro=dentro)
        k += 1
    return piezas


# =====================================================================
# 8. Documento: portada, índice, encabezados y marcadores
# =====================================================================
class Guia(BaseDocTemplate):
    def __init__(self, archivo, meta):
        super().__init__(str(archivo), pagesize=A4, leftMargin=MARGEN_I, rightMargin=MARGEN_D,
                         topMargin=MARGEN_S, bottomMargin=MARGEN_INF, title=meta["titulo"],
                         author="Proyecto PyWrap Huffman", subject=meta["subtitulo"],
                         creator="output/guia_estudio/generar_guia_estudio.py (ReportLab)")
        self.meta = meta
        marco = Frame(MARGEN_I, MARGEN_INF, ANCHO, ALTO_PAG - MARGEN_S - MARGEN_INF, id="marco",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="portada", frames=[marco], onPage=self.portada),
                               PageTemplate(id="normal", frames=[marco], onPageEnd=self.marco_pagina)])
        self.capitulo, self.apertura = "Índice", False

    def beforeDocument(self):  # Cada pasada de multiBuild empieza de nuevo en el índice.
        self.capitulo, self.apertura = "Índice", False

    def afterFlowable(self, f):
        if hasattr(f, "_capitulo"):
            self.capitulo, self.apertura = f._capitulo, True
        if hasattr(f, "_toc"):
            nivel, texto, clave = f._toc
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel, closed=nivel > 0)
            self.notify("TOCEntry", (nivel, texto, self.page, clave))

    def marco_pagina(self, c, doc):
        c.saveState()
        if not self.apertura:
            c.setFont("Segoe", 8)
            c.setFillColor(GRIS)
            c.drawString(MARGEN_I, ALTO_PAG - 40, self.capitulo)
            c.drawRightString(ANCHO_PAG - MARGEN_D, ALTO_PAG - 40, "Huffman desde cero · Guía de estudio")
            c.setStrokeColor(BORDE)
            c.setLineWidth(0.7)
            c.line(MARGEN_I, ALTO_PAG - 47, ANCHO_PAG - MARGEN_D, ALTO_PAG - 47)
        c.setStrokeColor(BORDE)
        c.line(MARGEN_I, 38, ANCHO_PAG - MARGEN_D, 38)
        c.setFont("Segoe", 7.8)
        c.setFillColor(GRIS)
        c.drawString(MARGEN_I, 25, f"comprimir.py y descomprimir.py · versión definitiva · commit {COMMIT}")
        caja(c, ANCHO_PAG - MARGEN_D - 30, 20, 30, 15, TEAL, None, 7.5)
        c.setFillColor(white)
        c.setFont("Segoe-Bold", 8.2)
        c.drawCentredString(ANCHO_PAG - MARGEN_D - 15, 24.6, str(doc.page))
        c.restoreState()
        self.apertura = False

    def portada(self, c, doc):
        m = self.meta
        c.saveState()
        base = 392  # Borde inferior del bloque oscuro.
        c.setFillColor(TINTA)
        c.rect(0, base, ANCHO_PAG, ALTO_PAG - base, stroke=0, fill=1)
        c.setFillColor(HexColor("#24314f"))
        c.setFont("Consolas", 8)
        for fila in range(32):  # Textura de fondo hecha con los bits reales de ZIP.
            y = ALTO_PAG - 34 - fila * 13
            if y < base + 10:
                break
            c.drawString(300, y, " ".join((T.bits_relleno * 8)[fila % 7:][:22]))
        # Árbol decorativo con la forma real del árbol de AAAAABBC (y = borde inferior de cada nodo).
        alto = 24
        nodos = {"r": (452, 690, str(peso(T.raiz, T.frecuencias)), True),
                 "i": (392, 612, str(peso(T.raiz[0], T.frecuencias)), True),
                 "a": (512, 612, f"A · {T.frecuencias[65]}", False),
                 "c": (352, 534, f"C · {T.frecuencias[67]}", False),
                 "b": (432, 534, f"B · {T.frecuencias[66]}", False)}
        c.setStrokeColor(TEAL_VIVO)
        c.setLineWidth(1.4)
        for padre, hijo, bit in (("r", "i", "0"), ("r", "a", "1"), ("i", "c", "0"), ("i", "b", "1")):
            x1, y1 = nodos[padre][0], nodos[padre][1]
            x2, y2 = nodos[hijo][0], nodos[hijo][1] + alto
            c.line(x1, y1, x2, y2)
            c.setFillColor(TEAL_VIVO)
            c.setFont("Segoe-Bold", 9)
            c.drawString((x1 + x2) / 2 + (-13 if bit == "0" else 6), (y1 + y2) / 2 + 2, bit)
        for x, y, texto, interno in nodos.values():
            caja(c, x - 27, y, 54, alto, TINTA if interno else TEAL_VIVO, TEAL_VIVO, 7, 1.3)
            c.setFillColor(white if interno else TINTA)
            c.setFont("Segoe-Bold", 10)
            c.drawCentredString(x, y + 8, texto)
        c.setFillColor(TEAL_VIVO)
        c.setFont("Segoe-Bold", 9.5)
        c.drawString(MARGEN_I, 772, "GUÍA DE ESTUDIO · PROYECTO PYWRAP", charSpace=1.8)
        c.setFillColor(white)
        c.setFont("Segoe-Black", 46)
        c.drawString(MARGEN_I, 704, "Huffman")
        c.setFillColor(TEAL_VIVO)
        c.setFont("Segoe-Light", 40)
        c.drawString(MARGEN_I, 659, "desde cero")
        c.setFillColor(HexColor("#d3dbe7"))
        c.setFont("Segoe", 13)
        for k, l in enumerate(m["subtitulo"].split(" | ")):
            c.drawString(MARGEN_I, 612 - k * 18, l)
        c.setFillColor(HexColor("#9fb0c8"))
        c.setFont("Segoe", 10)
        for k, l in enumerate(m["lema"].split(" | ")):
            c.drawString(MARGEN_I, 552 - k * 15, l)
        # El método: las seis etapas de cada explicación.
        c.setFillColor(HexColor("#9fb0c8"))
        c.setFont("Segoe", 9)
        c.drawString(MARGEN_I, 470, "Cada tema recorre la misma ruta:")
        etapas = (("CONCEPTO", TEAL), ("EXPLICACIÓN", AMBAR), ("CÓDIGO REAL", HexColor("#4b5d85")),
                  ("EJECUCIÓN", NARANJA), ("RESULTADO", VERDE), ("CONCLUSIÓN", VIOLETA))
        hueco = 13
        ancho_etapa = (ANCHO - hueco * (len(etapas) - 1)) / len(etapas)
        for k, (texto, color) in enumerate(etapas):
            x = MARGEN_I + k * (ancho_etapa + hueco)
            caja(c, x, 436, ancho_etapa, 20, color, None, 10)
            c.setFillColor(white)
            c.setFont("Segoe-Bold", 7.4)
            c.drawCentredString(x + ancho_etapa / 2, 442.6, texto)
            if k < len(etapas) - 1:
                c.setFillColor(TEAL_VIVO)
                c.setFont("Segoe-Bold", 10)
                c.drawCentredString(x + ancho_etapa + hueco / 2, 442, "→")
        # Tira de bytes del .pkz de AAAAABBC.
        c.setFillColor(TINTA)
        c.setFont("Segoe-Semibold", 12.5)
        c.drawString(MARGEN_I, 350, "El ejemplo que recorre toda la guía")
        c.setFont("Segoe", 9.6)
        c.setFillColor(GRIS)
        c.drawString(MARGEN_I, 334, f"El texto AAAAABBC ({len(T.datos)} bytes) se convierte en este archivo .pkz "
                                    f"de {len(T.pkz)} bytes:")
        campos = ["NF"] + ["TREE"] * len(T.arbol) + ["BS"] + ["ZIP"] * len(T.zip)
        colores = {"NF": (VIOLETA_CLARO, VIOLETA), "TREE": (TEAL_CLARO, TEAL), "BS": (NARANJA_CLARO, NARANJA),
                   "ZIP": (VERDE_CLARO, VERDE)}
        w = ANCHO / len(T.pkz)
        for i, (b, campo) in enumerate(zip(T.pkz, campos)):
            fondo, borde = colores[campo]
            caja(c, MARGEN_I + i * w + 1, 286, w - 2, 30, fondo, borde, 4, 1)
            c.setFillColor(TINTA)
            c.setFont("Consolas-Bold", 11)
            c.drawCentredString(MARGEN_I + i * w + w / 2, 297, f"{b:02X}")
        for a, z, campo in ((0, 0, "NF"), (1, len(T.arbol), "TREE"), (len(T.arbol) + 1, len(T.arbol) + 1, "BS"),
                            (len(T.arbol) + 2, len(T.pkz) - 1, "ZIP")):
            c.setFillColor(colores[campo][1])
            c.setFont("Segoe-Bold", 9)
            c.drawCentredString(MARGEN_I + (a + z + 1) * w / 2, 272, campo)
        # Las tres partes de la guía.
        partes = (("CAPÍTULOS 1 A 3", "La idea, sin código", TEAL,
                   "Bytes, árbol, códigos y formato .pkz, resueltos a mano con AAAAABBC."),
                  ("CAPÍTULOS 4 A 6", "El código real", NARANJA,
                   "El Python necesario y los dos programas, bloque a bloque y variable a variable."),
                  ("CAPÍTULOS 7 A 10", "Práctica y exposición", VIOLETA,
                   "Validaciones, ejercicios resueltos, preguntas de exposición y glosario."))
        hueco = 12
        ancho_parte = (ANCHO - 2 * hueco) / 3
        estilo = ParagraphStyle("parte", fontName="Segoe", fontSize=8.8, leading=12.2, textColor=GRIS)
        for k, (etiqueta, titulo, color, texto) in enumerate(partes):
            x = MARGEN_I + k * (ancho_parte + hueco)
            caja(c, x, 132, ancho_parte, 104, FONDO, BORDE, 7, 0.8)
            c.setFillColor(color)
            c.rect(x + 12, 224, 28, 3, stroke=0, fill=1)
            c.setFont("Segoe-Bold", 7.6)
            c.drawString(x + 12, 208, etiqueta)
            c.setFillColor(TINTA)
            c.setFont("Segoe-Semibold", 11.5)
            c.drawString(x + 12, 192, titulo)
            parrafo = Paragraph(texto, estilo)
            _, h = parrafo.wrap(ancho_parte - 24, 60)
            parrafo.drawOn(c, x + 12, 180 - h)
        c.setFillColor(GRIS)
        c.setFont("Segoe", 8.8)
        c.drawString(MARGEN_I, 104, f"Versión definitiva del código (commit {COMMIT}): comprimir.py "
                                    f"({NLINEAS['comprimir.py']} líneas) y descomprimir.py "
                                    f"({NLINEAS['descomprimir.py']} líneas).")
        c.drawString(MARGEN_I, 90, "Cada ejemplo, tabla y salida de terminal se obtuvo ejecutando esos programas.")
        c.setStrokeColor(BORDE)
        c.line(MARGEN_I, 72, ANCHO_PAG - MARGEN_D, 72)
        c.setFont("Segoe", 8.6)
        c.drawString(MARGEN_I, 56, m.get("fecha", ""))
        c.drawRightString(ANCHO_PAG - MARGEN_D, 56,
                          "Concepto → explicación → código → ejecución → resultado → conclusión")
        c.restoreState()


def construir_pdf(meta, bloques, destino):
    estado = {"capitulos": 0, "seccion": 0, "previas": False}
    toc = TableOfContents(levelStyles=[TOC0, TOC1], dotsMinLevel=0)
    titulo_indice = Paragraph("Índice", ParagraphStyle("indice", fontName="Segoe-Semibold", fontSize=26,
                                                        leading=32, textColor=TINTA, spaceAfter=4))
    nota_indice = Paragraph(inline("Los capítulos 1 a 3 explican la idea sin código; del 4 al 6 se estudia el "
                                   "código real; del 7 al 10 se practica y se prepara la exposición."),
                            ParagraphStyle("nota_indice", parent=CUERPO, textColor=GRIS, spaceAfter=10))
    historia = [NextPageTemplate("normal"), PageBreak(), titulo_indice, nota_indice, toc, PageBreak()]
    estado["previas"] = False
    historia += convertir(bloques, ANCHO, estado)
    doc = Guia(destino, meta)
    doc.multiBuild(historia, maxPasses=8)
    return doc


# =====================================================================
# 9. Verificación final del PDF y programa principal
# =====================================================================
def verificar_pdf(ruta):
    from pypdf import PdfReader

    texto = re.sub(r"\s+", " ", " ".join(p.extract_text() for p in PdfReader(str(ruta)).pages))
    problemas = []
    for archivo in PROGRAMAS:  # Los apéndices contienen el código completo.
        for n, l in enumerate(CODIGO[archivo], 1):
            if l.strip() and re.sub(r"\s+", " ", l).strip() not in texto:
                problemas.append(f"El PDF no contiene la línea {n} de {archivo}")
    for prohibido in ("heapq.heap", "cantidad_bits", ".resolve()", "python3", "(1 <<", "cola[0][2]"):
        if prohibido in texto:
            problemas.append(f"El PDF contiene texto de una versión anterior: {prohibido}")
    for requerido in (hexa(T.pkz), COMMIT, "AAAAABBC"):
        if requerido not in texto:
            problemas.append(f"El PDF no contiene: {requerido}")
    return problemas, len(PdfReader(str(ruta)).pages)


def imprimir_tablas():
    for nombre in ("mensaje", "frecuencias", "vueltas", "codigos", "recorrer", "pkz", "leer_arbol", "pasos"):
        print(f"\n<!-- tabla: {nombre} -->")
        for fila in tabla_esperada(nombre):
            print("| " + " | ".join("" if v is None else v for v in fila) + " |")


def main():
    if "--tablas" in sys.argv:
        imprimir_tablas()
        return 0
    if SIN_CONFIRMAR:
        print("Aviso: comprimir.py o descomprimir.py tienen cambios sin confirmar en git.")
    meta, bloques = leer_fuente()
    errores = verificar(meta, bloques)
    if errores:
        print(f"La guía NO coincide con el código real ({len(errores)} diferencias):")
        for e in errores:
            print("  -", e)
        return 1
    print("Verificación previa: la guía coincide con el código real.")
    SALIDA_PDF.parent.mkdir(parents=True, exist_ok=True)
    temporal = SALIDA_PDF.with_suffix(".tmp.pdf")
    construir_pdf(meta, bloques, temporal)
    problemas, paginas = verificar_pdf(temporal)
    if problemas:
        print("El PDF generado tiene problemas:")
        for p in problemas:
            print("  -", p)
        return 1
    os.replace(temporal, SALIDA_PDF)
    print(f"PDF generado y verificado: {SALIDA_PDF} ({paginas} páginas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
