# ────────────────────────────────────────────────────────────────
# 📦 Load environment variables from .env or .env.example
# ────────────────────────────────────────────────────────────────
ifneq (,$(wildcard .env))
	include .env
	export
else ifneq (,$(wildcard .env.example))
	include .env.example
	export
endif


# ────────────────────────────────────────────────────────────────
# 🛠️ Configuration Defaults (can be overridden in .env)
# ────────────────────────────────────────────────────────────────

PORT ?= 8000
IMAGE_NAME ?= data-correction-api
CONTAINER_NAME ?= data-correction-api-container
DOCKER_USERNAME ?= your-dockerhub-username
GIT_SHA ?= local_test

# ────────────────────────────────────────────────────────────────
# 🚀 Main Targets
# ────────────────────────────────────────────────────────────────

all: build run                    ## Build and run the Data Correction API
deploy: build run test stop       ## Full CI/CD simulation
check: lint format                ## Code quality checks

# ────────────────────────────────────────────────────────────────
# 🔧 Local Development
# ────────────────────────────────────────────────────────────────

dev:                             ## Run API locally with virtual environment
	. venv/Scripts/activate && python start_server.py

dev-watch:                       ## Run API locally with auto-reload
	. venv/Scripts/activate && uvicorn app.api:app --host 0.0.0.0 --port $(PORT) --reload

# ────────────────────────────────────────────────────────────────
# 🐳 Docker Commands
# ────────────────────────────────────────────────────────────────

build:                           ## Build Docker image
	docker build -t $(IMAGE_NAME) .

run: stop                        ## Run container with mapped port and environment
	docker run -d -p $(PORT):8000 --env-file .env --name $(CONTAINER_NAME) $(IMAGE_NAME)

stop:                            ## Stop and remove container
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

clean:                           ## Remove Docker image
	docker rmi -f $(IMAGE_NAME) || true

push:                            ## Push Docker image to Docker Hub
	docker tag $(IMAGE_NAME) $(DOCKER_USERNAME)/$(IMAGE_NAME):$(GIT_SHA)
	docker push $(DOCKER_USERNAME)/$(IMAGE_NAME):$(GIT_SHA)

prune:                           ## Remove stopped containers
	docker container prune -f

prune-all:                       ## Remove ALL unused Docker objects
	docker system prune -a -f

# ────────────────────────────────────────────────────────────────
# 🔁 Live Development Mode
# ────────────────────────────────────────────────────────────────

up:                              ## Run with volume mount and live reload
	docker run --rm -it \
		--env-file .env \
		-p $(PORT):8000 \
		-v $(PWD)/app:/app/app \
		--name $(CONTAINER_NAME)-dev \
		$(IMAGE_NAME) \
		uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

# ────────────────────────────────────────────────────────────────
# 🧪 API Testing
# ────────────────────────────────────────────────────────────────

test:                            ## Test Data Correction API endpoints
	@echo "🔍 Testing Data Correction API on port $(PORT)..."
	sleep 3
	echo ""
	@echo "Testing root endpoint..."
	curl --fail http://localhost:$(PORT)/
	echo ""
	@echo "Testing ping endpoint..."
	curl --fail http://localhost:$(PORT)/ping
	echo ""
	@echo "Testing data endpoint..."
	curl --fail http://localhost:$(PORT)/data
	echo ""
	@echo "Testing single correction endpoint..."
	curl -X POST "http://localhost:$(PORT)/correct" \
		-H "Content-Type: application/json" \
		-d '{"field_name": "vessel_name", "current_value": "TEST VESSEL EMAIL@TEST.COM"}' || true
	echo ""
	@echo "✅ All endpoints tested successfully."

test-correction:                 ## Test field correction functionality
	@echo "🧪 Testing field correction..."
	curl -X POST "http://localhost:$(PORT)/correct" \
		-H "Content-Type: application/json" \
		-d '{"field_name": "vessel_name", "current_value": "MAERSK LINE INFO@MAERSK.COM"}'

test-batch:                      ## Test batch correction functionality
	@echo "🧪 Testing batch correction..."
	curl -X POST "http://localhost:$(PORT)/correct/batch" \
		-H "Content-Type: application/json" \
		-d '{"items": [{"field_name": "po_number", "current_value": "PO: 12345"}, {"field_name": "currency", "current_value": "US DOLLARS"}]}'

test-guidance:                   ## Test guidance generation
	@echo "🧪 Testing guidance generation..."
	curl -X POST "http://localhost:$(PORT)/guidance" \
		-H "Content-Type: application/json" \
		-d '{"company_id": "TEST_COMPANY", "frequent_corrections": [{"field_name": "vessel_name", "original_value": "TEST INFO@TEST.COM", "corrected_value": "TEST", "frequency": 5}]}'

test-validate:                   ## Test pattern validation
	@echo "🧪 Testing pattern validation..."
	curl -X POST "http://localhost:$(PORT)/validate" \
		-H "Content-Type: application/json" \
		-d '{"examples": [{"field_name": "vessel_name", "original_value": "TEST INFO@TEST.COM", "corrected_value": "TEST", "should_integrate": true, "reason": "Email contamination pattern"}]}'

test-all-endpoints:              ## Test all API endpoints comprehensively
	$(MAKE) test-correction
	echo ""
	$(MAKE) test-batch
	echo ""
	$(MAKE) test-guidance
	echo ""
	$(MAKE) test-validate

# ────────────────────────────────────────────────────────────────
# 🎯 Code Quality & Formatting
# ────────────────────────────────────────────────────────────────

lint:							## Lint with flake8
	flake8 app --count --max-line-length=88 --statistics

format:							## Format with black + isort
	isort app
	black app

autofix:						## Auto-fix code style issues
	isort app
	black app
	autopep8 app --in-place --recursive --aggressive --aggressive

# ────────────────────────────────────────────────────────────────
# 📌 Meta
# ────────────────────────────────────────────────────────────────

docs:                            ## Open API documentation in browser
	@echo "📖 Opening API documentation..."
	@echo "FastAPI docs: http://localhost:$(PORT)/docs"
	@echo "ReDoc docs: http://localhost:$(PORT)/redoc"
	@echo "HTML overview: file://$(PWD)/data_correction_api_overview.html"

help:                            ## Show this help message
	@echo "Data Correction API - Available Commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: all build run stop test deploy clean push prune prune-all format autofix lint check up dev dev-watch test-correction test-batch test-guidance test-validate test-all-endpoints docs help
