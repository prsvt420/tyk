# Architecture

## Architectural Approach and Dependencies

The project follows
[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
principles. Business rules and application use cases form the core, while
external interfaces and concrete technical implementations belong to the
outer layers.

The goal is to keep core logic independent of delivery mechanisms and
persistence libraries. This allows business rules and use cases to be
tested independently, and technical dependencies to be replaced by other
implementations of the same interfaces.

The table shows responsibilities and source dependencies between the four
main layers:

| Layer            | Responsibility                                 | Depends on                                |
|------------------|------------------------------------------------|-------------------------------------------|
| `domain`         | Business concepts and rules.                   |                                           |
| `application`    | Use cases and dependency contracts.            | `domain`                                  |
| `infrastructure` | Technical implementations and runtime support. | `application`, `domain`                   |
| `presentation`   | External interfaces and request handling.      | `application`, `domain`, `infrastructure` |

The project uses dependency injection (DI): use cases receive dependency
objects through their constructors. The constructor parameters are typed
with repository and code generator interfaces defined in `application`.

Provider functions in `presentation` explicitly choose the implementations,
create or reuse the required objects, and pass them to use case constructors.
For example, `provide_create_short_link_use_case()` passes a repository and
a short code generator into `CreateShortLinkUseCase`, whose parameters are
typed as `ShortLinkRepositoryInterface` and `ShortCodeGeneratorInterface`.

At runtime, `provide_short_link_repository()` creates a
`PostgreSQLShortLinkRepository` for the request and wraps it in
`RedisCachedShortLinkRepository`. The wrapper implements the same repository
interface and receives the shared asynchronous Redis client. Use cases
access caching through the existing repository contract.

The choice and construction of infrastructure objects stay outside use case
logic. Another implementation or a test double that satisfies the same
interface can be supplied without changing the use case.

The presentation layer also uses infrastructure's request context storage.

## Project Structure

The main directories are organized by responsibility:

| Path                  | Responsibility        |
|-----------------------|-----------------------|
| `src/domain/`         | Domain Layer.         |
| `src/application/`    | Application Layer.    |
| `src/infrastructure/` | Infrastructure Layer. |
| `src/presentation/`   | Presentation Layer.   |
| `src/config/`         | Configuration.        |
| `tests/`              | Tests.                |
| `alembic/`            | Database migrations.  |
| `scripts/`            | Auxiliary scripts.    |
| `.github/workflows/`  | GitHub Workflows.     |

## Asynchronous Execution

The application uses asynchronous request handling, database I/O and cache I/O.
Route handlers await application use cases, which await repository
operations through asynchronous interfaces.

The database adapter uses
[SQLAlchemy](https://docs.sqlalchemy.org/en/20/)'s asynchronous engine and
sessions with the [asyncpg](https://magicstack.github.io/asyncpg/current/)
driver. Cache operations use the asynchronous client from
[redis-py](https://redis.io/docs/latest/develop/clients/redis-py/).

When an awaited I/O operation suspends a request task, the event loop can
run other ready tasks. This allows concurrent request handling while
database and cache operations are waiting for I/O.

Validation, data mapping, short code generation and logging remain
synchronous. Declaring a function with `async def` does not automatically
move its work to another thread or make synchronous operations non-blocking.

## Domain Model and Business Rules

`ShortLink` is the domain entity. `OriginalURL` and `ShortCode` are immutable
value objects that validate their values on construction. Domain validation
applies when creating links and when rebuilding entities from stored data,
independently of request schema validation.

- `OriginalURL` requires an `http` or `https` scheme and a non-empty URL
  authority component (`netloc`).
- `ShortCode` accepts 4 to 32 characters from `0-9`, `A-Z` and `a-z`.
  Letter case is preserved and significant in the value object.
- `created_at` and a supplied `expires_at` must be timezone-aware. The
  entity normalizes both values to UTC.
- `expires_at=None` means no expiration. A supplied expiration must be
  strictly later than `created_at`.

A link is expired when `expires_at <= now`; equality already means the
link has expired. The check uses the current UTC time by default. An
expired link remains a valid domain entity, but the redirect use case
rejects it.

## Main Scenarios

### Creating a Short Link

1. The client sends `POST /api/v1/short-links` with `original_url` and an
   optional `expires_at`. Omitting `expires_at` or passing `null` creates
   a link without an expiration time.
2. The request schema validates the input. The route handler converts it
   into `CreateShortLinkDTO` and calls `CreateShortLinkUseCase`.
3. The use case validates domain values, obtains a candidate code from the
   generator and creates a `ShortLink` entity.
4. The caching repository delegates saving to the PostgreSQL repository,
   which maps the entity to a storage model and saves it in a transaction.
   After a successful commit, the use case returns the link as
   `ShortLinkDTO`.
5. The route handler builds `short_link_url` from `PUBLIC_BASE_URL` and
   `/r/{short_code}`. It returns `201 Created` with the link data in JSON
   and the same public URL in the `Location` header.

The full public URL is assembled in the presentation layer from settings;
it is not derived from the incoming request or stored with the link.
Collision retries are described in
[Collisions and Concurrent Requests](#collisions-and-concurrent-requests).

### Redirecting a Short Link

1. The client sends `GET /r/{short_code}`. The route handler passes the
   code to `GetShortLinkByShortCodeUseCase`.
2. The use case validates the code as `ShortCode` and asks the repository
   for the link. The repository first checks Redis. A cache hit is mapped
   to a domain entity; a miss loads the link from PostgreSQL and caches a
   found entity.
3. The use case checks that the link exists and has not expired, then
   returns it as `ShortLinkDTO`.
4. The route handler returns `307 Temporary Redirect` with `original_url`
   in the `Location` header. The client follows this address.

The application does not fetch the original URL or check the destination's
availability. Expiration is checked when resolving the code; this check
does not delete the stored link. Failed scenarios are described in
[Error Handling](#error-handling).

## Data Storage

Runtime persistence uses
[PostgreSQL](https://www.postgresql.org/docs/18/) through
`PostgreSQLShortLinkRepository`, which implements the application's
`ShortLinkRepositoryInterface`. Links are stored in the `short_links` table.

| Field          | Meaning                                                    |
|----------------|------------------------------------------------------------|
| `id`           | UUID primary key generated by the application.             |
| `original_url` | Original destination URL stored as text.                    |
| `short_code`   | Unique code used to look up the link.                       |
| `created_at`   | Creation time assigned by the application.                  |
| `expires_at`   | Optional expiration time; `NULL` means no expiration.       |

The domain entity normalizes timestamps to UTC, and the database uses
timezone-aware timestamp columns. A database constraint requires a non-null
`expires_at` to be later than `created_at`.

### Short Link Caching

`RedisCachedShortLinkRepository` adds caching around the persistent
repository using [Redis](https://redis.io/docs/latest/). It reads keys in the
`short_link:{short_code}` format. A found key supplies the link directly;
when the key is absent, the wrapper queries the persistent repository and
caches the returned entity. An absent link returns `None` without a cache
entry. Saving delegates to the persistent repository; cache entries are
populated during reads.

Each cache entry contains the complete entity as JSON. Its time to live
(TTL) is configured through `CACHE_SHORT_LINK_TTL_SECONDS`, with a default
of 86,400 seconds, or 24 hours, from its cache write. The provider passes
this value to the caching repository through its constructor.
Cache hits do not renew the TTL. This duration is independent of
`expires_at`: the use case checks link expiration after either lookup
path. Expiration of a cache key does not delete the stored database record.

If a Redis read raises `RedisError`, the wrapper logs a warning and returns
the result from the persistent repository without another cache operation
for that request. If writing a cache entry raises `RedisError`, it logs a
warning and returns the entity already loaded from the persistent repository.
Warnings include the short code, a read or write failure event and the
exception traceback. Errors from the persistent repository and errors while
rebuilding cached entities propagate through the existing exception handling.

### Data Representations

`ShortLink` is the domain entity and enforces business rules through its
own validation and value objects. `ShortLinkModel` defines the
[SQLAlchemy](https://docs.sqlalchemy.org/en/20/) mapping to the database.
`ShortLinkModelMapper` converts between these representations, rebuilding
the domain entity and its value objects when loading a record.

`ShortLinkCacheMapper` converts a domain entity to a JSON string and back.
The cached representation stores the UUID, URL, code and timezone-aware
timestamps as strings, with `null` for an omitted expiration. Loading it
rebuilds the UUID, datetimes and value objects through the domain entity's
normal validation.

The repository accepts and returns domain entities. Application use cases
convert results to `ShortLinkDTO` through `ShortLinkMapper`. Request and
response schemas define the external representation in the presentation
layer. Storage models stay inside infrastructure, so persistence details
do not become part of the use case contract.

### Sessions and Transactions

Each request that needs a repository receives its own asynchronous session
and repository instance. Sessions are created from the shared session
factory and closed when the dependency context exits. Connections are
acquired from the engine's pool on demand and released during cleanup.

The Redis client is shared across requests. A cache hit returns before the
PostgreSQL repository is queried, so the request's session does not execute
a database query on that path.

Each PostgreSQL `save()` call owns a transaction: it adds and flushes the
storage model, then commits on successful exit from the transaction block
or rolls back if the block fails. The save transaction completes before
the repository returns to the use case.

The PostgreSQL repository's `get_by_short_code()` queries by code and returns
a domain entity or `None`. Session cleanup also ends any transaction left
open by a database read.
Conflict handling is described in
[Collisions and Concurrent Requests](#collisions-and-concurrent-requests).

## Collisions and Concurrent Requests

A collision occurs when a generated `short_code` is already stored,
including when concurrent requests generate the same candidate. Uniqueness
is enforced during saving.

The runtime uses `RandomShortCodeGenerator`, which generates 7-character
candidates by default. Each character is selected with `secrets.choice`
from the domain's `SHORT_CODE_ALPHABET`. Generation is independent of the
original URL and can produce an already used candidate.

The runtime relies on the `uq_short_links_short_code` unique constraint in
[PostgreSQL](https://www.postgresql.org/docs/18/). Creation attempts an insert
directly. The constraint prevents two stored links from sharing a code
across concurrent requests and application processes using the same database.

The creation use case handles collisions as follows:

1. Generate a candidate code, create a new link entity and attempt to save
   it in a transaction.
2. If the short code uniqueness constraint rejects the insert, the
   transaction is rolled back and the repository raises
   `ShortCodeAlreadyExistsError`.
3. Generate another candidate and repeat the save attempt. The first
   successful save commits the link and completes the use case.

`MAX_SHORT_CODE_GENERATION_ATTEMPTS` bounds the total number of generation
and save attempts, including the first. The current limit is 10; exhausting
it raises `ShortCodeGenerationError`. Only recognized short code conflicts
trigger another attempt. Other generation, validation and storage errors
propagate to the caller.

Creation treats each request as a separate operation, so the same
`original_url` can have multiple short links. The uniqueness rule applies
to `short_code`.

## Error Handling

Domain errors inherit from `DomainError` and represent invalid business
values or states. Application errors inherit from `ApplicationError` and
represent use case outcomes. Custom technical errors inherit from
`InfrastructureError`. These exception hierarchies are independent of HTTP;
native library errors retain their types unless explicitly translated.

Infrastructure adapters translate recognized technical conditions into
application errors when a use case needs to handle them. For example, a
short code uniqueness conflict becomes `ShortCodeAlreadyExistsError`, with
the original exception preserved as its cause. Other repository errors
propagate unchanged. Transaction boundaries and conflict retries are
described in [Sessions and Transactions](#sessions-and-transactions) and
[Collisions and Concurrent Requests](#collisions-and-concurrent-requests).

Request schemas validate input structure and types, while domain objects
enforce business rules independently of HTTP. Request validation uses the
standard [FastAPI](https://fastapi.tiangolo.com/) handling. The HTTP layer
maps selected errors to responses; route handlers can apply a specific
mapping before an exception reaches the shared domain error handler.

| Condition                                                             | HTTP status | Handled by                   |
|-----------------------------------------------------------------------|-------------|------------------------------|
| Request validation failure                                            | `422`       | Framework validation handler |
| `DomainError` without route-specific handling                         | `422`       | Shared domain error handler  |
| `InvalidShortCodeError` or `ShortLinkNotFoundError` during a redirect | `404`       | Redirect route handler       |
| `ShortLinkExpiredError` during a redirect                             | `410`       | Redirect route handler       |
| Readiness check reports that the application is not ready             | `503`       | Probe route handler          |

Request validation responses contain a list of errors in `detail`. The
shared domain error handler and redirect handler use a string in `detail`.
The readiness probe uses `status`, returning `not_ready` for a negative
check result. Recognized check failures and timeouts produce this result;
unexpected exceptions follow the standard server error handling.

Response validation failures, unexpected request exceptions and unmapped
application errors, including `ShortCodeGenerationError`, are logged by
`RequestLoggingMiddleware` and reach the framework's default server error
handling. A `500` response is produced if the HTTP response has not started.
Its default body is plain text; `APP_DEBUG=true` enables traceback responses.

Settings validation and dependency configuration run during module
initialization. Errors such as `ShortCodeGeneratorError` for an invalid code
length can stop application loading before HTTP handlers are available.

## Initialization and Lifecycle

The server loads the exported `app` from `src/main.py`.
The application lifecycle consists of the following stages:

1. Module initialization. Settings are loaded and validated, and the
   database engine, session factory, Redis client and short code generator
   are created when their modules are first imported. These objects are
   shared within the process and reused across calls to `create_app()`.
   Database and Redis connections are acquired from their pools on demand.
2. Application creation. `create_app()` configures logging, creates the
   [FastAPI](https://fastapi.tiangolo.com/) application with its settings and
   `lifespan` handler, and registers routes, middleware and the domain error
   handler. The returned application is exported as `app`.
3. Startup. The server enters `lifespan`, which records the start time
   and logs the `app_started` event.
4. Shutdown. The `finally` block in `lifespan` sequentially disposes the
   shared database engine's connection pool and closes the Redis client,
   then logs `app_stopped` with the application uptime in `uptime_seconds`.

## Logging

Logging is configured centrally for the running application and its server.
Logs are written to standard output in JSON format.
Each log entry includes a UTC `timestamp`, `level`, `logger` and `message`.
`LOG_LEVEL` controls the application and server logging levels. Library
loggers have separate thresholds to limit noise.

Application events use an `event` field to identify the action independently
of the human-readable `message`. Logged events cover HTTP requests,
application startup and shutdown, and use case outcomes such as
`short_link_created`.

`RequestLoggingMiddleware` centralizes HTTP request outcome logging.
It starts a monotonic timer before invoking the wrapped application and
captures the outgoing response status code. The `duration_ms` field measures
the wrapped application call in milliseconds.
Non-HTTP scopes pass through without HTTP request logging.

When the application call returns, the middleware writes an
`http_request_completed` event at `INFO`. Handled error responses follow the
same path. Unhandled exceptions caught by the middleware produce an
`http_request_failed` event at `ERROR`, including `exception_type` and a
traceback, and are then propagated. Both outcome records include the HTTP
method, path, status code and `duration_ms`.

`RequestIDMiddleware` generates a new identifier for each HTTP request.
It stores the identifier in a `ContextVar`, and a logging filter adds it as
`request_id` to records emitted within that request's context. The middleware
restores the previous context value when processing ends, including on
exceptions. Logs outside a request context omit `request_id`. Responses
passing through the middleware include it in the `X-Request-ID` header,
allowing a response to be matched to its log entries.

Within the user middleware stack, `RequestIDMiddleware` wraps
`RequestLoggingMiddleware`, making the request context available while
request outcomes and use case events are logged.

## Health Checks

The application exposes HTTP probes for liveness and readiness checks.

| Endpoint      | Purpose                                                                          | Response                                |
|---------------|----------------------------------------------------------------------------------|-----------------------------------------|
| `GET /livez`  | Confirms that the HTTP application responds, independently of dependency health. | `200`                                   |
| `GET /readyz` | Reports readiness to serve traffic based on the application's readiness checks.  | `200` when ready; `503` when not ready. |

Readiness is determined by the application's checks of required resources
and dependencies. The HTTP layer exposes the resulting readiness status.

Successful startup does not by itself establish readiness. Readiness is
evaluated when its probe is called; a negative result changes the probe
response without disabling other application routes.
