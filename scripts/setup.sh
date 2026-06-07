#!/bin/bash
set -e

echo "========================================="
echo "  SpeakEasy - AI English Coach Setup"
echo "========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    exit 1
fi
echo "[OK] Docker found: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not available. Please install it."
    exit 1
fi
echo "[OK] Docker Compose found"

# Check .env
if [ ! -f .env ]; then
    echo "[SETUP] Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "[ACTION REQUIRED] Please edit .env and fill in your API keys:"
    echo "  - ALIYUN_ACCESS_KEY_ID / ALIYUN_ACCESS_KEY_SECRET / ALIYUN_NLS_APPKEY"
    echo "  - DEEPSEEK_API_KEY"
    echo "  - YOUDAO_APP_KEY / YOUDAO_APP_SECRET"
    echo ""
    echo "Then run this script again."
    exit 0
fi
echo "[OK] .env file found"

# Build
echo ""
echo "[BUILD] Building Docker images..."
docker compose build

# Start
echo ""
echo "[START] Starting services..."
docker compose up -d

# Wait for backend health
echo ""
echo "[WAIT] Waiting for backend to be healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "[OK] Backend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[WARN] Backend health check timeout. Check logs: docker compose logs backend"
    fi
    sleep 2
done

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo "  Frontend: http://localhost"
echo "  Backend:  http://localhost:8000"
echo "  Health:   http://localhost:8000/health"
echo ""
echo "  To run smoke tests:"
echo "    cd backend && python -m pytest ../tests/smoke -v"
echo ""
echo "  To view logs:"
echo "    docker compose logs -f"
echo "========================================="
