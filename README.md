# Tyk

[![Python 3.13](https://img.shields.io/badge/Python-3.13-green)](https://docs.python.org/3.13/)
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
- [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
- [HTTPX](https://www.python-httpx.org/)
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

The project follows Clean Architecture principles, keeping its core business logic
independent of delivery mechanisms, persistence, and external systems. See the
[Architecture](docs/ARCHITECTURE.md) for details.

## Configuration

The project is configured through environment variables. Use .env.template as a
starting point and adjust the values for your environment.

| Variable            | Description                                                                                                                                                                                                                                                         |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `APP_DEBUG`         | Enables [FastAPI](https://fastapi.tiangolo.com/) debug mode.                                                                                                                                                                                                        |
| `APP_TITLE`         | Application title shown in the API documentation.                                                                                                                                                                                                                   |
| `APP_VERSION`       | Application version shown in the API documentation.                                                                                                                                                                                                                 |
| `APP_DESCRIPTION`   | Application description shown in the API documentation.                                                                                                                                                                                                             |
| `LOG_LEVEL`         | Minimum log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.                                                                                                                                                                                              |
| `PUBLIC_BASE_URL`   | Public base URL for generated short links, e.g. `https://tyk.example`; the app appends `/r/{short_code}`.                                                                                                                                                           |
| `DATABASE_URL`      | [PostgreSQL](https://www.postgresql.org/docs/18/) connection URL for the app and [Alembic](https://alembic.sqlalchemy.org/en/latest/); [Docker Compose](https://docs.docker.com/compose/) builds it from `DATABASE_NAME`, `DATABASE_USER`, and `DATABASE_PASSWORD`. |
| `DATABASE_NAME`     | [PostgreSQL](https://www.postgresql.org/docs/18/) database name used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                         |
| `DATABASE_USER`     | [PostgreSQL](https://www.postgresql.org/docs/18/) user used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                                  |
| `DATABASE_PASSWORD` | [PostgreSQL](https://www.postgresql.org/docs/18/) password used by [Docker Compose](https://docs.docker.com/compose/).                                                                                                                                              |

## Quick Start

Prerequisites: [Docker](https://docs.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

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

Both fields are required. Set `expires_at` to `null` for a link without
expiration, or provide a future ISO 8601 timestamp with a timezone.

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

Prerequisites: [Git](https://git-scm.com/), [Python 3.13+](https://docs.python.org/3.13/), [uv](https://docs.astral.sh/uv/), and a running [PostgreSQL](https://www.postgresql.org/docs/18/) instance with an existing
database and user.

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

3. Update `.env` to match your [PostgreSQL](https://www.postgresql.org/docs/18/) connection and local server address.
   For the default local setup:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tyk
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

Code quality is maintained through:

- [Black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) for code formatting
- [Flake8](https://flake8.pycqa.org/en/latest/) and its plugins for linting and security checks
- [mypy](https://mypy.readthedocs.io/en/stable/) in strict mode for static type checking
- [pytest](https://docs.pytest.org/en/stable/) and [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) with a 100% coverage requirement
- [pre-commit](https://pre-commit.com/) hooks for automated checks before commits

## Testing

The test suite uses [pytest](https://docs.pytest.org/en/stable/) for unit and
integration tests. Install the development dependencies before running it:

   ```bash
   uv sync
   ```

Unit tests run by default and do not require external infrastructure:

   ```bash
   uv run pytest
   ```

Integration tests require a running
[PostgreSQL](https://www.postgresql.org/docs/18/) instance configured through
`DATABASE_URL`. The database user must have permission to create and drop
databases because each test session uses an isolated temporary database.

Run the complete test suite with:

   ```bash
   uv run pytest -m "integration or not integration"
   ```

The project enforces 100% test coverage, including branch coverage.

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
