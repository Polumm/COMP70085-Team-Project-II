#!/usr/bin/env bash
# Build script for all services (sample usage)
echo "Building all services..."
for service in services/*-service; do
  echo "Building $service..."
  (cd "$service" && docker build -t "$(basename "$service")":latest .)
done
