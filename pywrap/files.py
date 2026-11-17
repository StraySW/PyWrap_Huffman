"""Módulo de compatibilidad con operaciones de archivo."""
from .huffman import (
    FormatError,
    Result,
    compress,
    decompress,
    output_path,
)

__all__ = ['FormatError', 'Result', 'compress', 'decompress', 'output_path']
