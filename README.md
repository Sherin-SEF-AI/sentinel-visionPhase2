# Sentinel Vision Phase 2 - Security Intelligence Platform

A production-grade enterprise security intelligence platform with natural language video search, threat signature detection, advanced forensics, and real-time monitoring capabilities.

## Features

- **Natural Language Video Search**: Conversational querying of video archives using Gemini 3 Pro
- **Threat Signature Detection**: 150+ predefined threat signatures with custom signature builder
- **Advanced Forensics**: Timeline reconstruction, multi-camera correlation, pattern analysis
- **Real-time Person Tracking**: Cross-frame identity linking across multiple cameras
- **Live Monitoring**: Real-time threat alerts and camera feed monitoring
- **Production-Ready**: Scalable microservice architecture with comprehensive error handling

## Technology Stack

- **Backend**: FastAPI (Python 3.11+) with asyncio
- **Vision AI**: Gemini 3 Pro, Gemini 1.5 Flash, YOLO11
- **Vector Database**: Qdrant
- **Relational Database**: PostgreSQL 16+
- **Cache**: Redis
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Video Processing**: OpenCV, FFmpeg

## Architecture

The system uses a microservice architecture with the following services:

1. **Video Ingestion Service**: Camera stream monitoring and frame extraction
2. **Frame Analysis Service**: Gemini-powered scene understanding and embedding generation
3. **Person Tracking Service**: Cross-frame identity linking with spatiotemporal validation
4. **Threat Signature Detection Service**: Real-time threat evaluation and alerting
5. **Natural Language Search Service**: Conversational video archive querying
6. **Forensic Analysis Service**: Advanced investigative capabilities
7. **Alert Management Service**: Real-time notification delivery
8. **API Gateway Service**: Unified API access and routing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Gemini API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd sentinel-visionPhase2
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Start services with Docker Compose:
```bash
docker-compose up -d
```

4. Initialize database:
```bash
python scripts/init_db.py
```

5. Access the application:
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- API: http://localhost:8000

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Project Structure

```
sentinel-visionPhase2/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Database connections
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── api/                    # API routes
│   │   ├── services/               # Business logic services
│   │   │   ├── video_ingestion.py
│   │   │   ├── frame_analysis.py
│   │   │   ├── person_tracking.py
│   │   │   ├── threat_detection.py
│   │   │   ├── search.py
│   │   │   └── forensics.py
│   │   └── utils/                  # Utility functions
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── init_db.py
│   └── load_signatures.py
├── docker-compose.yml
├── .env.example
└── README.md
```

## Configuration

Key configuration options in `.env`:

```
# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_3_PRO_MODEL=gemini-3-pro-preview
GEMINI_FLASH_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=text-embedding-005

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentinel_vision
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=frame_embeddings

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
LOG_LEVEL=INFO
MAX_CAMERAS=32
FRAME_EXTRACTION_FPS=1
MOTION_DETECTION_FPS=5
```

## API Documentation

Once the backend is running, access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.
