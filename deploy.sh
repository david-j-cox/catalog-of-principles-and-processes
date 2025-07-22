#!/bin/bash

# JEAB Catalog Deployment Script
# This script helps set up and deploy the JEAB Catalog application

set -e

echo "🚀 JEAB Catalog Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning "Creating .env file. Please update with your Railway DATABASE_URL"
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/jeab_database

# For Railway deployment, this will be automatically set by Railway
# DATABASE_URL=postgresql://railway_user:railway_password@railway_host:5432/railway_database

# Development settings
DEBUG=True
ENVIRONMENT=development
EOF
    fi
    
    # Create sample data
    print_status "Creating sample data..."
    python sample_data.py
    
    print_success "Backend setup complete"
    cd ..
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning "Creating .env file. Please update with your Railway backend URL"
        cat > .env << EOF
# API Configuration
# Update this with your Railway backend URL
REACT_APP_API_URL=https://your-railway-backend.up.railway.app

# For local development, use:
# REACT_APP_API_URL=http://localhost:8000
EOF
    fi
    
    print_success "Frontend setup complete"
    cd ..
}

# Run backend locally
run_backend() {
    print_status "Starting backend server..."
    cd backend
    source venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Run frontend locally
run_frontend() {
    print_status "Starting frontend development server..."
    cd frontend
    npm start
}

# Deploy to Railway
deploy_railway() {
    print_status "Deploying to Railway..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI is not installed. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
    
    # Login to Railway
    print_status "Logging into Railway..."
    railway login
    
    # Deploy
    print_status "Deploying backend to Railway..."
    cd backend
    railway up
    
    print_success "Backend deployed to Railway"
    cd ..
}

# Deploy to GitHub Pages
deploy_github_pages() {
    print_status "Deploying to GitHub Pages..."
    
    cd frontend
    
    # Update homepage in package.json
    print_status "Updating package.json homepage..."
    # This would need to be updated manually with the correct GitHub username
    
    # Build and deploy
    print_status "Building and deploying to GitHub Pages..."
    npm run deploy
    
    print_success "Frontend deployed to GitHub Pages"
    cd ..
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo "1. Check dependencies"
    echo "2. Setup backend"
    echo "3. Setup frontend"
    echo "4. Setup both backend and frontend"
    echo "5. Run backend locally"
    echo "6. Run frontend locally"
    echo "7. Deploy backend to Railway"
    echo "8. Deploy frontend to GitHub Pages"
    echo "9. Full deployment (Railway + GitHub Pages)"
    echo "0. Exit"
    echo ""
    read -p "Enter your choice (0-9): " choice
    
    case $choice in
        1) check_dependencies ;;
        2) setup_backend ;;
        3) setup_frontend ;;
        4) setup_backend && setup_frontend ;;
        5) run_backend ;;
        6) run_frontend ;;
        7) deploy_railway ;;
        8) deploy_github_pages ;;
        9) deploy_railway && deploy_github_pages ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo "Invalid choice. Please try again." ;;
    esac
}

# Check if script is run with arguments
if [ $# -eq 0 ]; then
    show_menu
else
    case $1 in
        "check") check_dependencies ;;
        "backend") setup_backend ;;
        "frontend") setup_frontend ;;
        "setup") setup_backend && setup_frontend ;;
        "run-backend") run_backend ;;
        "run-frontend") run_frontend ;;
        "deploy-railway") deploy_railway ;;
        "deploy-pages") deploy_github_pages ;;
        "deploy") deploy_railway && deploy_github_pages ;;
        *) echo "Usage: $0 [check|backend|frontend|setup|run-backend|run-frontend|deploy-railway|deploy-pages|deploy]" ;;
    esac
fi 