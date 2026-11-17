"""Alternativa de consola, sin necesidad de Tkinter."""
import argparse
from pathlib import Path

from pywrap import compress, decompress
from pywrap.reporting import describe_result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='PyWrap: compresión Huffman sin pérdida.')
    parser.add_argument('action', choices=['compress', 'decompress'])
    parser.add_argument('file', help='Ruta del archivo de entrada')
    parser.add_argument('--output-dir', help='Directorio de salida')
    parser.add_argument('--overwrite', action='store_true',
                        help='Autorizar explícitamente el reemplazo del destino')
    args = parser.parse_args(argv)
    folder = (Path(args.output_dir).expanduser() if args.output_dir else
              Path(__file__).resolve().parent / 'data' /
              ('wrp' if args.action == 'compress' else 'unwrp'))
    try:
        operation = compress if args.action == 'compress' else decompress
        result = operation(args.file, folder, overwrite=args.overwrite)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Error de PyWrap: {error}\n')
    print(describe_result(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
