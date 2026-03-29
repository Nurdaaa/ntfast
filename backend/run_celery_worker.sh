#!/bin/bash
echo "Starting Celery Worker for Financial Analysis System..."
echo ""
echo "Make sure Redis is running before starting this worker!"
echo ""
celery -A app.core.celery_app worker --loglevel=info
