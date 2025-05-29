from flask import Flask, request, jsonify
import os
import subprocess
import ast
import ipaddress

app = Flask(__name__)

# Retrieve password from environment variable instead of hardcoding
PASSWORD = os.environ.get('PASSWORD', 'default_password')

@app.route('/')
def hello():
    name = request.args.get('name', 'World')
    if not name.isalnum():
        return jsonify({"error": "Invalid name"}), 400
    return f"Hello, {name}!"

# Secure ping route with input validation and no shell=True
@app.route('/ping')
def ping():
    ip = request.args.get('ip')
    try:
        ipaddress.ip_address(ip)  # Validate IP address
        result = subprocess.check_output(["ping", "-c", "1", ip])
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

