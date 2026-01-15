# Makefile for Job Application Tracker
# Common commands for development and CI

.PHONY: help install lint format test test-cov migrate run docker-up docker-down clean

# Default target
help:
	@echo "Job Application Tracker - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install dependencies"
	@echo "  make run         - Run development server"
	@echo "  make migrate     - Run database migrations"
	@echo "  make shell       - Open Django shell"
	@echo ""
	@echo "Celery (Async Tasks):"
	@echo "  make celery-worker - Start Celery worker locally"
	@echo "  make celery-beat   - Start Celery beat scheduler"
	@echo "  make celery-logs   - View Celery container logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-cov    - Run tests with coverage"
	@echo "  make test-fast   - Run tests without coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Check code style"
	@echo "  make format      - Auto-format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make docker-logs - View container logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove cache files"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements/development.txt

# Run development server
run:
	python manage.py runserver

# Run database migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate

# Open Django shell
shell:
	python manage.py shell

# Run all tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=apps --cov=services --cov-report=html --cov-report=term-missing -v
	@echo "Coverage report: htmlcov/index.html"

# Run tests without coverage (faster)
test-fast:
	pytest -v --tb=short -q

# Lint code
lint:
	@echo "Checking code formatting with Black..."
	black --check --diff --exclude migrations .
	@echo ""
	@echo "Checking import sorting with isort..."
	isort --check-only --diff --skip migrations .
	@echo ""
	@echo "Linting with flake8..."
	flake8 --exclude=migrations,__pycache__,.venv .
	@echo ""
	@echo "All checks passed!"

# Auto-format code
format:
	@echo "Formatting code with Black..."
	black --exclude migrations .
	@echo ""
	@echo "Sorting imports with isort..."
	isort --skip migrations .
	@echo ""
	@echo "Code formatted!"

# Start Docker containers
docker-up:
	docker-compose up -d

# Stop Docker containers
docker-down:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f

# View Celery worker logs
celery-logs:
	docker-compose logs -f celery_worker

# Build and start Docker containers
docker-build:
	docker-compose up -d --build

# Start Celery worker locally (for development)
celery-worker:
	celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery-beat:
	celery -A config beat -l info

# Clean cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	@echo "Cache cleaned!"

# Create superuser
superuser:
	python manage.py createsuperuser

# Collect static files
collectstatic:
	python manage.py collectstatic --no-input

# Check for security issues
security:
	pip install safety
	safety check

# Generate API schema
schema:
	python manage.py spectacular --file schema.yml
	@echo "OpenAPI schema generated: schema.yml"
