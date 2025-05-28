# Keycloak IAM System

A comprehensive Identity and Access Management (IAM) system demonstrating Flask API integration with Keycloak for secure authentication and authorization.

## Requirements Met

This project fulfills all specified requirements:

1. **Set Up Keycloak**
   - Docker Compose configuration for Keycloak and Flask app
   - Custom realm (`flask-demo`) with pre-configured client and users
   - Automated realm import with proper client settings

2. **Protect the Flask API**
   - Token validation middleware for both Keycloak and simple JWT tokens
   - Secure protected routes with proper authentication checks
   - Handles both authenticated and unauthenticated requests correctly

3. **Test the Setup**
   - Automated setup script (`setup.sh`) for complete configuration
   - Comprehensive test suite (`test_apis.py`) validating all endpoints
   - Interactive web interface for manual API testing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask App     │    │   Keycloak      │
│                 │◄──►│                 │◄──►│                 │
│ - Interactive   │    │ - API Endpoints │    │ - Authentication│
│   Testing UI    │    │ - Token Valid.  │    │ - User Mgmt     │
│ - Login Pages   │    │ - Protected     │    │ - JWT Tokens    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone and navigate to project
git clone <your-repo-url>
cd keycloak-iam-system

# Run automated setup
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# Start services
docker-compose up -d

# Wait for services to be ready (60-90 seconds)

# Test the setup
python3 test_apis.py
```

## Project Structure

```
keycloak-iam-system/
├── app.py                      # Main Flask application
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Flask app container
├── requirements.txt            # Python dependencies
├── setup.sh                   # Automated setup script
├── test_apis.py               # Comprehensive API tests
├── keycloak/
│   └── realm-export.json      # Keycloak realm configuration
└── templates/
    ├── index.html             # Main testing interface
    ├── simple_login.html      # Simple login form
    └── dashboard.html         # User dashboard
```

## Authentication Methods

### 1. Keycloak OIDC Authentication
- **Realm**: `flask-demo`
- **Client**: `flask-app`
- **Users**: 
  - `admin` / `adminpassword` (admin role)
  - `testuser` / `testpassword` (user role)

### 2. Simple JWT Authentication
- **User**: `admin` / `password`
- Self-contained JWT tokens for backwards compatibility

## API Endpoints

### Public Endpoints
- `GET /` - Main web interface
- `GET /api/public` - Public API (no auth required)
- `GET /health` - Health check

### Authentication Endpoints
- `POST /api/keycloak-login` - Get Keycloak token
- `POST /api/login` - Get simple JWT token
- `GET /keycloak-login` - Web-based Keycloak login
- `GET /simple-login` - Simple web login

### Protected Endpoints
- `GET /api/protected` - Requires Keycloak token
- `GET /api/protected-simple` - Requires simple JWT token
- `GET /dashboard` - User dashboard (web session)

## Testing

### Interactive Web Testing
1. Open http://localhost:5000
2. Use the button interface to test:
   - 🟢 Public API access
   - 🔵 Token generation
   - 🔴 Protected endpoint access
   - ⚫ Results management

### Automated API Testing
```bash
# Run comprehensive test suite
python3 test_apis.py

# Expected output: All tests should pass
# Tests include: authentication, authorization, security validation
```

### Manual API Testing

**Get Keycloak Token:**
```bash
curl -X POST http://localhost:5000/api/keycloak-login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpassword"}'
```

**Access Protected Endpoint:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/protected
```

**Test Unauthorized Access (should fail):**
```bash
curl http://localhost:5000/api/protected
# Expected: HTTP 401 Unauthorized
```

## Security Features

- ✅ **Token Validation**: Proper JWT signature verification
- ✅ **Authorization Headers**: Bearer token implementation
- ✅ **Access Control**: Protected endpoints block unauthorized access
- ✅ **Invalid Token Handling**: Proper error responses
- ✅ **Session Management**: Secure web session handling
- ✅ **OIDC Compliance**: Standard OpenID Connect flow

##  Docker Configuration

### Services
- **Keycloak**: `localhost:8080` (admin/admin)
- **Flask App**: `localhost:5000`

### Environment Variables
- `KEYCLOAK_URL`: Keycloak server URL
- `FLASK_ENV`: Flask environment (development/production)

## 📊 Test Results

The test suite validates:

1. **Public Access**: Unauthenticated endpoints work
2. **Authentication**: Both Keycloak and JWT login work
3. **Authorization**: Tokens grant access to protected resources
4. **Security**: Unauthorized and invalid requests are blocked
5. **Health**: All services are operational

Example test output:
```
🧪 Starting Comprehensive API Testing
════════════════════════════════════

✅ Health Check: healthy
✅ Public API: accessible without authentication  
✅ Keycloak Admin Login: token obtained
✅ Keycloak Protected API: access granted
✅ Unauthorized Access: correctly blocked (HTTP 401)
✅ Invalid Token: correctly rejected (HTTP 401)

🎉 ALL TESTS PASSED (10/10)

🔒 Security Validation:
✅ Unauthorized access blocked
✅ Invalid tokens rejected  
✅ Keycloak authentication working
✅ Protected endpoints secured
```

##  Management Commands

```bash
# View service logs
docker-compose logs -f

# Restart services  
docker-compose restart

# Stop services
docker-compose down

# Rebuild Flask app
docker-compose build flask-app

# Access Keycloak admin
open http://localhost:8080
# Login: admin/admin
```

## 🔧 Keycloak Configuration

The system automatically configures:

- **Realm**: `flask-demo`
- **Client**: `flask-app` with proper redirect URIs
- **Users**: Pre-created with different roles
- **Roles**: Realm and client-specific roles
- **Groups**: User organization structure

Access Keycloak admin at http://localhost:8080 (admin/admin) to modify configuration.

##  Troubleshooting

### Services Won't Start
```bash
# Check Docker
docker --version
docker-compose --version

# Clean restart
docker-compose down
docker-compose up -d --build
```

### Keycloak Not Ready
```bash
# Check Keycloak health
curl http://localhost:8080/health/ready

# View Keycloak logs
docker-compose logs keycloak
```

### API Tests Failing
```bash
# Verify services are running
curl http://localhost:5000/health
curl http://localhost:8080/health/ready

# Check network connectivity
docker-compose ps
```

### Token Issues
- Verify credentials match the realm configuration
- Check token expiration (default: 5 minutes for Keycloak)
- Ensure proper Authorization header format: `Bearer <token>`

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Flask-OIDC Integration](https://flask-oidc.readthedocs.io/)
- [JWT Token Validation](https://pyjwt.readthedocs.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 🎯 Next Steps

This foundation can be extended with:

- Role-based access control (RBAC)
- Multi-tenant support
- API rate limiting
- Token refresh mechanisms
- Integration with external identity providers
- Production deployment configurations

