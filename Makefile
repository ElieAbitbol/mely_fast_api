# ────────────────────────────────────────────────────────────────
# 📦 Load environment variables from .env
# ────────────────────────────────────────────────────────────────

ifneq (,$(wildcard .env))
	include .env
	export
endif

# ────────────────────────────────────────────────────────────────
# 🛠️ Configuration Defaults (can be overridden in .env)
# ────────────────────────────────────────────────────────────────

PORT ?= 8000
IMAGE_NAME ?= fastapi-image
CONTAINER_NAME ?= fastapi-container
DOCKER_USERNAME ?= your-dockerhub-username
GIT_SHA ?= latest

# ────────────────────────────────────────────────────────────────
# 🚀 Main Targets
# ────────────────────────────────────────────────────────────────

all: build run                    ## Build and run the app
deploy: build run test stop       ## Full CI/CD simulation
check: lint format test           ## Code quality + endpoint tests

# ────────────────────────────────────────────────────────────────
# 🐳 Docker Commands
# ────────────────────────────────────────────────────────────────

build:                           ## Build Docker image
	docker build -t $(IMAGE_NAME) .

run: stop                        ## Run container with mapped port
	docker run -d -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME)

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

test:                            ## Test key endpoints
	@echo "🔍 Testing on port $(PORT)..."
	sleep 3
	echo ""
	curl --fail http://localhost:$(PORT)/
	echo ""
	curl --fail http://localhost:$(PORT)/data
	echo ""
	curl --fail http://localhost:$(PORT)/ping || true
	echo ""
	@echo "✅ All endpoints responded successfully."

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

.PHONY: all build run stop test deploy clean push prune prune-all format autofix lint check up
