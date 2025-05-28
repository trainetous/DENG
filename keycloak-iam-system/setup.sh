#!/bin/bash

# Keycloak IAM System Setup Script
# This script automates the configuration and testing of the Keycloak IAM system

set -e

echo "🚀 Starting Keycloak IAM System Setup"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEYCLOAK_URL="http://localhost:8080"
FLASK_URL="http://localhost:5000"
REALM_NAME="flask-demo"
CLIENT_ID="flask-app"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_dependencies() {
    print_step "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    print_status "Dependencies check passed"
}

# Create necessary directories
create_directories() {
    print_step "Creating directories..."
    
    mkdir -p keycloak
    mkdir -p templates
    
    print_status "Directories created"
}

# Clean up any existing containers
cleanup_existing() {
    print_step "Cleaning up existing containers..."
    
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f >/dev/null 2>&1 || true
    
    print_status "Cleanup completed"
}

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=60
    local attempt=1
    
    print_step "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Start services
start_services() {
    print_step "Starting services with Docker Compose..."
    
    # Start services
    docker-compose up -d --build
    
    print_status "Docker containers started"
    
    # Wait for Keycloak to be ready (this takes longer)
    print_step "Waiting for Keycloak to fully initialize (this may take 2-3 minutes)..."
    wait_for_service "$KEYCLOAK_URL/health/ready" "Keycloak"
    
    # Wait for Flask app to be ready
    wait_for_service "$FLASK_URL/health" "Flask app"
    
    print_status "All services are running"
}

# Configure Keycloak
configure_keycloak() {
    print_step "Configuring Keycloak realm and users..."
    
    # Install required Python packages if not present
    python3 -c "import requests" 2>/dev/null || {
        print_warning "Installing required Python packages..."
        pip3 install requests >/dev/null 2>&1 || {
            print_error "Failed to install required packages. Please run: pip3 install requests"
            return 1
        }
    }
    
    # Run Keycloak configuration
    if python3 configure_keycloak.py; then
        print_status "Keycloak configuration completed"
        return 0
    else
        print_error "Keycloak configuration failed"
        return 1
    fi
}

