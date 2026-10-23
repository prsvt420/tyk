# Contributing

Contributions to Tyk are welcome. Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
when participating in the project. Report suspected vulnerabilities through
the process described in the [Security Policy](SECURITY.md).

## Issues and Suggestions

Search existing issues before opening a new report. When reporting a bug,
include:

- minimal steps to reproduce the problem;
- the expected and actual behavior;
- the affected version or commit;
- relevant environment and configuration details.

For a feature request, describe the problem and the expected outcome.
Include a proposed approach when it helps explain the request.

## Development Setup

Follow [Local Development](README.md#local-development) to prepare the
environment, configure application settings and apply database migrations.
Run the commands below from the repository root.

Install application and development dependencies from the lock file with
[uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked
```

Tests require valid application settings, including `DATABASE_URL`.
Integration tests also require a reachable
[PostgreSQL](https://www.postgresql.org/docs/18/) instance. The database user
must be able to connect to the `postgres` database and create and drop
databases; the tests create an isolated temporary database for each session.
See [Testing](README.md#testing) for details.

## Git Hooks

Install both [pre-commit](https://pre-commit.com/) hook types:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

The `pre-commit` hook runs the configured file checks, formatting, linting,
type checking and tests. The `commit-msg` hook validates commit
messages with [Commitizen](https://commitizen-tools.github.io/commitizen/).
Both are configured in `.pre-commit-config.yaml`.

The test hook always runs the full [pytest](https://docs.pytest.org/en/stable/)
suite, including integration tests, so
[PostgreSQL](https://www.postgresql.org/docs/18/) must also be available
when committing documentation changes.
If a formatter changes files, review the changes and stage them again
before retrying the commit.

## Making Changes

- Keep changes focused on the problem being addressed.
- Follow [Code Style](CODE_STYLE.md) and the layer boundaries described in
  [Architecture](ARCHITECTURE.md).
- Add or update tests for changed behavior, including relevant error paths.
  The project requires 100% coverage of statements and branches in `src`.
- Update documentation when behavior, configuration or development
  instructions change.
- Keep `pyproject.toml` and `uv.lock` consistent when changing dependencies.
- Include an [Alembic](https://alembic.sqlalchemy.org/en/latest/) revision
  when changing the persisted schema. Review generated revisions and
  verify that the migrations apply to a development database.

## Running Checks

Run the configured checks against all tracked files before submitting
changes:

```bash
uv run pre-commit run --all-files
```

This command includes the full [pytest](https://docs.pytest.org/en/stable/)
suite. To run it separately:

```bash
uv run pytest
```

For a unit-test-only run without a running database:

```bash
uv run pytest -m "not integration"
```

Valid application settings are still required. Run all unit and integration
tests before submitting changes.

The [GitHub Actions](https://docs.github.com/en/actions) workflow in
`.github/workflows/ci.yaml` installs locked dependencies, applies migrations,
runs `alembic check` and runs `pre-commit run --all-files` for pull requests
and pushes to `main`.

The `commit-msg` check runs separately when creating a commit; the command
above and the CI workflow do not validate commit messages.

## Load Testing

Load tests use [Locust](https://docs.locust.io/en/stable/) and run separately
against a running application and its configured database.
[pytest](https://docs.pytest.org/en/stable/),
[pre-commit](https://pre-commit.com/) and the CI workflow do not execute
these scenarios.
See [Load Testing](README.md#load-testing) for the available user classes,
commands and report options.

When adding or changing a scenario, validate the expected response and
group dynamic request paths under stable names in the statistics. Account
for setup requests when interpreting the results.

Save reports under `tests/load/results/<version>/<scenario>/<run>/`.
Keep a separate `README.md` alongside the reports to record testing
information.

## Commit Messages

Use English commit messages following
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
type(scope): description
```

Common types include `feat`, `fix`, `refactor`, `perf`, `test`, `docs`,
`build`, `ci` and `chore`. Write a short description in the imperative,
such as `add`, `fix`, `configure` or `clarify`.

Choose a scope that identifies the affected area, such as `links`, `http`,
`app`, `logging`, `database` or `project`. For tooling changes, use the
tool name when appropriate, such as `pre-commit` or `mypy`. For
documentation, use the document name, such as `readme`, `architecture`,
`code-style` or `contributing`.

Examples:

```text
feat(links): add short link retrieval use case
test(http): add endpoint tests
docs(contributing): add contribution guidelines
```

Mark incompatible changes with `!` before the colon or a
`BREAKING CHANGE:` footer. Explain the compatibility impact and any
required migration steps. For example:

```text
feat(links)!: change short link response format
```

Stage the intended changes with Git, then use Commitizen to compose a
commit interactively:

```bash
uv run cz commit
```

You can also write the message with `git commit`; the installed
`commit-msg` hook applies the same validation. To check a proposed message
without creating a commit:

```bash
uv run cz check --message "docs(contributing): add contribution guidelines"
```

## Versioning

The project version is defined in `[project].version` in `pyproject.toml`.
Commitizen uses the `uv` version provider to update that value and the
project's version in `uv.lock`. It also updates the files listed in
`version_files`: `src/config/app_settings.py` and `.env.template`.

Inspect the current project version with:

```bash
uv run cz version --project
```

Version tags follow the `v$version` format, for example `v0.1.0`. The
`major_version_zero` setting keeps the major version at zero during initial
development.

Version changes are part of release preparation. For the first release,
tag the reviewed commit with the version already declared in the project.
For later releases, Commitizen can calculate a version bump from commit
history; see its [bump documentation](https://commitizen-tools.github.io/commitizen/commands/bump/).
A normal `cz bump` updates version files, creates a commit and creates a
local tag. Prepare it in a clean working tree.

Review version references outside the configured files as well. In
particular, the application image tags in `compose.yaml` are not updated
by Commitizen.

## Changelog

[git-cliff](https://git-cliff.org/docs/) generates the changelog from Git
history using the configuration in `pyproject.toml`. The configuration
includes Conventional Commits and filters out messages that do not follow
that format.

Generate or update `CHANGELOG.md` from the committed history with:

```bash
uv run git-cliff --config pyproject.toml --output CHANGELOG.md
```

Review the generated changes before committing them. Release tags divide
the history into versions; commits after the latest tag appear as
unreleased changes.

Commitizen's `update_changelog_on_bump` is disabled. Changelog generation is
handled separately by git-cliff during release preparation.

## Pull Requests

Create a branch from the latest `main`. If you do not have write access
to this repository, work in a fork. Open a pull request from your branch
against this repository's `main` branch. Include:

- the problem being addressed and the resulting behavior;
- related issues, when applicable;
- the checks performed and their results;
- relevant changes to configuration, schema or API behavior.

Keep the description focused on the final change and make sure the CI
checks pass.
