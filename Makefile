.PHONY: help install dev test lint format clean docker-build docker-run k8s-deploy k8s-delete

help:
	@echo "Statistical Feature Builder - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-push  - Push Docker image"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy   - Deploy to Kubernetes"
	@echo "  make k8s-delete   - Delete from Kubernetes"
	@echo "  make k8s-logs     - View logs"
	@echo ""

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app/
	mypy app/

format:
	black app/
	isort app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.log' -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker build -t pulse/sfb:1.0.0 .

docker-run:
	docker run -p 8000:8000 --env-file .env pulse/sfb:1.0.0

docker-push:
	docker tag pulse/sfb:1.0.0 registry.pulse.ai/sfb:1.0.0
	docker push registry.pulse.ai/sfb:1.0.0

k8s-deploy:
	kubectl create namespace pulse-services --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl apply -f k8s/ingress.yaml

k8s-delete:
	kubectl delete -f k8s/ingress.yaml
	kubectl delete -f k8s/hpa.yaml
	kubectl delete -f k8s/deployment.yaml

k8s-logs:
	kubectl logs -f deployment/sfb-deployment -n pulse-services

k8s-status:
	kubectl get pods -n pulse-services
	kubectl get svc -n pulse-services
	kubectl get hpa -n pulse-services
