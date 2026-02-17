#!/bin/bash

# Get the DISPLAY variable from the host
export DISPLAY=${DISPLAY:-:0}

# Add current user to xhost (allow connections)
xhost +local:docker 2>/dev/null || echo "X11 forwarding may not be available"

# Start the Docker containers
echo "Starting Quiz App with Docker Compose..."
echo "Using DISPLAY: $DISPLAY"
docker compose up -d

# Show logs
echo ""
echo "Containers started. Showing logs (press Ctrl+C to exit):"
docker compose logs -f quizapp
