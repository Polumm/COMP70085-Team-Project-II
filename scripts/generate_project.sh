#!/usr/bin/env bash
#
# generate_project.sh
# -------------------
# This script creates a sample monorepo structure for a microservices project
# with a frontend, multiple services, infrastructure configurations, and more.

# Exit immediately if a command exits with a non-zero status:
set -e

# Use first argument as PROJECT_NAME or default to 'my-microservices-project'
PROJECT_NAME=${1:-my-microservices-project}

echo "Creating project structure in folder: $PROJECT_NAME ..."
echo

# 1. Create the main project folder and subfolders
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# 2. docs/ folder
mkdir -p docs/architecture-diagrams
touch docs/design-decisions.md

# 3. infrastructure/ folder
mkdir -p infrastructure/terraform
mkdir -p infrastructure/k8s-manifests
cat <<EOF > infrastructure/docker-compose.yml
version: '3'
services:
  # Example microservice definitions:
  user-service:
    build: ../services/user-service
    ports:
      - "3001:3001"
  chat-service:
    build: ../services/chat-service
    ports:
      - "3002:3002"
  gateway-service:
    build: ../services/gateway-service
    ports:
      - "8080:8080"
EOF

# 4. scripts/ folder
mkdir -p scripts
cat <<'EOF' > scripts/init.sh
#!/usr/bin/env bash
# Initialize or bootstrap the local environment (e.g., create .env files)
echo "Initializing environment..."
EOF

cat <<'EOF' > scripts/build.sh
#!/usr/bin/env bash
# Build script for all services (sample usage)
echo "Building all services..."
for service in services/*-service; do
  echo "Building $service..."
  (cd "$service" && docker build -t "$(basename "$service")":latest .)
done
EOF

cat <<'EOF' > scripts/deploy.sh
#!/usr/bin/env bash
# Deploy script (sample usage, adjust for your environment)
echo "Deploying to target environment..."
EOF

chmod +x scripts/*.sh

# 5. .github/ for GitHub workflows
mkdir -p .github/workflows
cat <<EOF > .github/workflows/ci-cd.yaml
name: CI-CD

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repo
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build and test each service
        run: |
          for service in services/*-service; do
            echo "Building and testing \$service"
            cd \$service
            # Example: npm install && npm test (or appropriate command for your stack)
            # Build Docker image
            docker build -t "\$service:latest" .
            cd ../..
EOF

cat <<EOF > .github/PULL_REQUEST_TEMPLATE.md
## Description
A short summary of the changes you've made and why.

## Testing
What did you test, and how?

## Related Issues
Link to any issues or tickets that this PR addresses.

## Additional Context
Add any other context or screenshots about the pull request here.
EOF

# 6. Top-level files
touch .gitignore
touch LICENSE
echo "# $PROJECT_NAME" > README.md
echo "Basic project structure created by generate_project.sh" >> README.md

# 7. services/ folder (Sample microservices)
mkdir -p services/user-service/src
mkdir -p services/user-service/tests
cat <<EOF > services/user-service/Dockerfile
# Example Dockerfile for user-service
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
EOF
cat <<EOF > services/user-service/README.md
# User Service
Handles user-related operations such as registration, login, and profile management.

## Getting Started
- \`npm install\`
- \`npm start\`

## Endpoints
- POST /users
- GET /users/:id
EOF

mkdir -p services/user-service/migrations
touch services/user-service/migrations/20230101_create_users_table.sql

# Chat-service
mkdir -p services/chat-service/src
mkdir -p services/chat-service/tests
cat <<EOF > services/chat-service/Dockerfile
# Example Dockerfile for chat-service
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3002
CMD ["npm", "start"]
EOF
cat <<EOF > services/chat-service/README.md
# Chat Service
Manages chat sessions, messages, and interactions with the LLM (if any).

## Getting Started
- \`npm install\`
- \`npm start\`

## Endpoints
- POST /chats
- GET /chats/:id
EOF

mkdir -p services/chat-service/migrations
touch services/chat-service/migrations/20230101_create_chat_table.sql

# Gateway-service
mkdir -p services/gateway-service/src
mkdir -p services/gateway-service/tests
cat <<EOF > services/gateway-service/Dockerfile
# Example Dockerfile for gateway-service
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "start"]
EOF
cat <<EOF > services/gateway-service/README.md
# Gateway Service
Acts as an API gateway or reverse proxy, routing external requests to appropriate microservices.

## Getting Started
- \`npm install\`
- \`npm start\`

## Routes
- /api/users -> user-service
- /api/chats -> chat-service
EOF

# 8. Frontend folder
mkdir -p frontend/src
mkdir -p frontend/public
cat <<EOF > frontend/package.json
{
  "name": "frontend",
  "version": "1.0.0",
  "description": "Example frontend for the microservices project",
  "scripts": {
    "start": "echo 'Starting frontend... (Replace with React/Vue/Angular command)'",
    "build": "echo 'Building frontend... (Replace with build command)'"
  },
  "dependencies": {},
  "devDependencies": {}
}
EOF
cat <<EOF > frontend/README.md
# Frontend
A sample frontend that consumes the Gateway Service and other microservices.

## Getting Started
- \`npm install\`
- \`npm start\`

## Build
- \`npm run build\`
EOF

# 9. libs folder (optional shared code)
mkdir -p libs/external-apis/src
cat <<EOF > libs/external-apis/package.json
{
  "name": "external-apis",
  "version": "1.0.0",
  "description": "Shared library for external API calls",
  "main": "src/index.js",
  "dependencies": {},
  "devDependencies": {}
}
EOF

# Final output
echo
echo "✅ Project structure created successfully in: $PROJECT_NAME"
echo "You can now explore the newly created folders and files."
