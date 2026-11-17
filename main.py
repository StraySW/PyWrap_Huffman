"""Iniciar la interfaz gráfica: python3 main.py."""
import sys


def main() -> int:
    try:
        import tkinter as tk
    except ImportError:
        print('PyWrap necesita Tkinter. Instala Python con soporte Tcl/Tk. '
              'Consulta la sección macOS del README. La consola cli.py sigue disponible.',
              file=sys.stderr)
        return 1
    # Tk 8.5 de las herramientas de Apple puede abortar el proceso nativo
    # antes de que Python pueda capturar una excepción.
    if sys.platform == 'darwin' and tk.TkVersion < 8.6:
        print('PyWrap: Tk 8.5 de macOS no es compatible con esta interfaz. '
              'Instala Python de python.org con Tk 8.6 o posterior y verifica '
              '`python3 -m tkinter`. Consulta README.md. Puedes usar cli.py mientras tanto.',
              file=sys.stderr)
        return 1
    from pywrap.gui import launch
    try:
        launch()
    except tk.TclError as error:
        print(f'PyWrap no pudo iniciar Tkinter: {error}. '
              'Verifica `python3 -m tkinter` y consulta README.md.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
