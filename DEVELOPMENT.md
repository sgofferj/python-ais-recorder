# Development Guide

This guide covers local development setup, testing, and contributing to the project.

## Prerequisites

- Python 3.12+
- Poetry
- MariaDB 11.4+ (or Docker for containerized setup)

## Local Setup

### 1. Clone and Environment

```bash
git clone https://github.com/sgofferj/python-ais-recorder.git
cd python-ais-recorder

# Create virtual environment
python3 -m venv .venv

# Install dependencies
./.venv/bin/pip install poetry
./.venv/bin/poetry install --with dev
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
cat > .env << EOF
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_DATABASE=ais_recorder
MARIADB_USER=ais_user
MARIADB_PASSWORD=your_password
EOF
```

### 3. Database Setup

#### Option A: Local MariaDB

```bash
# Create database and user
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS ais_recorder;
CREATE USER IF NOT EXISTS 'ais_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ais_recorder.* TO 'ais_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

#### Option B: Docker Compose (with MariaDB only)

```bash
docker-compose up -d mariadb
```

### 4. Initialize Database

```bash
# Run Alembic migrations
./.venv/bin/alembic upgrade head
```

Or initialize tables directly:
```bash
./.venv/bin/poetry run python -c "import asyncio; from ais_recorder.database import init_db; asyncio.run(init_db())"
```

## Running the Application

### Full Stack

```bash
./.venv/bin/poetry run python src/ais_recorder/main.py
```

### Individual Components

```bash
# API only
./.venv/bin/poetry run uvicorn ais_recorder.api:app --host 0.0.0.0 --port 8000

# MQTT receiver only
./.venv/bin/poetry run python src/ais_recorder/receiver.py

# Retention worker only
./.venv/bin/poetry run python src/ais_recorder/retention.py
```

### Docker Compose (Full Stack)

```bash
docker-compose up -d
```

## Quality Checks

Run all linters and type checkers:

```bash
./.venv/bin/poetry run black src
./.venv/bin/poetry run mypy src
./.venv/bin/poetry run pylint src/ais_recorder
```

Or run all at once:
```bash
./.venv/bin/poetry run black src && ./.venv/bin/poetry run mypy src && ./.venv/bin/poetry run pylint src/ais_recorder
```

## Database Migrations

### Create a New Migration

```bash
./.venv/bin/alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
./.venv/bin/alembic upgrade head
```

### Rollback

```bash
./.venv/bin/alembic downgrade -1
```

## Testing API

```bash
# Health check
curl http://localhost:8000/health

# List vessels
curl http://localhost:8000/vessels

# Query positions with filters
curl "http://localhost:8000/positions?mmsi=123456789&start_time=2024-01-01T00:00:00"
```

## Project Dependencies

### Adding New Dependencies

```bash
# Main dependencies
./.venv/bin/poetry add <package>

# Dev dependencies
./.venv/bin/poetry add --group dev <package>

# Update lock file
./.venv/bin/poetry lock
```

## Code Style

- Follow PEP-8
- Line length: 120 characters
- Use type hints throughout
- All modules must pass: `black`, `mypy --strict`, `pylint`

## Git Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Run quality checks before committing
4. Push and create pull request

### Commit Message Format

```
<type>: <short description>

<optional longer description>

<optional: issues fixed>
```

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`

## Docker Development

### Build Image

```bash
docker build -t python-ais-recorder .
```

### Run with Custom Config

```bash
docker run -d \
  -e MARIADB_HOST=host.docker.internal \
  -e MARIADB_USER=ais_user \
  -e MARIADB_PASSWORD=password \
  -p 8000:8000 \
  python-ais-recorder
```

### Development with Volume Mount

```bash
docker run -d \
  -v $(pwd)/src:/app/src:ro \
  -e MARIADB_HOST=host.docker.internal \
  -p 8000:8000 \
  python-ais-recorder
```

## Troubleshooting

### MariaDB Connection Issues

```bash
# Test connection
mysql -u ais_user -p -h localhost ais_recorder

# Check container health
docker-compose ps
docker-compose logs mariadb
```

### Migration Errors

```bash
# Show current migration
./.venv/bin/alembic current

# Show migration history
./.venv/bin/alembic history

# Recreate database (development only)
./.venv/bin/alembic downgrade base
./.venv/bin/alembic upgrade head
```

### MQTT Receiver Not Connecting

- Check firewall rules for `meri.digitraffic.fi:443`
- Verify TLS certificate requirements
- Check Digitraffic service status