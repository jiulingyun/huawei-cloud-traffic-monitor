Docker Compose for Huawei Cloud Traffic Monitor

Services:
- backend: Python FastAPI app (uvicorn)
- frontend: Vue app served by nginx

Usage:
1. Copy `.env.example` to `.env` and fill in credentials.
2. Build and start:
   docker compose -f docker/docker-compose.yml up --build -d


