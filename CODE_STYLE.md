# Code Style

This guide describes the programming principles and coding conventions used
in the project. Apply them when adding or changing code. Architectural
responsibilities and runtime behavior are documented in
[Architecture](ARCHITECTURE.md).

The automated rules come from [pyproject.toml](pyproject.toml) and
[pre-commit configuration](.pre-commit-config.yaml). The remaining guidance
describes the design and readability decisions to consider during review.

## Programming Principles

Clean Code in this project means clear intent, focused responsibilities and
explicit effects.

### Readability

Write code whose purpose, inputs and effects are clear to the reader.
Use domain vocabulary and names that describe the responsibility, such as
`short_link_repository` and `is_expired`. Prefer keyword arguments when
they make a call easier to understand.

### KISS and YAGNI

Keep It Simple (KISS): choose the simplest clear solution that satisfies
the requirement. For example, a route handler can validate and map input,
call a use case and construct the response.

You Aren't Gonna Need It (YAGNI): introduce features and extension points
for concrete needs. A repository interface supports storage substitution
and isolated tests; a generic repository framework needs its own practical
justification.

### DRY

Don't Repeat Yourself (DRY): give shared business rules and knowledge one
authoritative definition. For example, short code validation and generation
use the same domain alphabet. Extract common behavior when the code shares
meaning and reasons to change; similar syntax alone is insufficient.

### SOLID

- Single Responsibility: give a component a coherent responsibility.
  A use case coordinates an application operation; a repository handles
  persistence.
- Open/Closed: use established extension points when replacing a
  dependency. Another repository can implement the application interface
  while the use case keeps its existing logic.
- Liskov Substitution: preserve the interface's behavior, return types,
  error semantics and supported keyword arguments. A repository lookup
  must preserve the contract for a missing link.
- Interface Segregation: keep interfaces focused on what their callers
  need. For example, a short code generator exposes generation separately
  from repository operations.
- Dependency Inversion: make application logic depend on application
  contracts. Providers choose concrete implementations and inject them
  into use cases.

### Explicit Dependencies and Side Effects

Make business dependencies visible in constructor parameters. Keep storage
access, resource ownership and other effects visible at their boundaries.
For example, the repository owns its save transaction, and a provider owns
the request session's lifetime.

### Composition

Prefer composing collaborators to reuse behavior. For example, a creation
use case receives a repository and a generator. Use inheritance where it
expresses a contract or framework requirement, as with repository
interfaces, exception hierarchies and persistence models.

## Formatting and Imports

