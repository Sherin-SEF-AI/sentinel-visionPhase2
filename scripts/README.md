# Sentinel Vision Scripts

This directory contains utility scripts for database initialization, maintenance, and operations.

## Scripts

### init_db.py

Initialize the database with tables, threat signatures, and sample data.

```bash
python scripts/init_db.py
```

This script:
- Creates all database tables
- Initializes Qdrant vector database collection
- Loads 150+ predefined threat signatures
- Creates sample camera records for testing

### Requirements

Ensure the backend dependencies are installed and the database services are running:

```bash
cd backend
pip install -r requirements.txt

# Start database services
docker-compose up -d postgres qdrant redis
```

### Environment Variables

Ensure your `.env` file is configured with database connection details:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentinel_vision
POSTGRES_USER=sentinel_user
POSTGRES_PASSWORD=your_password

QDRANT_HOST=localhost
QDRANT_PORT=6333

REDIS_HOST=localhost
REDIS_PORT=6379

GEMINI_API_KEY=your_gemini_api_key
```

## Usage Notes

- Run `init_db.py` after first deployment or when resetting the database
- The script is idempotent - it won't duplicate data if run multiple times
- Threat signatures are loaded from `backend/data/threat_signatures.json`
- Sample cameras can be modified or replaced with real camera configurations

## Troubleshooting

If you encounter connection errors:

1. Verify database services are running: `docker-compose ps`
2. Check database credentials in `.env`
3. Ensure PostgreSQL is accepting connections
4. Verify Qdrant service is accessible at configured port

For Gemini API issues:
- Verify your API key is valid
- Ensure you have sufficient API quota
- Check network connectivity to Google AI services
