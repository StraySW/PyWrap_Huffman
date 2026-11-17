# Referencias de compatibilidad

Estos cuatro `.pkz` se generaron con el código de la fase 1, antes de modificar la aplicación para la fase 2. No se regeneran durante las pruebas. `test_analysis.py` fija sus SHA-256 y verifica descompresión exacta y recompresión idéntica.

- `anita.txt.pkz`: `b'anita patina'`, 28 bytes.
- `empty.bin.pkz`: archivo vacío, 2 bytes.
- `single.bin.pkz`: 17 repeticiones del byte `X`, 7 bytes.
- `all-bytes.bin.pkz`: bytes 0 a 255, una aparición de cada uno, 1280 bytes.

Son archivos de PyWrap; no provienen de WinWrap Java.
