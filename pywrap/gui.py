"""Interfaz gráfica de usuario simple y directa para PyWrap."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .huffman import compress, decompress, Result
from .reporting import describe_result


BG = '#F4F6F9'
WHITE = '#FFFFFF'
PRIMARY = '#1F6FEB'
DARK = '#1C2128'
MUTED = '#57606A'


class PyWrapApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('PyWrap | Compresor Huffman')
        self.geometry('720x600')
        self.minsize(640, 500)
        self.configure(bg=BG)

        self.mode = tk.StringVar(value='compress')
        self.file_path = tk.StringVar()

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure('TFrame', background=BG)
        style.configure('Card.TFrame', background=WHITE, relief='flat')
        style.configure('TLabel', background=BG, foreground=DARK, font=('Segoe UI', 10))
        style.configure('Card.TLabel', background=WHITE, foreground=DARK, font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=BG, foreground=PRIMARY, font=('Segoe UI', 18, 'bold'))
        style.configure('Subtitle.TLabel', background=BG, foreground=MUTED, font=('Segoe UI', 10))
        style.configure('CardTitle.TLabel', background=WHITE, foreground=DARK, font=('Segoe UI', 11, 'bold'))
        style.configure('TRadiobutton', background=WHITE, foreground=DARK, font=('Segoe UI', 10))
        style.configure('Primary.TButton', background=PRIMARY, foreground=WHITE, font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('Primary.TButton', background=[('active', '#1A56B8'), ('disabled', '#A5C4F5')])

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Encabezado
        ttk.Label(main_frame, text='PyWrap · Compresión Huffman', style='Title.TLabel').pack(anchor='w')
        ttk.Label(
            main_frame,
            text='Compresión y descompresión de archivos mediante algoritmo Huffman por caracteres y bytes.',
            style='Subtitle.TLabel',
        ).pack(anchor='w', pady=(2, 16))

        # Tarjeta de selección y acción
        action_card = ttk.Frame(main_frame, style='Card.TFrame', padding=16)
        action_card.pack(fill='x', pady=(0, 14))

        ttk.Label(action_card, text='Archivo de entrada:', style='CardTitle.TLabel').pack(anchor='w', pady=(0, 6))

        file_row = ttk.Frame(action_card, style='Card.TFrame')
        file_row.pack(fill='x', pady=(0, 12))

        self.entry_file = ttk.Entry(file_row, textvariable=self.file_path, font=('Segoe UI', 10))
        self.entry_file.pack(side='left', fill='x', expand=True, padx=(0, 8))

        btn_browse = ttk.Button(file_row, text='Examinar…', command=self._browse_file)
        btn_browse.pack(side='left')

        # Selector de operación
        op_row = ttk.Frame(action_card, style='Card.TFrame')
        op_row.pack(fill='x', pady=(0, 12))

        ttk.Radiobutton(op_row, text='Comprimir (Wrap a .pkz)', variable=self.mode, value='compress').pack(side='left', padx=(0, 20))
        ttk.Radiobutton(op_row, text='Descomprimir (UnWrap)', variable=self.mode, value='decompress').pack(side='left')

        btn_execute = ttk.Button(action_card, text='▶ Ejecutar Operación', style='Primary.TButton', command=self._execute)
        btn_execute.pack(fill='x')

        # Tarjetas de resumen métrico
        metrics_frame = ttk.Frame(main_frame)
        metrics_frame.pack(fill='x', pady=(0, 14))

        self.card_orig = self._metric_box(metrics_frame, 'Original', '-')
        self.card_comp = self._metric_box(metrics_frame, 'Resultado', '-')
        self.card_change = self._metric_box(metrics_frame, 'Variación', '-')
        self.card_symbols = self._metric_box(metrics_frame, 'Símbolos', '-')

        # Consola de detalles
        ttk.Label(main_frame, text='Registro de operación y estadísticas:', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 4))
        self.console = tk.Text(main_frame, height=10, bg=WHITE, fg=DARK, font=('Consolas', 9), relief='flat', padx=10, pady=10)
        self.console.pack(fill='both', expand=True)

        self._log('PyWrap listo. Selecciona un archivo para comprimir o descomprimir.')

    def _metric_box(self, parent: ttk.Frame, title: str, initial_value: str) -> tk.StringVar:
        box = ttk.Frame(parent, style='Card.TFrame', padding=10)
        box.pack(side='left', fill='both', expand=True, padx=4)
        ttk.Label(box, text=title, style='Card.TLabel', foreground=MUTED, font=('Segoe UI', 9)).pack(anchor='center')
        val_var = tk.StringVar(value=initial_value)
        ttk.Label(box, textvariable=val_var, style='Card.TLabel', font=('Segoe UI', 12, 'bold')).pack(anchor='center')
        return val_var

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)
            if path.lower().endswith('.pkz'):
                self.mode.set('decompress')
            else:
                self.mode.set('compress')

    def _log(self, text: str) -> None:
        self.console.delete('1.0', 'end')
        self.console.insert('end', text + '\n')

    def _execute(self) -> None:
        raw_path = self.file_path.get().strip()
        if not raw_path:
            messagebox.showwarning('Atención', 'Por favor selecciona un archivo de entrada.')
            return

        source = Path(raw_path)
        if not source.is_file():
            messagebox.showerror('Error', f'El archivo no existe:\n{source}')
            return

        action = self.mode.get()
        # Salida predeterminada en carpetas data/wrp y data/unwrp del proyecto
        base_dir = Path(__file__).resolve().parent.parent
        out_folder = base_dir / 'data' / ('wrp' if action == 'compress' else 'unwrp')

        try:
            op_func = compress if action == 'compress' else decompress
            try:
                res = op_func(source, out_folder, overwrite=False)
            except FileExistsError:
                if messagebox.askyesno('Archivo existente', 'El archivo de destino ya existe.\n¿Deseas reemplazarlo?'):
                    res = op_func(source, out_folder, overwrite=True)
                else:
                    self._log('Operación cancelada por el usuario (no se reemplazó el archivo existente).')
                    return

            self._update_results(res)
            messagebox.showinfo('Éxito', f'Operación completada con éxito.\nGuardado en: {res.destination.name}')
        except Exception as error:
            messagebox.showerror('Error de PyWrap', str(error))
            self._log(f'ERROR: {error}')

    def _update_results(self, res: Result) -> None:
        self.card_orig.set(f'{res.original_bytes:,} B')
        self.card_comp.set(f'{res.compressed_bytes:,} B')
        if res.original_bytes:
            pct = res.savings_percentage
            sign = '-' if pct >= 0 else '+'
            self.card_change.set(f'{sign}{abs(pct):.1f}%')
        else:
            self.card_change.set('N/A')
        self.card_symbols.set(str(res.symbol_count))

        self._log(describe_result(res))


def launch() -> None:
    app = PyWrapApp()
    app.mainloop()
