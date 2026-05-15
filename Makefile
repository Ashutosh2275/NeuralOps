.PHONY: help up down migrate backend workers frontend minikube-up minikube-deploy test lint

help:
	@echo "SentinelOps AI — available targets:"
	@echo "  make up              - Start Docker Compose stack"
	@echo "  make down            - Stop Docker Compose stack"
	@echo "  make migrate         - Run Alembic migrations"
	@echo "  make backend         - Start FastAPI server"
	@echo "  make workers         - Start background workers"
	@echo "  make frontend        - Start React dev server"
	@echo "  make minikube-up     - Start Minikube cluster"
	@echo "  make minikube-deploy - Deploy SentinelOps to Minikube"
	@echo "  make test            - Run backend tests"
	@echo "  make lint            - Run linters"

up:
	docker compose up -d

down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

backend:
	cd backend && uvicorn sentinelops.main:app --host 0.0.0.0 --port 8000 --reload

workers:
	cd backend && python -m sentinelops.workers.runner

frontend:
	cd frontend && npm run dev

minikube-up:
	minikube start --cpus=4 --memory=8192 --driver=docker
	minikube addons enable metrics-server
	minikube addons enable ingress

minikube-deploy:
	kubectl apply -f infra/kubernetes/namespace.yaml
	kubectl apply -f infra/kubernetes/configmaps/
	kubectl apply -f infra/kubernetes/monitoring/
	kubectl apply -f infra/kubernetes/sentinelops/

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check src/
	cd frontend && npm run lint
