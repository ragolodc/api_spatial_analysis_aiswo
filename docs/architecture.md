# Arquitectura — Qué significa "hacer un buen trabajo"

> Este documento define el estándar de calidad. Los agentes revisores
> evalúan código contra este archivo. Si no está aquí, no es un requisito.

## Principios

1. **Domain-Driven Design (DDD)** El proyecto implementa el DDD. Las capas deben quedar bien claras. No introducir capas adicionales (servicios, repositorios, ORMs) hasta que haya una razón concreta documentada en `feature_list.json`.

2. **Vertical Slice Structure.** Cada _Slice_ vive dentro de `src/modules/<slice_name>`. Debe existir el mínimo acoplamiento posible entre _slices_. En caso de ser factible por cuestiones prácticas, algún acoplamiento, este debe ser siempre discutido y aprobado. 

   Notes:
   - Not all folders are mandatory in every slice.
   - Add files only when needed.
   - Keep naming consistent across slices.
   - En caso de que los ficheros se tornen execsivamente grandes, se realizará una subdivisión:

   Notes:
   - Los nombres deben ser descriptivos y reflejar la responsabilidad.

3. **SOLID.** El proyecto implementa los principios SOLID. La aplicación de este principio en caso de que no quede clara o no sea conveniente en algún contexto específico, se discute.

4. **DRY.** El proyecto implementa los principios DRY. La conveniencia de la aplicación de este principio puede discutirse y evaluerse, por razones que pueden ser prácticas.

5. **Dependencias externas.** Si una feature requiere una dependencia, primero se discute (estado `blocked`).

6. **Errores explícitos.** Las funciones que pueden fallar (id no existe, errores de validación, etc.) lanzan excepciones nombradas, no devuelven `None`.

7. **Clara separación entre domain, application, interface e infrastructure.** Se debe observar por la correcta separación entre estos elementos.

8. **Atomicidad en disco.** Toda escritura a `notes.json` se hace primero en un archivo temporal y luego `os.replace()`. Nunca dejar el archivo a medio escribir.

9. **Otros principios generales de DDD:**

   ## DDD organizacion

   ### Domain
   - Business rules and invariants.
   - No framework dependencies (FastAPI, SQLAlchemy, httpx, etc).
   - Rich domain errors and explicit value objects.

   ### Application
   - Orchestrates use cases.
   - Defines input/output DTOs.
   - Defines ports (repository/external service abstractions).
   - No concrete infrastructure logic.

   ### Interface
   - HTTP layer only.
   - Request/response schemas.
   - Input validation, mapping to use cases, error translation.

   ### Infrastructure
   - SQLAlchemy repositories, external clients, geospatial adapters.
   - Implementation of application ports.
   - No business decisions that belong to domain.

   ### Bootstrap
   - Dependency wiring per slice.
   - Factories used by routers.

   ## Dependency Rules

   Allowed direction:
   1. `presentation -> application`
   2. `application -> domain`
   3. `infrastructure -> application + domain`
   4. `bootstrap -> all layers in same slice`

   Forbidden examples:
   1. `domain -> infrastructure`
   2. `domain -> presentation`
   3. direct imports from another slice's infrastructure module

10. **Principios de Política de Acceso a Datos:**

    ## Data Access Policy (Institutionalized)

    This project uses a hybrid persistence strategy with strict boundaries.

    Policy:
    1. Each slice must declare one primary data access mode:
    - ORM-first (SQLAlchemy declarative + repository), or
    - SQL-first (explicit SQL via `text()`/query layer).
    2. Do not mix ORM entities and ad-hoc SQL in the same use case function.
    3. Cross-store analytics (PostgreSQL + ClickHouse) must be isolated behind infrastructure adapters.
    4. Migrations remain explicit in Alembic, regardless of runtime access mode.
   
    ## PR Checklist (Data Access)

    Every PR that touches persistence should pass this checklist:
    1. The slice primary data access mode is unchanged, or the change is explicitly justified.
    2. No mixed ORM + SQL flow inside a single use case body.
    3. Repository/query adapter owns persistence concerns (not interface or domain).
    4. Alembic migration is included when schema changes.
    5. Tests cover the affected persistence path (unit + interface, and integration if relevant).

## Cross-Slice Communication

1. Prefer interaction via application ports and explicit DTOs.
2. Avoid importing domain internals from another slice.
3. Shared technical concerns can live in `src/shared/`.
4. Shared business concepts should be minimized and intentionally modeled.


## Definition Of Done For New Slice

1. Domain model and invariants covered.
2. Use cases + ports defined.
3. Infrastructure adapters implemented.
4. Router + schemas documented in OpenAPI.
5. Basic tests: domain + use case + interface happy path.
6. Added to bootstrap and main app registration.
