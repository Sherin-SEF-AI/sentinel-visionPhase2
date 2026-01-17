# Sentinel Vision Phase 2 - Deployment Guide

Complete deployment guide for the security intelligence platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker Compose)](#quick-start-docker-compose)
3. [Manual Deployment](#manual-deployment)
4. [Configuration](#configuration)
5. [Database Initialization](#database-initialization)
6. [Running the Application](#running-the-application)
7. [Troubleshooting](#troubleshooting)
8. [Production Considerations](#production-considerations)

## Prerequisites

### Required Software

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **Git** for cloning the repository

### Required API Keys

- **Google Gemini API Key**: Obtain from [Google AI Studio](https://makersuite.google.com/app/apikey)

### System Requirements

**Minimum:**
- 4 CPU cores
- 16 GB RAM
- 100 GB storage
- Ubuntu 20.04+ or similar Linux distribution

**Recommended:**
- 8+ CPU cores
- 32 GB RAM
- 500 GB SSD storage
- GPU for YOLO (optional, for future)

## Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone <repository-url>
cd sentinel-visionPhase2
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Edit the `.env` file with your configuration:

```bash
# REQUIRED: Add your Gemini API key
GEMINI_API_KEY=your_actual_api_key_here

# Database passwords (change for production)
POSTGRES_PASSWORD=secure_password_here

# Optional: Adjust other settings as needed
```

### 3. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Qdrant vector database (ports 6333, 6334)
- Redis cache (port 6379)
- Backend API (port 8000)
- Frontend (port 3000)

### 4. Initialize Database

```bash
# Wait for services to be ready (about 30 seconds)
sleep 30

# Run initialization script
docker-compose exec backend python /app/../scripts/init_db.py
```

### 5. Access Application

- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6. Add Cameras

Use the frontend or API to add cameras:

```bash
curl -X POST "http://localhost:8000/api/v1/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "CAM001",
    "name": "Main Entrance",
    "location": "Building A - Main Entrance",
    "facility_zone": "Public Entry",
    "stream_url": "rtsp://your-camera-ip:554/stream",
    "is_active": true
  }'
```

## Manual Deployment

### Backend Setup

#### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
  libpq-dev build-essential libgl1-mesa-glx libglib2.0-0 \
  libsm6 libxext6 libxrender-dev ffmpeg

# Install PostgreSQL client
sudo apt install -y postgresql-client
```

#### 2. Set Up Python Environment

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Backend

```bash
cp ../.env.example ../.env
# Edit .env with your configuration
```

#### 4. Start Backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Setup

#### PostgreSQL

```bash
# Using Docker (recommended)
docker run -d \
  --name sentinel_postgres \
  -e POSTGRES_DB=sentinel_vision \
  -e POSTGRES_USER=sentinel_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:16-alpine
```

Or install natively:

```bash
sudo apt install postgresql-16
sudo -u postgres createuser sentinel_user
sudo -u postgres createdb sentinel_vision -O sentinel_user
sudo -u postgres psql -c "ALTER USER sentinel_user PASSWORD 'secure_password';"
```

#### Qdrant

```bash
docker run -d \
  --name sentinel_qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

#### Redis

```bash
docker run -d \
  --name sentinel_redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine redis-server --appendonly yes
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Frontend

```bash
cp .env.example .env
# Edit VITE_API_URL and VITE_WS_URL if needed
```

#### 3. Development

```bash
npm run dev
```

#### 4. Production Build

```bash
npm run build

# Serve with nginx or any static server
npx serve -s dist -p 3000
```

## Configuration

### Environment Variables

#### Backend Configuration

```bash
# Gemini API (REQUIRED)
GEMINI_API_KEY=your_api_key

# Database connections
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sentinel_vision
POSTGRES_USER=sentinel_user
POSTGRES_PASSWORD=secure_password

QDRANT_HOST=localhost
QDRANT_PORT=6333

REDIS_HOST=localhost
REDIS_PORT=6379

# Application settings
LOG_LEVEL=INFO
MAX_CAMERAS=32
FRAME_EXTRACTION_FPS=1
MOTION_DETECTION_FPS=5

# Performance tuning
WORKER_PROCESSES=4
MAX_CONCURRENT_FRAMES=50
DATABASE_POOL_SIZE=20
```

#### Frontend Configuration

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Camera Configuration

Cameras can be added via:

1. **Frontend UI**: Navigate to Cameras page and click "Add Camera"
2. **API**: POST to `/api/v1/cameras`
3. **Database**: Direct SQL insertion (not recommended)

#### Supported Stream Protocols

- RTSP: `rtsp://camera-ip:554/stream`
- RTMP: `rtmp://camera-ip/live/stream`
- HLS: `http://camera-ip/stream.m3u8`

#### Camera Configuration Parameters

```json
{
  "camera_id": "CAM001",
  "name": "Descriptive Camera Name",
  "location": "Physical Location",
  "facility_zone": "Zone Name",
  "access_level": "public|restricted|secure|high_security",
  "location_type": "entrance|parking_lot|hallway|office",
  "stream_url": "rtsp://...",
  "frame_extraction_fps": 1,
  "motion_detection_enabled": true,
  "motion_detection_fps": 5,
  "motion_sensitivity": 50
}
```

## Database Initialization

### Automatic Initialization

```bash
cd backend
python ../scripts/init_db.py
```

This script:
- Creates all database tables
- Initializes Qdrant collection
- Loads threat signatures
- Creates sample cameras

### Manual Verification

```bash
# Check PostgreSQL tables
psql -U sentinel_user -d sentinel_vision -c "\dt"

# Check Qdrant collection
curl http://localhost:6333/collections

# Check Redis
redis-cli ping
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Production Mode

#### Using Docker Compose

```bash
docker-compose up -d
```

#### Using Systemd Services

Create `/etc/systemd/system/sentinel-backend.service`:

```ini
[Unit]
Description=Sentinel Vision Backend
After=network.target postgresql.service

[Service]
Type=simple
User=sentinel
WorkingDirectory=/opt/sentinel-vision/backend
Environment="PATH=/opt/sentinel-vision/backend/venv/bin"
ExecStart=/opt/sentinel-vision/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable sentinel-backend
sudo systemctl start sentinel-backend
sudo systemctl status sentinel-backend
```

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to PostgreSQL"

```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# or
sudo systemctl status postgresql

# Test connection
psql -h localhost -U sentinel_user -d sentinel_vision
```

#### 2. "Qdrant collection not found"

```bash
# Reinitialize Qdrant
python scripts/init_db.py
```

#### 3. "Gemini API errors"

```bash
# Verify API key
echo $GEMINI_API_KEY

# Test API access
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY"
```

#### 4. "Camera stream connection failed"

- Verify RTSP URL is correct
- Check network connectivity to camera
- Ensure camera supports the protocol (RTSP/RTMP/HLS)
- Try accessing stream with VLC or ffplay first:
  ```bash
  ffplay rtsp://camera-ip:554/stream
  ```

#### 5. "Frontend can't connect to backend"

- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `.env`
- Ensure frontend proxy is configured correctly

### Logs

**Backend logs:**
```bash
docker-compose logs -f backend
# or
tail -f /var/log/sentinel-backend/app.log
```

**Database logs:**
```bash
docker-compose logs -f postgres
```

**Frontend logs:**
```bash
docker-compose logs -f frontend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Detailed readiness
curl http://localhost:8000/ready

# Liveness
curl http://localhost:8000/live

# WebSocket stats
curl http://localhost:8000/api/v1/stats
```

## Production Considerations

### Security

1. **Change default passwords** in `.env`
2. **Use HTTPS** with SSL certificates (nginx/Let's Encrypt)
3. **Enable authentication** (implement JWT in future phase)
4. **Restrict database access** to application servers only
5. **Use secrets management** (Vault, AWS Secrets Manager)
6. **Enable firewall rules**

```bash
# Example UFW rules
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Block external PostgreSQL access
sudo ufw deny 6333/tcp  # Block external Qdrant access
sudo ufw enable
```

### Performance Tuning

#### PostgreSQL

```sql
-- Tune for performance
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
```

#### Qdrant

- Adjust HNSW index parameters for your dataset size
- Monitor memory usage and adjust accordingly
- Consider sharding for very large deployments

#### Application

- Increase `WORKER_PROCESSES` for more concurrent processing
- Adjust `MAX_CONCURRENT_FRAMES` based on available resources
- Tune `DATABASE_POOL_SIZE` for your workload

### Backup Strategy

#### Database Backups

```bash
# PostgreSQL backup
docker exec sentinel_postgres pg_dump -U sentinel_user sentinel_vision | gzip > backup_$(date +%Y%m%d).sql.gz

# Qdrant backup
curl -X POST 'http://localhost:6333/collections/frame_embeddings/snapshots'
```

#### Automated Backups

Create cron job:

```bash
# /etc/cron.d/sentinel-backup
0 2 * * * root /opt/sentinel-vision/scripts/backup.sh
```

### Monitoring

Set up monitoring with:

- **Prometheus** for metrics
- **Grafana** for visualization
- **AlertManager** for alerting

Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'sentinel-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Scaling

#### Horizontal Scaling

- Run multiple backend instances behind a load balancer
- Share Redis and databases across instances
- Use managed services for databases (RDS, managed Qdrant)

#### Vertical Scaling

- Increase server resources (CPU, RAM)
- Add GPU for YOLO processing (future)
- Use faster storage (NVMe SSD)

### High Availability

- Run backend instances across multiple servers
- Use PostgreSQL replication
- Implement Redis clustering
- Set up health checks and automatic failover

## Support

For issues, questions, or contributions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs for error messages
3. Consult API documentation at `/docs`
4. Check GitHub issues

## Next Steps

After successful deployment:

1. Add your cameras via the UI
2. Test natural language search functionality
3. Configure threat signatures for your facility
4. Set up user authentication (future phase)
5. Enable video ingestion (uncomment in `main.py`)
6. Configure monitoring and alerts
7. Set up automated backups

---

**Deployment Checklist:**

- [ ] Environment configured (`.env`)
- [ ] Gemini API key added
- [ ] Database services running
- [ ] Database initialized
- [ ] Backend API accessible
- [ ] Frontend accessible
- [ ] Cameras added
- [ ] Search functionality tested
- [ ] Threat alerts working
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Security hardened
- [ ] Documentation reviewed

**Ready for production!** 🚀
