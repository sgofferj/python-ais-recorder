# AIS Recorder

## Completed
- [x] Why do we have .venv/ and venv? - Cleaned up, removed duplicate venv
- [x] Environment variables/.env support - Already implemented via pydantic-settings with python-dotenv

## Implemented from Gemini suggestions
- [x] Asynchronous Architecture - Converted to async SQLAlchemy with aiomysql
- [x] Container Orchestration - Created docker-compose.yaml with app + MariaDB
- [x] Schema Migrations - Set up Alembic with initial migration
- [x] Structured Logging - Added structlog with JSON output for Loki
- [x] Health Checks - Added /health endpoint for Docker/K8s
- [x] Input Validation - Enhanced Pydantic schemas with strict validation
- [x] Database Partitioning - Deferred (would restrict retention time flexibility)

## In Progress

## Pending