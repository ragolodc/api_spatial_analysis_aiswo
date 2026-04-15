# AISWO Spatial Analysis API

Configuracion inicial para una API de analisis espacial con:

- FastAPI
- PostgreSQL + PostGIS
- Alembic
- Docker Compose
- Estructura base DDD (vertical slice `elevation`)

## Estructura

```text
src/
  modules/
    elevation/
      domain/
      application/
      infrastructure/
      presentation/
  shared/
    config/
    db/
alembic/
```

## Levantar entorno

1. Construir y levantar servicios:

```bash
docker compose up --build -d
```

2. Ejecutar migraciones:

```bash
docker compose exec api alembic upgrade head
```

3. Probar API:

- Health: `GET http://localhost:8000/health`
- Elevation sources: `GET http://localhost:8000/elevation/sources`

## Notas sobre rasters (recomendacion inicial)

Para los raster DEM, una estrategia inicial pragmatica es:

- Guardar metadatos e indices espaciales en PostGIS.
- Guardar archivos raster en almacenamiento de objetos (S3/MinIO) o filesystem versionado.
- Persistir en PostgreSQL solo referencia (`source_url`), SRID, bounding box y atributos de ingesta.

Cuando el flujo crezca, puedes evaluar `raster2pgsql` y PostGIS Raster para cargas completas en base de datos.
