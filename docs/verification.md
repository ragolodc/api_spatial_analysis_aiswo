# Verificación — Cómo demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificación

### Nivel 1 — Tests unitarios (obligatorio)

Toda función pública en `src/` tiene al menos un test en `tests/` que:

1. Cubre el camino feliz.
2. Cubre al menos un camino de error si la función puede fallar.
3. Se mockea todo lo que es necesario.

### Nivel 2 — Test de integración del endopoint.

1. Se debe realizar el test de integración del endpoint, para verificar que funciona correctamente todo el flujo de trabajo.

## Verificación final antes de cerrar

```bash
python -m pytest .\tests -v          # debe terminar con [OK] Entorno listo
```

Si algún test está rojo, **no** marques nada como `done`. Anota el bloqueo en `progress/current.md` con estado `blocked` en `feature_list.json`.
