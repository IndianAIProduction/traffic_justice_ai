#!/bin/bash
# Traffic Justice AI - Development Setup Script
set -e

echo "==================================="
echo " Traffic Justice AI - Dev Setup"
echo "==================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required."; exit 1; }

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env and add your OPENAI_API_KEY before running the app."
fi

# Build and start services
echo ""
echo "Building and starting Docker services..."
docker compose up --build -d

# Wait for postgres
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker compose exec backend alembic upgrade head || echo "Note: Run migrations manually after first Alembic revision is created."

echo ""
echo "==================================="
echo " Setup Complete!"
echo "==================================="
echo ""
echo " Frontend:  http://localhost:3000"
echo " Backend:   http://localhost:8000"
echo " API Docs:  http://localhost:8000/docs"
echo " ChromaDB:  http://localhost:8001"
echo ""
echo " Next steps:"
echo "   1. Edit .env with your OPENAI_API_KEY"
echo "   2. Place legal documents in backend/data/legal_corpus/"
echo "   3. Run: docker compose exec backend python run_ingestion.py"
echo "   4. Read README.md in the repo root for full documentation"
echo ""
