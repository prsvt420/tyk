# Tyk

[![Python 3.13](https://img.shields.io/badge/Python-3.13-green)](https://docs.python.org/3.13/)
[![CI](https://github.com/prsvt420/tyk/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/prsvt420/tyk/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/github/license/prsvt420/tyk)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/prsvt420/tyk?branch=main&color=green)](https://github.com/prsvt420/tyk/commits/main)

## About

Tyk is a high-performance URL shortening service built to handle large volumes of link creation and redirect traffic.

## Features

- URL shortening
- Expiring links
- Fast redirects

## Technology Stack

- [Python 3.13](https://docs.python.org/3.13/)
- [python-json-logger](https://nhairs.github.io/python-json-logger/latest/)
- [AnyIO](https://anyio.readthedocs.io/en/stable/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [PostgreSQL 18](https://www.postgresql.org/docs/18/)
- [SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/)
- [asyncpg](https://magicstack.github.io/asyncpg/current/)
- [Redis](https://redis.io/docs/latest/)
- [redis-py](https://redis.io/docs/latest/develop/clients/redis-py/)
- [hiredis](https://github.com/redis/hiredis-py)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
- [HTTPX](https://www.python-httpx.org/)
- [Locust](https://docs.locust.io/en/stable/)
- [mypy](https://mypy.readthedocs.io/en/stable/)
- [Black](https://black.readthedocs.io/en/stable/)
- [isort](https://isort.readthedocs.io/en/latest/)
- [Flake8](https://flake8.pycqa.org/en/latest/)
- [pre-commit](https://pre-commit.com/)
- [uv](https://docs.astral.sh/uv/)
- [Commitizen](https://commitizen-tools.github.io/commitizen/)
- [git-cliff](https://git-cliff.org/docs/)
- [Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Architecture

The project follows [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) principles, keeping its core business logic
independent of delivery mechanisms, persistence, and external systems. See the
[Architecture](ARCHITECTURE.md) for details.

## Configuration

The project is configured through environment variables. Use .env.template as a
starting point and adjust the values for your environment.

| Variable                        | Description                                                                                                                                                                                                                                                         |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `APP_DEBUG`                     | Enables [FastAPI](https://fastapi.tiangolo.com/) debug mode.                                                                                                                                                                                                        |
| `APP_TITLE`                     | Application title shown in the API documentation.                                                                                                                                                                                                                   |
| `APP_VERSION`                   | Application version shown in the API documentation.                                                                                                                                                                                                                 |
| `APP_DESCRIPTION`               | Application description shown in the API documentation.                                                                                                                                                                                                             |
| `LOG_LEVEL`                     | Minimum log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.                                                                                                                                                                                              |
| `PUBLIC_BASE_URL`               | Public base URL for generated short links, e.g. `https://tyk.example`; the app appends `/r/{short_code}`.                                                                                                                                                           |
| `CACHE_URL`                     | [Redis](https://redis.io/docs/latest/) connection URL for short link caching, e.g. `redis://localhost:6379/0`. The server must be reachable from the application.                                                                                                   |
| `CACHE_SHORT_LINK_TTL_SECONDS`  | Time to live for cached short links, in seconds. Default: `86400` (24 hours); must be greater than `0`.                                                                                                                                                             |
| `CACHE_CONNECT_TIMEOUT_SECONDS` | Cache connection timeout in seconds. Default: `0.5`; must be greater than `0`.                                                                                                                                                                                      |
| `CACHE_SOCKET_TIMEOUT_SECONDS`  | Timeout for cache socket reads and writes, in seconds. Default: `0.2`; must be greater than `0`.                                                                                                                                                                    |
| `DATABASE_URL`                  | [PostgreSQL](https://www.postgresql.org/docs/18/) connection URL for the app and [Alembic](https://alembic.sqlalchemy.org/en/latest/); [Docker Compose](https://docs.docker.com/compose/) builds it from `DATABASE_NAME`, `DATABASE_USER`, and `DATABASE_PASSWORD`. |
| `DATABASE_NAME`                 | [PostgreSQL](https://www.postgresql.org/docs/18/) database name used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                         |
| `DATABASE_USER`                 | [PostgreSQL](https://www.postgresql.org/docs/18/) user used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                                  |
| `DATABASE_PASSWORD`             | [PostgreSQL](https://www.postgresql.org/docs/18/) password used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                              |

Cache timeouts limit individual connection and socket I/O stages; they do
not set a total HTTP request deadline.

## Quick Start

Prerequisites: [Docker](https://docs.docker.com/) and
[Docker Compose](https://docs.docker.com/compose/).

1. Clone the repository:

   ```bash
   git clone https://github.com/prsvt420/tyk.git
   cd tyk
   ```

2. Create the environment file:

   ```bash
   cp .env.template .env
   ```

3. Build and start the application:

   ```bash
   docker compose up --build
   ```

The API will be available at `http://127.0.0.1:8000`. See the interactive
[API documentation](http://127.0.0.1:8000/docs) for available endpoints.

## Usage

After completing [Quick Start](#quick-start), open another [Bash](https://www.gnu.org/software/bash/manual/) terminal. The examples use the default local configuration.

Create a short link with [curl](https://curl.se/docs/manpage.html):

   ```bash
   curl -X 'POST' \
     'http://127.0.0.1:8000/api/v1/short-links' \
     -H 'accept: */*' \
     -H 'Content-Type: application/json' \
     -d '{
     "original_url": "https://yandex.ru/",
     "expires_at": "2030-01-01T00:00:00Z"
   }'
   ```

Only `original_url` is required. Omit `expires_at` or set it to `null` for a
link without expiration. To set an expiration, provide a future ISO 8601
timestamp with a timezone.

The API returns `201 Created`. Example response body:

   ```json
   {
     "id": "cbf62a60-4ac7-4a1d-af11-e855726bd179",
     "original_url": "https://yandex.ru/",
     "short_code": "DFFGW6F",
     "short_link_url": "http://127.0.0.1:8000/r/DFFGW6F",
     "created_at": "2026-10-21T06:24:09.452018Z",
     "expires_at": "2030-01-01T00:00:00Z"
   }
   ```

The ID, short code, and creation time are generated for each request. The
`Location` response header contains the same URL as `short_link_url`.

Use the actual `short_link_url` from your response in the commands below;
`DFFGW6F` is only an example.

Inspect the redirect response:

   ```bash
   curl --include http://127.0.0.1:8000/r/DFFGW6F
   ```

The API returns `307 Temporary Redirect` with the original URL in `Location`:

   ```http
   HTTP/1.1 307 Temporary Redirect
   location: https://yandex.ru/
   ```

Open the short link in a browser, or follow the redirect with [curl](https://curl.se/docs/manpage.html):

   ```bash
   curl --location http://127.0.0.1:8000/r/DFFGW6F
   ```

## Local Development

Prerequisites: [Git](https://git-scm.com/),
[Python 3.13+](https://docs.python.org/3.13/),
[uv](https://docs.astral.sh/uv/), a running
[PostgreSQL](https://www.postgresql.org/docs/18/) instance with an existing
database and user, and a running [Redis](https://redis.io/docs/latest/)
instance. Both services must be accessible from your host.

The current [Compose](https://docs.docker.com/compose/) configuration does not publish the [PostgreSQL](https://www.postgresql.org/docs/18/) port to the
host. For this workflow, use a [PostgreSQL](https://www.postgresql.org/docs/18/) instance accessible from your host.

Follow these steps to run the application locally:

1. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/prsvt420/tyk.git
   cd tyk
   ```

2. Create the environment file if you have not already done so:

   ```bash
   cp .env.template .env
   ```

3. Update `.env` to match your [PostgreSQL](https://www.postgresql.org/docs/18/) connection, [Redis](https://redis.io/docs/latest/) connection and local server address.
   For the default local setup:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tyk
   CACHE_URL=redis://localhost:6379/0
   PUBLIC_BASE_URL=http://127.0.0.1:8000
   ```

   Local runs use `DATABASE_URL` directly. `DATABASE_NAME`, `DATABASE_USER`, and
   `DATABASE_PASSWORD` configure [Docker Compose](https://docs.docker.com/compose/).

4. Install the application and development dependencies:

   ```bash
   uv sync
   ```

5. Apply database migrations:

   ```bash
   uv run alembic upgrade head
   ```

6. Start the development server:

   ```bash
   uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

The API will be available at `http://127.0.0.1:8000`. See the interactive
[API documentation](http://127.0.0.1:8000/docs) for available endpoints.

## Code Quality

The codebase follows clean code principles, including clear naming, small
focused components, explicit dependencies, and separation of concerns.

See [Code Style](CODE_STYLE.md) for programming principles and coding
conventions.

Code quality is maintained through:

- [Black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) for code formatting
- [Flake8](https://flake8.pycqa.org/en/latest/) and its plugins for linting and security checks
- [mypy](https://mypy.readthedocs.io/en/stable/) in strict mode for static type checking
- [pytest](https://docs.pytest.org/en/stable/) and [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) with a 100% coverage requirement
- [pre-commit](https://pre-commit.com/) hooks for automated checks before commits
- [GitHub Actions](https://docs.github.com/en/actions) for automated checks on pull requests and pushes to `main`

## Testing

Unit and integration tests use [pytest](https://docs.pytest.org/en/stable/).
Load tests use [Locust](https://docs.locust.io/en/stable/) and run separately;
see [Load Testing](#load-testing). Install the development dependencies
before running tests:

   ```bash
   uv sync
   ```

By default, [pytest](https://docs.pytest.org/en/stable/) runs all unit and
integration tests with coverage.
Integration tests require a running [PostgreSQL](https://www.postgresql.org/docs/18/) instance configured through
`DATABASE_URL`. The database user must be able to connect to the `postgres` database and create and drop databases because each test session uses an isolated temporary database.

Run all unit and integration tests with:

   ```bash
   uv run pytest
   ```

To run only unit tests without a running database:

   ```bash
   uv run pytest -m "not integration"
   ```

Valid application settings, including `DATABASE_URL` and `CACHE_URL`, are
still required.
Unit tests replace [Redis](https://redis.io/docs/latest/) operations with
mocks, so they do not require a running cache server.

The [pre-commit](https://pre-commit.com/) test hook runs the full
[pytest](https://docs.pytest.org/en/stable/) suite, so
[PostgreSQL](https://www.postgresql.org/docs/18/) must also be available
when committing.

The project enforces 100% test coverage, including branch coverage.

## Load Testing

[Locust](https://docs.locust.io/en/stable/) scenarios are defined in
`tests/load/locustfile.py`. They send requests to a running application and
create records in its configured database. Redirect scenarios also read
and populate the configured [Redis](https://redis.io/docs/latest/) cache.
Use a development instance for these runs. [pytest](https://docs.pytest.org/en/stable/),
[pre-commit](https://pre-commit.com/) and the CI workflow do not run load tests.

Prepare the environment using [Local Development](#local-development),
and use this server command for load testing:

```bash
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 --workers 1
```

This starts one application worker without automatic reload. Run
[Locust](https://docs.locust.io/en/stable/) from another terminal with the
development dependencies installed.

| User class              | Behavior                                                                                                         |
|-------------------------|------------------------------------------------------------------------------------------------------------------|
| `CreateShortLinkUser`   | Creates links without expiration and checks for `201` with a non-empty string `short_code` in the JSON response. |
| `RedirectShortLinkUser` | Creates one link at startup, repeatedly requests it and checks for `307` with the expected `Location`.           |

Both classes use `constant(0)` and a five-second request timeout. Users
start the next task without an artificial pause. Redirect requests do not
follow the destination URL.

The examples below run short, 30-second scenario checks. `-u` sets the
number of users, `-r` sets the user spawn rate per second, and `-t` sets
the total run time, including the ramp-up period.

Creation only:

```bash
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8000 --headless -u 1 -r 1 -t 30s CreateShortLinkUser
```

Redirects only:

```bash
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8000 --headless -u 1 -r 1 -t 30s RedirectShortLinkUser
```

Mixed traffic, with one user of each class:

```bash
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8000 --headless -u 2 -r 2 -t 30s CreateShortLinkUser RedirectShortLinkUser
```

Equal class weights control the distribution of users; they do not
guarantee equal request rates for creation and redirects.

Each redirect user makes a setup POST, recorded as
`/api/v1/short-links (setup)`. It contributes to the aggregate statistics.
Read redirect measurements from the GET `/r/{short_code}` row separately.

### Reports

Save each run under `tests/load/results/<version>/<scenario>/<run>/`, for example
`tests/load/results/v0.1.0/create/run-01/`. Use a separate directory for each repeat.
Add these options to the selected [Locust](https://docs.locust.io/en/stable/)
command to save reports:

- `--html tests/load/results/v0.1.0/create/run-01/locust_report.html` saves an HTML report.
- `--csv tests/load/results/v0.1.0/create/run-01/locust` sets the prefix for CSV files.

Adjust the version, scenario and run directory for each measurement.
Record testing conditions and results in `BENCHMARKS.md`.

## Benchmarks

[Benchmarks](BENCHMARKS.md) describes the methodology and results for
short link creation, redirects and mixed traffic. It includes RPS,
response-time percentiles and failure counts, together with test
conditions and raw report locations.

## Changelog

All notable changes to the project are documented in the [Changelog](CHANGELOG.md).

## Contributing

Contributions are welcome. Please read the [Contributing](CONTRIBUTING.md)
for details on setting up the development environment and submitting changes.

## Conventional Commits

The project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Commit messages are created and validated with [Commitizen](https://commitizen-tools.github.io/commitizen/), while [git-cliff](https://git-cliff.org/) uses the structured commit history to generate the changelog.

## Code of Conduct

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before contributing to the project.

## Contact

For questions, feedback, or general support, open an [issue](https://github.com/prsvt420/tyk/issues) or contact the maintainer [@prsvt420](https://github.com/prsvt420).

## Security

To report a security vulnerability, please follow the instructions in the [Security Policy](SECURITY.md).

## License

This project is licensed under the terms of the [MIT License](LICENSE).
