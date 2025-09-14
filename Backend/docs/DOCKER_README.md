# Simple Docker Setup

## Quick Start

1. Copy environment file:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` file with your values

3. Build and run:
   ```bash
   docker-compose up --build
   ```

4. Access the application at `http://localhost:8000`

## Environment Variables

- `SECRET_KEY`: Django secret key
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `EMAIL_HOST_USER`: Email username
- `EMAIL_HOST_PASSWORD`: Email password
- `JWT_SECRET_KEY`: JWT secret key

## Files

- `Dockerfile`: Simple Python Alpine container
- `docker-compose.yaml`: Basic service configuration
- `.dockerignore`: Excludes unnecessary files
- `env.template`: Environment variables template
