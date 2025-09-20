from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Job metrics
jobs_created_total = Counter(
    'jobs_created_total',
    'Total number of jobs created',
    ['kind']
)

jobs_failed_total = Counter(
    'jobs_failed_total',
    'Total number of jobs failed',
    ['kind', 'reason']
)

jobs_completed_total = Counter(
    'jobs_completed_total',
    'Total number of jobs completed',
    ['kind']
)

# Webhook metrics
webhook_delivery_attempts = Counter(
    'webhook_delivery_attempts_total',
    'Total number of webhook delivery attempts',
    ['endpoint_id', 'status']
)

webhook_delivery_duration = Histogram(
    'webhook_delivery_duration_seconds',
    'Time spent delivering webhooks',
    ['endpoint_id']
)

# Processing metrics
processing_time_histogram = Histogram(
    'processing_time_seconds',
    'Time spent processing jobs',
    ['kind']
)

# Upload metrics
uploads_initiated_total = Counter(
    'uploads_initiated_total',
    'Total number of uploads initiated'
)

uploads_completed_total = Counter(
    'uploads_completed_total',
    'Total number of uploads completed'
)

uploads_failed_total = Counter(
    'uploads_failed_total',
    'Total number of uploads failed'
)

# System metrics
active_jobs = Gauge(
    'active_jobs',
    'Number of active jobs',
    ['status']
)

active_webhooks = Gauge(
    'active_webhooks',
    'Number of active webhook endpoints'
)


def get_metrics_response():
    """Get Prometheus metrics as a response"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
