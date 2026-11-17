"""Una selección de archivo, dos botones y un resultado."""
from __future__ import annotations

from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .huffman import compress, decompress


class PyWrapApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('PyWrap | Compresor Huffman')
        self.geometry('680x440')
        self.minsize(520, 360)
        self.output_root = Path(__file__).resolve().parent.parent / 'data'
        self.file_path = tk.StringVar()
        self.busy = False
        self.events = SimpleQueue()
        self.protocol('WM_DELETE_WINDOW', self._close)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='PyWrap · Huffman', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Selecciona un archivo y elige una operación.').pack(anchor='w', pady=(4, 12))
        row = ttk.Frame(frame)
        row.pack(fill='x')
        entry = ttk.Entry(row, textvariable=self.file_path)
        entry.pack(side='left', fill='x', expand=True)
        browse = ttk.Button(row, text='Examinar…', command=self._browse_file)
        browse.pack(side='left', padx=(8, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=12)
        wrap = ttk.Button(buttons, text='Comprimir', command=lambda: self._execute('compress'))
        wrap.pack(side='left', fill='x', expand=True, padx=(0, 4))
        unwrap = ttk.Button(buttons, text='Descomprimir', command=lambda: self._execute('decompress'))
        unwrap.pack(side='left', fill='x', expand=True, padx=(4, 0))
        self.controls = (entry, browse, wrap, unwrap)
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 12))
        self.console = tk.Text(frame, wrap='word', font=('Segoe UI', 10), state='disabled')
        self.console.pack(fill='both', expand=True)
        self._log('Listo. Admite cualquier tipo de archivo.\nLas salidas se guardan en data/wrp y data/unwrp.')

    def _browse_file(self):
        path = filedialog.askopenfilename(title='Seleccionar archivo')
        if path:
            self.file_path.set(path)

    def _log(self, text):
        self.console.configure(state='normal')
        self.console.delete('1.0', 'end')
        self.console.insert('end', text + '\n')
        self.console.configure(state='disabled')

    def _execute(self, action, *, overwrite=False):
        if self.busy:
            return
        if not self.file_path.get().strip():
            messagebox.showwarning('PyWrap', 'Selecciona un archivo primero.', parent=self)
            return
        source = Path(self.file_path.get().strip()).expanduser()
        folder = self.output_root / ('wrp' if action == 'compress' else 'unwrp')
        operation = compress if action == 'compress' else decompress
        self.busy = True
        for control in self.controls:
            control.configure(state='disabled')
        self.progress.start()
        self._log('Procesando… Puedes mover la ventana mientras termina.')

        def work():
            try:
                self.events.put(operation(source, folder, overwrite=overwrite))
            except Exception as error:
                self.events.put(error)

        Thread(target=work, daemon=True).start()
        self.after(50, self._finish, action)

    def _finish(self, action):
        try:
            result = self.events.get_nowait()
        except Empty:
            self.after(50, self._finish, action)
            return
        self.busy = False
        self.progress.stop()
        for control in self.controls:
            control.configure(state='normal')
        if isinstance(result, FileExistsError):
            if messagebox.askyesno('Archivo existente', 'El destino ya existe. ¿Reemplazarlo?', parent=self):
                self._execute(action, overwrite=True)
            else:
                self._log('Operación cancelada. Se conservó el archivo existente.')
        elif isinstance(result, Exception):
            self._log(f'Error: {result}')
            messagebox.showerror('Error de PyWrap', str(result), parent=self)
        else:
            self._log(str(result))

    def _close(self):
        if self.busy:
            messagebox.showwarning('PyWrap', 'Espera a que termine la operación antes de cerrar.', parent=self)
        else:
            self.destroy()


def launch() -> None:
    PyWrapApp().mainloop()
