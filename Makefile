.PHONY: init up down logs ps restart clean

# Initialize the project
init:
	@echo "Creating .env file from example..."
	cp .env.example .env
	@echo "Initializing git repository..."
	git init

# Start all services in detached mode
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# View logs for all services
logs:
	docker-compose logs -f

# List running containers
ps:
	docker-compose ps

# Restart all services
restart:
	docker-compose restart

# Stop and remove all containers, networks, and volumes
clean:
	docker-compose down -v

# Format Python code
format:
	docker-compose run --rm api-gateway black .
	docker-compose run --rm api-gateway isort .

# Run tests
test:
	docker-compose run --rm api-gateway pytest

# Initialize the database
init-db:
	@echo "Initializing database..."
	# Add database initialization commands here

# Create and start all services
setup: init up

# Show help
help:
	@echo "Available targets:"
	@echo "  init      - Initialize the project (create .env, git init)"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - View logs for all services"
	@echo "  ps        - List running containers"
	@echo "  restart   - Restart all services"
	@echo "  clean     - Stop and remove all containers, networks, and volumes"
	@echo "  format    - Format Python code"
	@echo "  test      - Run tests"
	@echo "  setup     - Initialize and start all services"
	@echo "  help      - Show this help message"
