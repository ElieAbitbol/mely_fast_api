<!-- README.md -->

## ✅ Environment Setup

### 📄 `.env.example`

Copy this file as `.env` and adjust values for local development or CI/CD.

```dotenv
# Docker Hub credentials (used by GitHub Actions)
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password-or-token

# App configuration
PORT=8000
IMAGE_NAME=fastapi-image
CONTAINER_NAME=fastapi-container

# Git SHA tag for pushed Docker image
GIT_SHA=latest
```

> ✅ Rename this file manually:

```bash
cp .env.example .env
```

---

## 🔐 GitHub Actions — Add Secrets

In **GitHub → Settings → Secrets → Actions**, add the following:

| Secret Name       | Description                       |
| ----------------- | --------------------------------- |
| `DOCKER_USERNAME` | Your Docker Hub username          |
| `DOCKER_PASSWORD` | Your Docker Hub password or token |

---

## 🛠️ Makefile Targets Reference

You can manage your app lifecycle using these commands:

| Command                    | Description                                                |
| -------------------------- | ---------------------------------------------------------- |
| `make`                     | Build and run the app on default port (`PORT`)             |
| `make run`                 | Run the container                                          |
| `make run PORT=8080`       | Run on a custom port                                       |
| `make up`                  | Run in **dev mode** with live reload and volume mount      |
| `make stop`                | Stop and remove the container                              |
| `make clean`               | Remove the Docker image                                    |
| `make deploy`              | Full CI/CD flow: build → run → test → stop                 |
| `make test`                | Call `/data` and `/ping` endpoints to verify availability  |
| `make lint`                | Lint code using `flake8`                                   |
| `make format`              | Format code using `black` and `isort`                      |
| `make autofix`             | Auto-fix with `autopep8`, `black`, `isort`                 |
| `make check`               | Run lint + format + endpoint tests                         |
| `make push`                | Push Docker image to Docker Hub using `GIT_SHA` as the tag |
| `make push GIT_SHA=abc123` | Push with a custom tag                                     |
| `make prune`               | Remove all stopped containers                              |
| `make prune-all`           | Full system cleanup: remove all unused images/containers   |

---