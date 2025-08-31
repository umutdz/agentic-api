# Docker Setup Guide for Agentic API

This guide provides comprehensive instructions for setting up and running the Agentic API application using Docker Compose in a local development environment.

## Prerequisites

Before starting, ensure you have the following installed:
- Docker and Docker Compose
- Git
- OpenAI API key
- SERPAPI API key (for content research functionality)

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd agentic-api

# Copy environment file
cp .env.example .env

# Create and activate virtual environment using uv with specific Python version
uv venv --python 3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies using uv
uv sync

```

### 2. Configure Environment
Edit the `.env` file with your configuration:
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here

# Database Configuration
MONGODB_URL=mongodb://localhost:27017/agentic_api
POSTGRES_URL=postgresql://user:password@localhost:5432/agentic_api

# Redis Configuration
REDIS_URL=redis://localhost:6379

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

### 3. Build and Start Services
```bash
# Build all services
docker compose build --no-cache

# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

### 4. Access Services
Once all services are running, you can access:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Flower Dashboard**: http://localhost:5555
- **MongoDB**: localhost:27017
- **Mongo Express (MongoDB Admin)**: http://localhost:8081
  - **Username**: `admin`
  - **Password**: `pass`
- **PostgreSQL**: localhost:5432
- **pgAdmin (PostgreSQL Admin)**: http://localhost:81
  - **Email**: Configured via `PGADMIN_DEFAULT_EMAIL` in `.env`
  - **Password**: Configured via `PGADMIN_DEFAULT_PASSWORD` in `.env`
- **Redis**: localhost:6379
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Database Setup

### Initial Setup
The application uses both MongoDB and PostgreSQL. MongoDB stores jobs and log events, while PostgreSQL handles user management and Celery results.

### Running Migrations
Use the provided migration script for database operations:

```bash
# Make the script executable
chmod +x scripts/migrations.sh

# Run initial migration
./scripts/migrations.sh initial

# Upgrade to latest migration
./scripts/migrations.sh upgrade

# Show migration history
./scripts/migrations.sh show

# Show current migration
./scripts/migrations.sh current
```

### Migration Commands Reference
```bash
# Create new migration
./scripts/migrations.sh make "add new feature"

# Downgrade by 1 step
./scripts/migrations.sh downgrade

# Downgrade to base
./scripts/migrations.sh downgrade-zero

# Go to specific migration
./scripts/migrations.sh back <migration_id>
./scripts/migrations.sh forward <migration_id>
```

## Environment Variables

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key for LLM operations
- `SERPAPI_API_KEY`: Your SERPAPI key for web content research
- `SECRET_KEY`: JWT secret key for authentication
- `MONGODB_URL`: MongoDB connection string
- `POSTGRES_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

### Optional Variables
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT`: Environment name (development, staging, production)
- `CORS_ORIGINS`: Allowed CORS origins
- `RATE_LIMIT_PER_MINUTE`: API rate limiting

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
docker compose logs <service_name>

# Verify environment variables
docker compose config

# Rebuild service
docker compose build --no-cache <service_name>
```

#### Database Connection Issues
```bash
# Check database status
docker compose ps mongodb postgres

# Verify connection strings in .env
# Ensure ports are not conflicting with local services
```

#### Celery Worker Issues
```bash
# Check worker logs
docker compose logs -f celery

# Restart worker
docker compose restart celery

# Verify RabbitMQ is running
docker compose exec rabbitmq rabbitmqctl status
```

### Performance Tuning
```bash
# Increase worker count
docker compose up -d --scale celery=4

# Monitor resource usage
docker stats

# Check queue status
docker compose exec rabbitmq rabbitmqctl list_queues
```

## Next Steps

After successful setup:
1. **Test the API**: Visit http://localhost:8000/docs
2. **Create your first task**: Use the `/api/v1/agent/execute` endpoint
3. **Monitor jobs**: Check the Celery Flower dashboard
4. **Review logs**: Monitor MongoDB for job and log events

<!-- For production deployment, refer to our [Production Deployment Guide](production_deployment.md). -->
