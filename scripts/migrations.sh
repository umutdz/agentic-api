#!/bin/bash

# Migration script for agentic-api
# Usage: ./scripts/migrations.sh <command> [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Migration script for agentic-api"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Available commands:"
    echo "  initial          Make an initial migration"
    echo "  make <message>   Make a new migration with message"
    echo "  upgrade          Upgrade migrations to head"
    echo "  downgrade        Downgrade migrations by 1"
    echo "  downgrade-zero   Downgrade migrations to base"
    echo "  show             Show migration history"
    echo "  current          Show current migration"
    echo "  back <id>        Downgrade to specific migration ID"
    echo "  forward <id>     Upgrade to specific migration ID"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 initial"
    echo "  $0 make 'add user table'"
    echo "  $0 upgrade"
    echo "  $0 show"
}

# Function to make initial migration
initial_migration() {
    print_info "Making initial migration..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini revision --autogenerate -m "initial migration"
    print_success "Initial migration created successfully"
}

# Function to make new migration
make_migration() {
    if [ -z "$1" ]; then
        print_error "Migration message is required"
        echo "Usage: $0 make <message>"
        exit 1
    fi

    print_info "Making new migration: $1"
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini revision --autogenerate -m "$1"
    print_success "Migration created successfully"
}

# Function to upgrade migrations
upgrade_migrations() {
    print_info "Upgrading migrations to head..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini upgrade head
    print_success "Migrations upgraded successfully"
}

# Function to downgrade migrations
downgrade_migrations() {
    print_warning "Downgrading migrations by 1..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini downgrade -1
    print_success "Migrations downgraded successfully"
}

# Function to downgrade to base
downgrade_zero() {
    print_warning "Downgrading migrations to base..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini downgrade base
    print_success "Migrations downgraded to base"
}

# Function to show migrations
show_migrations() {
    print_info "Showing migration history..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini history
}

# Function to show current migration
current_migrations() {
    print_info "Showing current migration..."
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini current
}

# Function to go back to specific migration
back_migration() {
    if [ -z "$1" ]; then
        print_error "Migration ID is required"
        echo "Usage: $0 back <migration_id>"
        exit 1
    fi

    print_warning "Downgrading to migration: $1"
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini downgrade "$1"
    print_success "Downgraded to migration: $1"
}

# Function to go forward to specific migration
forward_migration() {
    if [ -z "$1" ]; then
        print_error "Migration ID is required"
        echo "Usage: $0 forward <migration_id>"
        exit 1
    fi

    print_info "Upgrading to migration: $1"
    docker compose run --rm agentic_api_app alembic -c /app/alembic.ini upgrade "$1"
    print_success "Upgraded to migration: $1"
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi

    case "$1" in
        "initial")
            initial_migration
            ;;
        "make")
            make_migration "$2"
            ;;
        "upgrade")
            upgrade_migrations
            ;;
        "downgrade")
            downgrade_migrations
            ;;
        "downgrade-zero")
            downgrade_zero
            ;;
        "show")
            show_migrations
            ;;
        "current")
            current_migrations
            ;;
        "back")
            back_migration "$2"
            ;;
        "forward")
            forward_migration "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Invalid command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
