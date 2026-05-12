# AIS Recorder

AIS data recorder from Digitraffic to MariaDB using MQTT and a REST API.

## Features

- **Real-time AIS Data Ingestion**: Receives AIS data from Digitraffic via MQTT over WebSockets
- **Asynchronous Architecture**: Built with async SQLAlchemy for high-concurrency handling
- **REST API**: FastAPI-based API for querying historical AIS positions and vessel metadata
- **Data Retention**: Automatic cleanup of old position data (configurable retention period)
- **Database Migrations**: Alembic-managed schema migrations
- **Container-Ready**: Docker and docker-compose support with health checks
- **Structured Logging**: JSON-formatted logs compatible with Loki/Grafana

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/sgofferj/python-ais-recorder.git
cd python-ais-recorder

# Create .env file
cat > .env << EOF
MARIADB_USER=ais_user
MARIADB_PASSWORD=your_secure_password
MARIADB_ROOT_PASSWORD=your_root_password
EOF

# Start the application
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Local Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## Configuration

The application is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MARIADB_HOST` | `localhost` | MariaDB server hostname |
| `MARIADB_PORT` | `3306` | MariaDB server port |
| `MARIADB_DATABASE` | `ais_recorder` | Database name |
| `MARIADB_USER` | (required) | Database username |
| `MARIADB_PASSWORD` | (required) | Database password |
| `RETENTION_HOURS` | `48` | Position data retention period |
| `API_WORKERS` | `1` | Number of API workers |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DIGITRAFFIC_USER` | `python-ais-recorder/1.0` | Digitraffic MQTT user agent |

## API Endpoints

### Health Check

```
GET /health
```

Returns service health and version information.

### Query Positions

```
GET /positions
```

Query historical AIS positions with optional filters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `mmsi` | integer | Filter by vessel MMSI |
| `imo` | integer | Filter by vessel IMO |
| `start_time` | datetime | Start of time range (ISO 8601) |
| `end_time` | datetime | End of time range (ISO 8601) |
| `bbox` | string | Bounding box filter (min_lon,min_lat,max_lon,max_lat) |

Example:
```bash
curl "http://localhost:8000/positions?mmsi=123456789&start_time=2024-01-01T00:00:00"
```

### List Vessels

```
GET /vessels
```

Returns all vessels in the metadata table.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AIS Recorder                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│  MQTT Receiver  │ Retention Worker│     FastAPI API         │
│  (paho-mqtt)    │  (APScheduler)  │   (uvicorn/asyncio)     │
├─────────────────┴─────────────────┴─────────────────────────┤
│                  Async SQLAlchemy (aiomysql)                 │
├─────────────────────────────────────────────────────────────┤
│                    MariaDB                                   │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
python-ais-recorder/
├── alembic/               # Database migrations
│   ├── env.py
│   ├── init.sql
│   └── versions/
├── src/ais_recorder/      # Source code
│   ├── api.py            # FastAPI REST endpoints
│   ├── config.py         # Pydantic settings
│   ├── database.py       # SQLAlchemy models
│   ├── main.py          # Main orchestrator
│   ├── receiver.py      # MQTT data receiver
│   ├── retention.py     # Data cleanup worker
│   └── schemas.py       # Pydantic schemas
├── docker-compose.yaml
├── Dockerfile
├── alembic.ini
└── pyproject.toml
```

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

See [LICENSE](LICENSE) for full details.