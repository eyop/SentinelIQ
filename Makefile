PYTHON ?= .venv\Scripts\python.exe
PIP ?= .venv\Scripts\pip.exe
TEST ?= pytest -q

.PHONY: help install test lint run docker-build docker-up deploy

help:
	@echo "Available targets:"
	@echo "  make install        Install Python dependencies"
	@echo "  make test           Run backend tests"
	@echo "  make run            Run FastAPI app locally"
	@echo "  make docker-build   Build backend and frontend images"
	@echo "  make docker-up      Start services with docker compose"
	@echo "  make deploy         Run deployment helper"

install:
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000

docker-build:
	docker build -t sentineliq-api:local .
	docker build -t sentineliq-frontend:local frontend/

docker-up:
	docker compose up --build -d

deploy:
	./deploy/deploy.sh $(HOST) $(USER) $(COMPOSE_PATH) $(TAG) $(OWNER)