# Test API endpoints
test_apis() {
    print_step "Testing API endpoints..."
    
    echo ""
    echo "🧪 API Test Results:"
    echo "==================="
    
    # Test public endpoint
    echo -n "Testing public API... "
    if curl -s -f "$FLASK_URL/api/public" > /dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL${NC}"
    fi
    
    # Test Keycloak token endpoint
    echo -n "Testing Keycloak token endpoint... "
    KEYCLOAK_TOKEN=$(curl -s -X POST "$FLASK_URL/api/keycloak-login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"adminpassword"}' 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)
    
    if [ -n "$KEYCLOAK_TOKEN" ] && [ "$KEYCLOAK_TOKEN" != "None" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        
        # Test Keycloak protected endpoint
        echo -n "Testing Keycloak protected API... "
        if curl -s -f -H "Authorization: Bearer $KEYCLOAK_TOKEN" "$FLASK_URL/api/protected" > /dev/null; then
            echo -e "${GREEN}✅ PASS${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        print_warning "Skipping Keycloak protected API test"
    fi
    
    # Test simple JWT token endpoint
    echo -n "Testing simple JWT token endpoint... "
    SIMPLE_TOKEN=$(curl -s -X POST "$FLASK_URL/api/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"password"}' 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('token', ''))" 2>/dev/null)
    
    if [ -n "$SIMPLE_TOKEN" ] && [ "$SIMPLE_TOKEN" != "None" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        
        # Test simple JWT protected endpoint
        echo -n "Testing simple JWT protected API... "
        if curl -s -f -H "Authorization: Bearer $SIMPLE_TOKEN" "$FLASK_URL/api/protected-simple" > /dev/null; then
            echo -e "${GREEN}✅ PASS${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        print_warning "Skipping simple JWT protected API test"
    fi
    
    # Test unauthorized access
    echo -n "Testing unauthorized access (should fail)... "
    if curl -s -f "$FLASK_URL/api/protected" > /dev/null 2>&1; then
        echo -e "${RED}❌ FAIL (should have been blocked)${NC}"
    else
        echo -e "${GREEN}✅ PASS (correctly blocked)${NC}"
    fi
}

# Display access information
show_access_info() {
    print_step "Setup complete! Access information:"
    
    echo ""
    echo "🌐 Service URLs:"
    echo "==============="
    echo "Flask Application: $FLASK_URL"
    echo "Keycloak Admin:    $KEYCLOAK_URL"
    echo "Keycloak Realm:    $KEYCLOAK_URL/realms/$REALM_NAME"
    
    echo ""
    echo "🔑 Test Credentials:"
    echo "==================="
    echo "Keycloak Admin:    admin / admin"
    echo "Keycloak Users:    admin / adminpassword"
    echo "                   testuser / testpassword"
    echo "Simple JWT:        admin / password"
    
    echo ""
    echo "🧪 Testing:"
    echo "==========="
    echo "1. Open $FLASK_URL in your browser"
    echo "2. Test both Keycloak and Simple JWT authentication"
    echo "3. Access Keycloak admin at $KEYCLOAK_URL (admin/admin)"
    echo "4. Run comprehensive tests: python3 test_apis.py"
    
    echo ""
    echo "📋 Manual API Testing:"
    echo "======================"
    echo "# Get Keycloak token:"
    echo "curl -X POST $FLASK_URL/api/keycloak-login \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"admin\",\"password\":\"adminpassword\"}'"
    
    echo ""
    echo "# Test protected endpoint:"
    echo "curl -H 'Authorization: Bearer <token>' $FLASK_URL/api/protected"
    
    echo ""
    echo "🔧 Management:"
    echo "=============="
    echo "Stop services:     docker-compose down"
    echo "View logs:         docker-compose logs -f"
    echo "Restart services:  docker-compose restart"
    echo "Full reset:        ./setup.sh"
}

# Run comprehensive tests
run_comprehensive_tests() {
    print_step "Running comprehensive API tests..."
    
    if [ -f "test_apis.py" ]; then
        if python3 test_apis.py; then
            print_status "All comprehensive tests passed!"
        else
            print_warning "Some comprehensive tests failed. Check the output above."
        fi
    else
        print_warning "test_apis.py not found. Skipping comprehensive tests."
    fi
}

# Main execution
main() {
    echo "Starting setup process..."
    
    check_dependencies
    create_directories
    cleanup_existing
    start_services
    
    # Configure Keycloak
    if configure_keycloak; then
        print_status "Keycloak configured successfully"
    else
        print_error "Keycloak configuration failed, but continuing with basic tests..."
    fi
    
    # Wait a bit for services to fully stabilize
    sleep 10
    
    test_apis
    show_access_info
    
    echo ""
    run_comprehensive_tests
    
    echo ""
    print_status "🎉 Keycloak IAM System setup completed!"
    echo ""
    print_warning "Keep this terminal open to see the setup information, or run 'docker-compose logs -f' to see service logs."
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Setup interrupted. Run \"docker-compose down\" to stop services.${NC}"; exit 1' INT

# Run main function
main "$@"
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"adminpassword"}' | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    
    if [ -n "$KEYCLOAK_TOKEN" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        
        # Test Keycloak protected endpoint
        echo -n "Testing Keycloak protected API... "
        if curl -s -f -H "Authorization: Bearer $KEYCLOAK_TOKEN" "$FLASK_URL/api/protected" > /dev/null; then
            echo -e "${GREEN}✅ PASS${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        print_warning "Skipping Keycloak protected API test"
    fi
    
    # Test simple JWT token endpoint
    echo -n "Testing simple JWT token endpoint... "
    SIMPLE_TOKEN=$(curl -s -X POST "$FLASK_URL/api/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"password"}' | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
    
    if [ -n "$SIMPLE_TOKEN" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        
        # Test simple JWT protected endpoint
        echo -n "Testing simple JWT protected API... "
        if curl -s -f -H "Authorization: Bearer $SIMPLE_TOKEN" "$FLASK_URL/api/protected-simple" > /dev/null; then
            echo -e "${GREEN}✅ PASS${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        print_warning "Skipping simple JWT protected API test"
    fi
    
    # Test unauthorized access
    echo -n "Testing unauthorized access (should fail)... "
    if curl -s -f "$FLASK_URL/api/protected" > /dev/null 2>&1; then
        echo -e "${RED}❌ FAIL (should have been blocked)${NC}"
    else
        echo -e "${GREEN}✅ PASS (correctly blocked)${NC}"
    fi
}

# Display access information
show_access_info() {
    print_step "Setup complete! Access information:"
    
    echo ""
    echo "🌐 Service URLs:"
    echo "==============="
    echo "Flask Application: $FLASK_URL"
    echo "Keycloak Admin:    $KEYCLOAK_URL"
    echo "Keycloak Realm:    $KEYCLOAK_URL/realms/$REALM_NAME"
    
    echo ""
    echo "🔑 Test Credentials:"
    echo "==================="
    echo "Keycloak Admin:    admin / admin"
    echo "Keycloak Users:    admin / adminpassword"
    echo "                   testuser / testpassword"
    echo "Simple JWT:        admin / password"
    
    echo ""
    echo "🧪 Testing:"
    echo "==========="
    echo "1. Open $FLASK_URL in your browser"
    echo "2. Test both Keycloak and Simple JWT authentication"
    echo "3. Access Keycloak admin at $KEYCLOAK_URL (admin/admin)"
    
    echo ""
    echo "📋 Manual API Testing:"
    echo "======================"
    echo "# Get Keycloak token:"
    echo "curl -X POST $FLASK_URL/api/keycloak-login \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"admin\",\"password\":\"adminpassword\"}'"
    
    echo ""
    echo "# Test protected endpoint:"
    echo "curl -H 'Authorization: Bearer <token>' $FLASK_URL/api/protected"
    
    echo ""
    echo "🔧 Management:"
    echo "=============="
    echo "Stop services:     docker-compose down"
    echo "View logs:         docker-compose logs -f"
    echo "Restart services:  docker-compose restart"
}

# Main execution
main() {
    echo "Starting setup process..."
    
    check_dependencies
    create_directories
    start_services
    
    # Wait a bit for services to fully initialize
    sleep 5
    
    test_apis
    show_access_info
    
    echo ""
    print_status "🎉 Keycloak IAM System setup completed successfully!"
    echo ""
    print_warning "Keep this terminal open to see the setup information, or run 'docker-compose logs -f' to see service logs."
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Setup interrupted. Run \"docker-compose down\" to stop services.${NC}"; exit 1' INT

# Run main function
main "$@"