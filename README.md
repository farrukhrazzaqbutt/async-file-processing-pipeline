# Async File Processing Pipeline

A resilient, idempotent file processing pipeline with resumable uploads and signed webhooks. Built with FastAPI, SQLAlchemy, Celery, and MinIO.

## Features

- **Pre-signed Uploads**: Direct upload to MinIO object storage with presigned URLs
- **Background Processing**: Celery workers for async file processing
- **Webhook Delivery**: Reliable webhook delivery with HMAC signatures and retry logic
- **Idempotent Operations**: Safe retry of operations using idempotency keys
- **Authentication**: JWT-based authentication with user management
- **Monitoring**: Prometheus metrics for observability
- **Testing**: Comprehensive test suite with pytest

## Architecture

```
Client → FastAPI → MinIO (Storage)
                ↓
            Celery Queue → Workers → Processing
                ↓
            Webhook Delivery → External Endpoints
```

## Tech Stack

- **Python 3.11**
- **FastAPI** - Web framework
- **SQLAlchemy 2.x** - ORM
- **PostgreSQL** - Database
- **Redis** - Message broker and caching
- **Celery** - Background task processing
- **MinIO** - Object storage
- **Docker Compose** - Container orchestration
- **Pytest** - Testing framework

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd async_file_processing_pipeline
   ```

2. **Set up environment variables**
   ```bash
   cp env.sample .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. **Create admin user**
   ```bash
   curl -X POST http://localhost:8000/auth/seed
   ```

6. **Access the API**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (admin/admin)

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start services**
   ```bash
   docker-compose up -d db redis minio
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the API**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Start Celery worker**
   ```bash
   celery -A app.workers.celery_app worker -Q default -l info
   ```

## API Usage

### Authentication

1. **Register a user**
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "email": "user@example.com", "password": "password123"}'
   ```

2. **Login**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user&password=password123"
   ```

### File Upload and Processing

1. **Initiate upload**
   ```bash
   curl -X POST http://localhost:8000/uploads/initiate \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"filename": "document.pdf", "content_type": "application/pdf", "size": 1024000}'
   ```

2. **Upload file directly to MinIO** (using the presigned URL from step 1)

3. **Complete upload**
   ```bash
   curl -X POST http://localhost:8000/uploads/{upload_id}/complete \
     -H "Authorization: Bearer <token>"
   ```

4. **Create processing job**
   ```bash
   curl -X POST http://localhost:8000/jobs \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"upload_id": 1, "kind": "text_extract"}'
   ```

5. **Check job status**
   ```bash
   curl -X GET http://localhost:8000/jobs/{job_id} \
     -H "Authorization: Bearer <token>"
   ```

### Webhook Configuration

1. **Create webhook endpoint**
   ```bash
   curl -X POST http://localhost:8000/webhooks/endpoints \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.com/webhook", "secret": "your-secret-key"}'
   ```

2. **Test webhook**
   ```bash
   curl -X POST http://localhost:8000/webhooks/test \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"endpoint_id": 1}'
   ```

## Webhook Payload

Webhooks are sent with HMAC-SHA256 signatures in the `X-Signature` header:

```json
{
  "job_id": 123,
  "status": "completed",
  "result": {
    "text": "Extracted text content...",
    "length": 1500,
    "file_type": "pdf"
  },
  "timestamp": "2023-01-01T00:00:00Z",
  "event_type": "job.completed"
}
```

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

## Job Types

- **text_extract**: Extract text from documents
- **thumbnail**: Generate image thumbnails
- **metadata**: Extract file metadata

## Configuration

Key environment variables:

```env
# Database
DATABASE_URL=postgresql://app:app@localhost:5432/app

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=uploads
MINIO_SECURE=false

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## Monitoring

The application includes Prometheus metrics:

- `jobs_created_total` - Total jobs created
- `jobs_failed_total` - Total jobs failed
- `webhook_delivery_attempts` - Webhook delivery attempts
- `processing_time_histogram` - Job processing time

Access metrics at: http://localhost:8000/metrics

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Deployment

1. **Set secure environment variables**
2. **Use a production database**
3. **Configure proper CORS settings**
4. **Set up SSL/TLS**
5. **Configure monitoring and logging**
6. **Set up backup strategies**

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.
