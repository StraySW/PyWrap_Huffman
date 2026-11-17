"""Pruebas de la interfaz gráfica simplificada de PyWrap."""

from pathlib import Path
import tempfile
from threading import Event
import time
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError:
    tk = None


@unittest.skipIf(tk is None, 'Se necesita Tkinter disponible para las pruebas de GUI.')
class GuiTests(unittest.TestCase):
    def wait_for_operation(self, app):
        deadline = time.monotonic() + 10
        while app.busy and time.monotonic() < deadline:
            app.update()
            time.sleep(0.005)
        self.assertFalse(app.busy, 'La operación no terminó.')

    def test_gui_compress_and_decompress(self):
        from pywrap import gui
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            app = gui.PyWrapApp(output_root=base / 'data')
            self.addCleanup(app.destroy)
            app.update()
            app.withdraw()
            src = base / 'test.txt'
            src.write_bytes(b'anita patina')

            # Comprimir
            app.file_path.set(str(src))
            with patch.object(gui.messagebox, 'showerror') as error:
                app._execute('compress')
                self.wait_for_operation(app)
                error.assert_not_called()

            out_pkz = base / 'data' / 'wrp' / 'test.txt.pkz'
            self.assertTrue(out_pkz.exists())
            self.assertEqual(out_pkz.stat().st_size, 28)

            # Descomprimir
            app.file_path.set(str(out_pkz))
            with patch.object(gui.messagebox, 'showerror') as error:
                app._execute('decompress')
                self.wait_for_operation(app)
                error.assert_not_called()

            restored = base / 'data' / 'unwrp' / 'test.txt'
            self.assertTrue(restored.exists())
            self.assertEqual(restored.read_bytes(), b'anita patina')

            # Una segunda ejecución debe respetar la negativa a reemplazar.
            restored.write_bytes(b'conservar este archivo')
            with patch.object(gui.messagebox, 'askyesno', return_value=False) as confirm:
                app._execute('decompress')
                self.wait_for_operation(app)
                confirm.assert_called_once()
            self.assertEqual(restored.read_bytes(), b'conservar este archivo')

            # Aceptar el reemplazo reinicia la operación en segundo plano.
            with patch.object(gui.messagebox, 'askyesno', return_value=True) as confirm:
                app._execute('decompress')
                self.wait_for_operation(app)
                confirm.assert_called_once()
            self.assertEqual(restored.read_bytes(), src.read_bytes())

    def test_window_remains_responsive_during_operation(self):
        from pywrap import gui
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            app = gui.PyWrapApp(output_root=base / 'data')
            self.addCleanup(app.destroy)
            app.withdraw()
            source = base / 'source.bin'
            source.write_bytes(bytes(range(256)))
            app.file_path.set(str(source))
            release = Event()
            real_compress = gui.compress

            def slow_compress(*args, **kwargs):
                if not release.wait(5):
                    raise TimeoutError('La prueba no liberó el trabajador.')
                return real_compress(*args, **kwargs)

            with patch.object(gui, 'compress', side_effect=slow_compress), \
                    patch.object(gui.messagebox, 'showwarning') as warning, \
                    patch.object(gui.messagebox, 'showerror') as error:
                try:
                    app._execute('compress')
                    self.assertTrue(app.busy)
                    self.assertTrue(all(str(c['state']) == 'disabled' for c in app.controls))
                    tick = []
                    app.after(0, lambda: tick.append(True))
                    app.update()
                    self.assertEqual(tick, [True])
                    app._close()
                    warning.assert_called_once()
                    self.assertTrue(app.winfo_exists())
                finally:
                    release.set()
                    self.wait_for_operation(app)
                error.assert_not_called()
            self.assertTrue(all(str(c['state']) == 'normal' for c in app.controls))

    def test_invalid_file_reports_error_and_reenables_controls(self):
        from pywrap import gui
        with tempfile.TemporaryDirectory() as folder:
            app = gui.PyWrapApp(output_root=folder)
            self.addCleanup(app.destroy)
            app.withdraw()
            app.file_path.set(str(Path(folder) / 'missing.bin'))
            with patch.object(gui.messagebox, 'showerror') as error:
                app._execute('compress')
                self.wait_for_operation(app)
                error.assert_called_once()
            self.assertTrue(all(str(c['state']) == 'normal' for c in app.controls))


if __name__ == '__main__':
    unittest.main()
