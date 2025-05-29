from flask import Flask, request, jsonify
import os
import subprocess
import ast
import ipaddress
import re
import logging
from functools import wraps
from markupsafe import escape

app = Flask(__name__)


# Set up proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom escape function (no dependency required)
def escape(s):
    """Simple HTML escaping function"""
    return (str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;"))

# Retrieve password from environment variable instead of hardcoding
# PASSWORD = os.environ.get('PASSWORD', 'default_password')
# Strict env var (no default)
PASSWORD = os.environ.get('PASSWORD')

""" @app.route('/')
def hello():
    name = request.args.get('name', 'World')
    if not name.isalnum():
        return jsonify({"error": "Invalid name"}), 400
    return f"Hello, {name}!"
 """
# Improved input validation 
@app.route('/')
def hello():
    name = request.args.get('name', 'World')
    # Better input validation
    if not re.match(r'^[a-zA-Z0-9]{1,30}$', name):
        logger.warning(f"Invalid input attempt: {name}")
        return jsonify({"error": "Invalid name"}), 400
    # Use escape to prevent XSS
    return f"Hello, {escape(name)}!"


# Secure ping route with input validation and no shell=True
# Add timeout
@app.route('/ping')
def ping():
    ip = request.args.get('ip')
    try:
        ipaddress.ip_address(ip)  # Validate IP address
        result = subprocess.check_output(["ping", "-c", "1", ip], timeout=5)
        return result
    except ValueError:
        return jsonify({"error": "Invalid IP address"}), 400 


# Secure calculate route using ast.literal_eval instead of eval
@app.route('/calculate')
def calculate():
    expression = request.args.get('expr')
    try:
        result = ast.literal_eval(expression)
        return str(result)
    except (SyntaxError, ValueError):
        return jsonify({"error": "Invalid expression"}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)  # Bind to localhost instead of all interfaces

