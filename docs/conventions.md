# Convenciones de código

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a sí mismo en todas partes.

## Estilo Python

- **Versión:** Python 3.9+ (sintaxis `list[str]` permitida).
- **Formato:** PEP 8. Líneas máximo 100 caracteres.
- **Imports:** stdlib primero, luego locales. Una línea por módulo.
- **Strings:** comillas dobles `"..."` siempre. Comillas simples solo
  para escapar comillas dobles dentro.
- **f-strings** para interpolación. Nada de `.format()` ni `%`.

## Nombres

| Tipo                  | Convención    | Ejemplo              |
| --------------------- | ------------- | -------------------- |
| Módulos               | `snake_case`  | `notes.py`           |
| Clases                | `PascalCase`  | `Note`               |
| Funciones / variables | `snake_case`  | `load_notes`         |
| Constantes            | `UPPER_SNAKE` | `DEFAULT_NOTES_PATH` |
| Privadas              | prefijo `_`   | `_atomic_write`      |

## Estructura de archivo

Cada archivo en `src/` empieza con:

```python
"""Una línea describiendo el propósito del módulo."""
from __future__ import annotations

# imports stdlib
import json
import os

# imports locales
from src.notes import Note
```

## Tests

- Un archivo de test por módulo: `tests/<slice>/<ddd_component>/test_<módulo>.py`.

## Manejo de errores

Excepciones del dominio en cada slice.

## Comentarios

Por defecto **no** se escriben. Solo se permiten cuando explican un _por qué_
no obvio (p. ej. workaround documentado, invariante sutil). Los nombres deben
hacer el resto.
