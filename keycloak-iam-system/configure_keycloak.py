#!/usr/bin/env python3
"""
Keycloak Configuration Script
Automatically configures Keycloak with realm, client, and users after startup
"""

import requests
import json
import time
import sys
from requests.auth import HTTPBasicAuth

# Configuration
KEYCLOAK_URL = "http://localhost:8080"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
REALM_NAME = "flask-demo"
CLIENT_ID = "flask-app"
CLIENT_SECRET = "flask-app-secret-key-12345"

class KeycloakConfigurator:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.base_url = KEYCLOAK_URL
        
    def log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "ERROR": "\033[91m",
            "WARNING": "\033[93m"
        }
        color = colors.get(level, "\033[0m")
        print(f"{color}[{timestamp}] {level}: {message}\033[0m")
        
    def wait_for_keycloak(self, max_attempts=30):
        """Wait for Keycloak to be ready"""
        self.log("Waiting for Keycloak to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.base_url}/health/ready", timeout=5)
                if response.status_code == 200:
                    self.log("Keycloak is ready!", "SUCCESS")
                    return True
            except requests.RequestException:
                pass
                
            if attempt < max_attempts - 1:
                print(".", end="", flush=True)
                time.sleep(2)
        
        self.log("Keycloak failed to start within expected time", "ERROR")
        return False
        
    def get_admin_token(self):
        """Get admin token for API access"""
        self.log("Getting admin token...")
        
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.admin_token}',
                    'Content-Type': 'application/json'
                })
                self.log("Admin token obtained", "SUCCESS")
                return True
            else:
                self.log(f"Failed to get admin token: {response.status_code}", "ERROR")
                return False
        except requests.RequestException as e:
            self.log(f"Error getting admin token: {e}", "ERROR")
            return False
            
    def create_realm(self):
        """Create the flask-demo realm"""
        self.log(f"Creating realm: {REALM_NAME}")
        
        realm_config = {
            "realm": REALM_NAME,
            "enabled": True,
            "displayName": "Flask Demo Realm",
            "accessTokenLifespan": 300,
            "ssoSessionIdleTimeout": 1800,
            "ssoSessionMaxLifespan": 36000,
            "requiredCredentials": ["password"],
            "registrationAllowed": False,
            "rememberMe": True,
            "verifyEmail": False,
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False
        }
        
        try:
            response = self.session.post(f"{self.base_url}/admin/realms", json=realm_config)
            if response.status_code == 201:
                self.log(f"Realm {REALM_NAME} created successfully", "SUCCESS")
                return True
            elif response.status_code == 409:
                self.log(f"Realm {REALM_NAME} already exists", "WARNING")
                return True
            else:
                self.log(f"Failed to create realm: {response.status_code} - {response.text}", "ERROR")
                return False
        except requests.RequestException as e:
            self.log(f"Error creating realm: {e}", "ERROR")
            return False
            
    def create_client(self):
        """Create the flask-app client"""
        self.log(f"Creating client: {CLIENT_ID}")
        
        client_config = {
            "clientId": CLIENT_ID,
            "name": "Flask Application",
            "description": "Flask app with Keycloak integration",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "secret": CLIENT_SECRET,
            "redirectUris": [
                "http://localhost:5000/*"
            ],
            "webOrigins": [
                "http://localhost:5000"
            ],
            "protocol": "openid-connect",
            "publicClient": False,
            "bearerOnly": False,
            "consentRequired": False,
            "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "authorizationServicesEnabled": False,
            "fullScopeAllowed": True,
            "attributes": {
                "access.token.lifespan": "300"
            }
        }
        
        try:
            response = self.session.post(f"{self.base_url}/admin/realms/{REALM_NAME}/clients", json=client_config)
            if response.status_code == 201:
                self.log(f"Client {CLIENT_ID} created successfully", "SUCCESS")
                return True
            elif response.status_code == 409:
                self.log(f"Client {CLIENT_ID} already exists", "WARNING")
                return True
            else:
                self.log(f"Failed to create client: {response.status_code} - {response.text}", "ERROR")
                return False
        except requests.RequestException as e:
            self.log(f"Error creating client: {e}", "ERROR")
            return False
            
    def create_roles(self):
        """Create realm and client roles"""
        self.log("Creating roles...")
        
        # Create realm roles
        realm_roles = [
            {"name": "user", "description": "User role"},
            {"name": "admin", "description": "Admin role"}
        ]
        
        for role in realm_roles:
            try:
                response = self.session.post(f"{self.base_url}/admin/realms/{REALM_NAME}/roles", json=role)
                if response.status_code in [201, 409]:  # Created or already exists
                    self.log(f"Realm role '{role['name']}' configured", "SUCCESS")
                else:
                    self.log(f"Failed to create realm role '{role['name']}': {response.status_code}", "ERROR")
            except requests.RequestException as e:
                self.log(f"Error creating realm role '{role['name']}': {e}", "ERROR")
        
        return True
        
    def create_users(self):
        """Create test users"""
        self.log("Creating users...")
        
        users = [
            {
                "username": "admin",
                "enabled": True,
                "emailVerified": True, 
                "email": "admin@example.com",
                "firstName": "Admin",
                "lastName": "User",
                "credentials": [{"type": "password", "value": "adminpassword", "temporary": False}],
                "realmRoles": ["user", "admin"]
            },
            {
                "username": "testuser",
                "enabled": True,
                "emailVerified": True,
                "email": "testuser@example.com", 
                "firstName": "Test",
                "lastName": "User",
                "credentials": [{"type": "password", "value": "testpassword", "temporary": False}],
                "realmRoles": ["user"]
            }
        ]
        
        for user in users:
            try:
                # Create user
                user_data = {k: v for k, v in user.items() if k != 'realmRoles'}
                response = self.session.post(f"{self.base_url}/admin/realms/{REALM_NAME}/users", json=user_data)
                
                if response.status_code == 201:
                    self.log(f"User '{user['username']}' created successfully", "SUCCESS")
                    
                    # Get user ID for role assignment
                    users_response = self.session.get(f"{self.base_url}/admin/realms/{REALM_NAME}/users?username={user['username']}")
                    if users_response.status_code == 200:
                        user_list = users_response.json()
                        if user_list:
                            user_id = user_list[0]['id']
                            self.assign_roles_to_user(user_id, user['realmRoles'])
                            
                elif response.status_code == 409:
                    self.log(f"User '{user['username']}' already exists", "WARNING")
                else:
                    self.log(f"Failed to create user '{user['username']}': {response.status_code}", "ERROR")
                    
            except requests.RequestException as e:
                self.log(f"Error creating user '{user['username']}': {e}", "ERROR")
                
        return True
        
    def assign_roles_to_user(self, user_id, role_names):
        """Assign realm roles to a user"""
        try:
            # Get available realm roles
            roles_response = self.session.get(f"{self.base_url}/admin/realms/{REALM_NAME}/roles")
            if roles_response.status_code == 200:
                all_roles = roles_response.json()
                roles_to_assign = [role for role in all_roles if role['name'] in role_names]
                
                if roles_to_assign:
                    response = self.session.post(
                        f"{self.base_url}/admin/realms/{REALM_NAME}/users/{user_id}/role-mappings/realm",
                        json=roles_to_assign
                    )
                    if response.status_code == 204:
                        self.log(f"Roles {role_names} assigned to user", "SUCCESS")
                    else:
                        self.log(f"Failed to assign roles: {response.status_code}", "ERROR")
        except requests.RequestException as e:
            self.log(f"Error assigning roles: {e}", "ERROR")
            
    def configure_keycloak(self):
        """Main configuration method"""
        self.log("Starting Keycloak configuration...")
        
        if not self.wait_for_keycloak():
            return False
            
        if not self.get_admin_token():
            return False
            
        if not self.create_realm():
            return False
            
        if not self.create_client():
            return False
            
        if not self.create_roles():
            return False
            
        if not self.create_users():
            return False
            
        self.log("Keycloak configuration completed successfully!", "SUCCESS")
        return True

def main():
    print("🔧 Keycloak Configuration Script")
    print("=" * 40)
    
    configurator = KeycloakConfigurator()
    
    if configurator.configure_keycloak():
        print("\n✅ Keycloak is now configured and ready!")
        print(f"🌐 Access URLs:")
        print(f"   Keycloak Admin: {KEYCLOAK_URL} (admin/admin)")
        print(f"   Realm: {KEYCLOAK_URL}/realms/{REALM_NAME}")
        print(f"🔑 Test Users:")
        print(f"   admin/adminpassword")
        print(f"   testuser/testpassword")
        return 0
    else:
        print("\n❌ Keycloak configuration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())