- Use [Black](https://black.readthedocs.io/en/stable/) with the configured
  79-character target line length.
- Use [isort](https://pycqa.github.io/isort/) with the Black profile and
  the same line length. The `src` package is configured as first-party.
- Follow the configured [Flake8](https://flake8.pycqa.org/en/latest/)
  checks, including the function complexity limit of 10.
- Use double quotes for strings and docstrings, following the formatter
  and configured quote checks.
- Keep imports explicit and let the tools handle their ordering. Use
  existing package exports for public project components.
- Keep suppressions such as `# noqa` or type-checking ignores narrow and
  justified by a specific limitation.

Generated migration revisions are excluded from the configured formatting,
linting and type-checking tools. Other file checks still apply according
to their configuration.

## Naming

- Use `snake_case` for modules, functions and variables, `PascalCase` for
  classes, and `UPPER_SNAKE_CASE` for constants.
- Express business limits and meaningful algorithm settings with named
  constants in the layer that owns them. In HTTP routes, use named status
  constants such as `status.HTTP_201_CREATED`.
- Preserve established acronyms: `OriginalURL`, `ShortLinkDTO` and
  `RequestIDMiddleware`.
- Follow existing suffixes for equivalent components, such as `UseCase`,
  `DTO`, `Interface`, `Mapper`, `Schema` and `Error` in class names, and
  `_use_case`, `_value_object` or `_interface` in module names.
- Use `provide_` for dependency providers and predicate names such as
  `is_expired` or `can_redirect` where they describe the behavior.
- Prefix internal implementation details with `_` where appropriate.

## Type Annotations

The project uses [mypy](https://mypy.readthedocs.io/en/stable/) in strict
mode with the configured framework plugin and generic type checks.

- Annotate function parameters, return values and instance state. Use
  `-> None` for functions that return no value.
- Use built-in generic types such as `list[str]` and unions such as
  `ShortLink | None`. Specify collection element types.
- Add local annotations where they clarify the data being handled.
- Keep `Any`, casts and type-checking suppressions limited to boundaries
  where precise typing is impractical. Use them with a concrete reason;
  preserve the actual contract between components.

## Functions, Classes and Dependencies

- Keep functions and classes focused on a coherent task. Extract helpers
  when they clarify responsibility or reusable behavior.
- Keep domain and application logic independent of presentation and
  persistence frameworks. Follow the layer boundaries in
  [Architecture](ARCHITECTURE.md#architectural-approach-and-dependencies).
- Pass replaceable dependencies through application interfaces into use
  case constructors. Choose concrete implementations in providers or
  application assembly code.
- Introduce a focused interface when a dependency boundary needs
  substitution or isolation.
- Keep domain entities, application DTOs, request schemas and storage
  models in their respective layers. Prefer immutable value objects and
  DTOs for data that should remain unchanged after construction.
- Follow the existing dataclass conventions: value objects and DTOs use
  `@dataclass(frozen=True, slots=True, kw_only=True)`. For domain entities
  whose state may change, use `@dataclass(slots=True, kw_only=True)`.

## Asynchronous Code and Resources

- Await asynchronous dependency operations and preserve their asynchronous
  contracts, including when an implementation performs only local work.
- Use asynchronous clients for network and storage I/O. Choose an explicit
  execution strategy for blocking calls or long computations in an
  asynchronous path. An `async def` declaration alone does not make
  synchronous work non-blocking.
- Use context managers and `finally` blocks to release resources and
  restore temporary state, including on exceptions.
- Keep sessions scoped to the operation or request that owns them.
  Shared settings, engines and session factories have different lifetimes
  from individual sessions.
- Preserve transaction ownership. Callers rely on the repository's save
  contract; they should not add an unrelated commit around that operation.

## Error Handling

- Use explicit checks and exceptions for input validation and business
  rules. Do not rely on `assert` for runtime validation.
- Use specific exception types that describe the failure. Catch an error
  when handling it, translating it at a boundary or reporting it at an
  appropriate outer boundary.
- Translate recognized technical conditions when the application needs
  to handle them. Preserve the original cause, for example:
  `raise ShortCodeAlreadyExistsError() from error`.
- Let unrecognized failures propagate. Use bare `raise` when re-raising
  the active exception.
- Keep HTTP response construction and status mapping in the HTTP layer.
- Keep broad catches at boundaries that need them. For example, request
  logging middleware catches unexpected exceptions, logs them and
  re-raises them.

## Logging

Use a module-level logger:

```python
from logging import Logger, getLogger

logger: Logger = getLogger(name=__name__)
```

Keep messages readable and pass structured context through `extra`.
Use a stable `event` value in `snake_case` to identify an application event,
such as `short_link_created`. Choose the level according to the outcome
and include a traceback with `logger.exception()` inside an exception
handler when it helps diagnose the failure.

Let the shared configuration supply handlers, formatting and request
context. Log business outcomes where they occur and leave HTTP outcome
and unhandled request exception logging to middleware. Avoid recording
the same exception at every layer. Keep credentials and other secrets
out of log context and messages.

## Docstrings and Comments

- Write docstrings in English using the configured Google convention.
  Start with a short summary of the behavior or responsibility.
- Add argument, return value and error details when they explain a
  non-obvious contract. A short summary is sufficient for simple behavior.
- Module, package and constructor docstrings are optional under the
  current lint configuration.
- Use comments to explain reasons, constraints or surprising behavior.
  Remove obsolete comments and commented-out code.
