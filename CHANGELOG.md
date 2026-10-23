## [0.1.0] - 2026-10-23

### 🚀 Features

- *(app)* Add FastAPI application factory
- *(config)* Add application settings
- *(http)* Add versioned API router
- *(links)* Add short link domain model
- *(links)* Add short link DTOs
- *(links)* Add short link repository and code generator interfaces
- *(links)* Add short link creation use case
- *(links)* Add random short code generator
- *(links)* Add in-memory short link repository
- *(links)* Add short link creation endpoint
- *(links)* Add short link retrieval use case
- *(links)* Add short link redirect endpoint
- *(links)* Enforce timezone-aware datetimes
- *(http)* Add domain exception handler
- *(app)* Add application lifespan
- *(config)* Add public base URL
- *(links)* Include short link URL in creation response
- *(http)* Add request ID tracking
- *(logging)* Add HTTP request logging
- *(links)* Log short link creation
- *(database)* Add SQLAlchemy database foundation
- *(links)* Add initial short links schema
- *(links)* Add short link model mapper
- *(links)* Add PostgreSQL short link repository
- *(operational)* Add livez endpoint
- *(operational)* Add readyz endpoint

### 🐛 Bug Fixes

- *(links)* Use valid expiration example
- *(links)* Validate expiration timezone offset
- *(links)* Prevent short code generation race
- *(env)* Provide valid development defaults
- *(links)* Make short link expiration optional

### 💼 Other

- *(project)* Configure uv Python project
- *(project)* Disable project packaging
- *(project)* Add Docker image
- *(project)* Add Docker Compose environment

### 🚜 Refactor

- *(links)* Validate short codes with allowed characters
- *(links)* Extract short link DTO mapper
- *(links)* Convert short link DTO mapper to class
- *(links)* Rename OriginalUrl to OriginalURL
- *(project)* Unify module file naming
- *(project)* Add package-level exports
- *(links)* Add explicit interface suffixes
- *(config)* Rename application settings
- *(logging)* Capitalize JSON in formatter name
- *(links)* Capitalize URL in domain error
- *(links)* Split short link schemas by contract
- *(links)* Split short link DTOs by purpose
- *(http)* Reorganize presentation routing
- *(links)* Clarify short link redirect router naming
- *(project)* Use built-in generic types
- *(logging)* Clarify logging configuration naming
- *(http)* Clarify API v1 router naming
- *(http)* Clarify domain error handler naming
- *(config)* Add package-level configuration exports
- *(links)* Use PostgreSQL short link repository
- *(http)* Replace deprecated HTTP 422 status constant
- *(app)* Use explicit middleware argument
- *(app)* Use app naming consistently

### 📚 Documentation

- *(license)* Add project license
- *(env)* Add environment template
- *(security)* Add security policy
- *(http)* Document endpoint responses
- *(code-of-conduct)* Add code of conduct
- *(readme)* Add project documentation
- *(readme)* Add CI status badge and workflow description
- *(architecture)* Add project architecture documentation
- *(code-style)* Add project coding guidelines
- *(contributing)* Add contribution guidelines
- *(project)* Remove links to source and configuration files

### 🧪 Testing

- *(project)* Configure pytest and coverage
- *(links)* Add short link domain tests
- *(links)* Add short link application tests
- *(links)* Add in-memory infrastructure tests
- *(links)* Add PostgreSQL short link repository tests
- *(http)* Add endpoint tests
- *(app)* Add readiness and request ID context tests
- *(http)* Add dependency provider tests
- *(http)* Add request middleware tests
- *(app)* Add configuration and startup tests
- *(project)* Run integration tests by default
- *(links)* Cover requests without expires_at

### ⚙️ Miscellaneous Tasks

- *(project)* Initialize repository
- *(git)* Add ignore rules
- *(flake8)* Configure linting rules
- *(isort)* Configure import sorting
- *(black)* Configure code formatter
- *(mypy)* Configure type checking
- *(pre-commit)* Add code quality hooks
- *(flake8)* Ignore __init__ docstrings
- *(logging)* Configure application logging
- *(database)* Configure Alembic migrations
- *(black)* Exclude Alembic migrations
- *(pre-commit)* Exclude Alembic migrations
- *(mypy)* Exclude Alembic migrations
- *(logging)* Configure database logging
- *(git-cliff)* Configure changelog generation
- *(commitizen)* Configure conventional commits
- *(pre-commit)* Validate commit messages with Commitizen
- *(release)* Synchronize version files
- *(pre-commit)* Add pytest hook
- *(logging)* Log only to standard output
- *(git)* Simplify ignore rules
- *(project)* Add GitHub Actions workflow
- *(project)* Check for missing migrations
