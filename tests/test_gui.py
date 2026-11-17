"""Pruebas de la interfaz gráfica simplificada de PyWrap."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Se necesita Tkinter disponible para las pruebas de GUI.')
class GuiTests(unittest.TestCase):
    def test_gui_compress_and_decompress(self):
        from pywrap import gui
        app = gui.PyWrapApp()
        self.addCleanup(app.destroy)
        app.update()
        app.withdraw()

        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            src = base / 'test.txt'
            src.write_bytes(b'anita patina')

            # Comprimir
            app.file_path.set(str(src))
            app.mode.set('compress')
            with patch.object(gui.messagebox, 'showinfo'):
                app._execute()

            out_pkz = Path(gui.__file__).resolve().parent.parent / 'data' / 'wrp' / 'test.txt.pkz'
            self.assertTrue(out_pkz.exists())
            self.assertEqual(out_pkz.stat().st_size, 28)

            # Descomprimir
            app.file_path.set(str(out_pkz))
            app.mode.set('decompress')
            with patch.object(gui.messagebox, 'showinfo'):
                app._execute()

            restored = Path(gui.__file__).resolve().parent.parent / 'data' / 'unwrp' / 'test.txt'
            self.assertTrue(restored.exists())
            self.assertEqual(restored.read_bytes(), b'anita patina')

            # Limpieza de archivos de prueba generados en data/
            out_pkz.unlink(missing_ok=True)
            restored.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
