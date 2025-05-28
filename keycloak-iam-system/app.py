from flask import Flask, request, jsonify, session, redirect, render_template, url_for
import jwt
import time
import requests
import os
from functools import wraps
from urllib.parse import urlencode
import base64
import secrets

app = Flask(__name__)
app.secret_key = 'demo-secret-key-change-in-production'

# Keycloak Configuration
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://localhost:8080')
KEYCLOAK_INTERNAL_URL = os.getenv('KEYCLOAK_INTERNAL_URL', 'http://keycloak:8080')
REALM_NAME = 'flask-demo'
CLIENT_ID = 'flask-app'
CLIENT_SECRET = 'flask-app-secret-key-12345'

# Keycloak URLs - use internal URL for server-to-server, external for browser redirects
KEYCLOAK_AUTH_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/auth"
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
KEYCLOAK_USERINFO_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM_NAME}/protocol/openid-connect/userinfo"
KEYCLOAK_CERTS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"

def get_keycloak_public_key():
    """Get Keycloak public key for token validation"""
    try:
        response = requests.get(KEYCLOAK_CERTS_URL)
        if response.status_code == 200:
            keys = response.json()['keys']
            # Return first key for simplicity (in production, match by kid)
            return keys[0] if keys else None
        return None
    except Exception as e:
        print(f"Error getting Keycloak public key: {e}")
        return None

def validate_keycloak_token(token):
    """Validate Keycloak JWT token"""
    try:
        # Remove Bearer prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # For development, we'll validate against Keycloak's userinfo endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(KEYCLOAK_USERINFO_URL, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Token validation error: {e}")
        return None

def keycloak_token_required(f):
    """Decorator to require valid Keycloak token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        user_info = validate_keycloak_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user = user_info
        return f(*args, **kwargs)
    
    return decorated

def simple_token_required(f):
    """Decorator for simple JWT tokens (backwards compatibility)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def home():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/keycloak-login')
def keycloak_login():
    """Initiate Keycloak login flow"""
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': url_for('keycloak_callback', _external=True),
        'state': state
    }
    
    auth_url = f"{KEYCLOAK_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/keycloak-callback')
def keycloak_callback():
    """Handle Keycloak callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or state != session.get('oauth_state'):
        return redirect(url_for('home'))
    
    # Exchange code for token
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': url_for('keycloak_callback', _external=True)
    }
    
    try:
        response = requests.post(KEYCLOAK_TOKEN_URL, data=token_data)
        if response.status_code == 200:
            tokens = response.json()
            
            # Get user info
            headers = {'Authorization': f"Bearer {tokens['access_token']}"}
            user_response = requests.get(KEYCLOAK_USERINFO_URL, headers=headers)
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                session['user'] = {
                    'username': user_info.get('preferred_username'),
                    'email': user_info.get('email'),
                    'method': 'keycloak',
                    'access_token': tokens['access_token']
                }
                session.pop('oauth_state', None)
                return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Keycloak callback error: {e}")
    
    return redirect(url_for('home'))

# API Endpoints
@app.route('/api/public', methods=['GET'])
def api_public():
    """Public API endpoint"""
    return jsonify({
        'message': 'This is a public endpoint - no authentication required!',
        'timestamp': int(time.time()),
        'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'authenticated': False,
        'endpoint': '/api/public'
    })

@app.route('/api/protected', methods=['GET'])
@keycloak_token_required
def api_protected():
    """Protected API endpoint (Keycloak tokens)"""
    return jsonify({
        'message': 'Successfully accessed protected endpoint with Keycloak token!',
        'user': request.user,
        'authenticated': True,
        'timestamp': int(time.time()),
        'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'endpoint': '/api/protected',
        'auth_method': 'keycloak'
    })

@app.route('/api/protected-simple', methods=['GET'])
@simple_token_required
def api_protected_simple():
    """Protected API endpoint (Simple JWT tokens)"""
    return jsonify({
        'message': 'Successfully accessed protected endpoint with simple JWT!',
        'user': request.user,
        'authenticated': True,
        'timestamp': int(time.time()),
        'server_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'endpoint': '/api/protected-simple',
        'auth_method': 'simple_jwt'
    })

@app.route('/api/keycloak-login', methods=['POST'])
def api_keycloak_login():
    """Get Keycloak token via direct grant"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    # Direct grant to Keycloak
    token_data = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': data['username'],
        'password': data['password'],
        'scope': 'openid email profile'
    }
    
    try:
        response = requests.post(KEYCLOAK_TOKEN_URL, data=token_data)
        if response.status_code == 200:
            tokens = response.json()
            
            # Get user info
            headers = {'Authorization': f"Bearer {tokens['access_token']}"}
            user_response = requests.get(KEYCLOAK_USERINFO_URL, headers=headers)
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                return jsonify({
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'token_type': 'Bearer',
                    'expires_in': tokens.get('expires_in', 300),
                    'user': {
                        'username': user_info.get('preferred_username'),
                        'email': user_info.get('email'),
                        'name': f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
                    },
                    'auth_method': 'keycloak'
                })
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"Keycloak login error: {e}")
        return jsonify({'error': 'Authentication service unavailable'}), 503

@app.route('/api/login', methods=['POST'])
def api_login():
    """Simple JWT login (backwards compatibility)"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    if data['username'] == 'admin' and data['password'] == 'password':
        current_time = int(time.time())
        expiration_time = current_time + 3600
        
        payload = {
            'username': data['username'],
            'role': 'admin',
            'iat': current_time,
            'exp': expiration_time
        }
        
        token = jwt.encode(payload, app.secret_key, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {'username': data['username'], 'role': 'admin'},
            'expires_in': '1 hour',
            'auth_method': 'simple_jwt'
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/simple-login', methods=['GET', 'POST'])
def simple_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'password':
            session['user'] = {'username': 'admin', 'method': 'simple'}
            return redirect('/dashboard')
        else:
            return render_template('simple_login.html', error=True)
    
    return render_template('simple_login.html')

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect('/')
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'keycloak_url': KEYCLOAK_URL,
        'realm': REALM_NAME
    })

if __name__ == '__main__':
    print("🚀 Starting Keycloak-Integrated IAM System")
    print(f"🔐 Keycloak URL: {KEYCLOAK_URL}")
    print(f"🏛️ Realm: {REALM_NAME}")
    print("🌐 Flask App: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)