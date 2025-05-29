
## 1. Developer’s Perspective: Initial Application Setup

The initial setup represents a developer’s implementation of a Flask application, containerized with Docker and orchestrated via Docker Compose, with automation provided by a Makefile. This version, located in the `before/` directory, contains intentional vulnerabilities to be addressed later.

### 1.1 Flask Application

The initial Flask application includes endpoints with common security flaws: hardcoded secrets, command injection, and unsafe use of `eval()`.

**Initial Vulnerable Code: `before/app.py`**
```python
from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

# Hard-coded password
PASSWORD = "supersecretpassword"

@app.route('/')
def hello():
    name = request.args.get('name', 'World')
    if not name.isalnum():
        return jsonify({"error": "Invalid name"}), 400
    return f"Hello, {name}!"

# Command injection vulnerability
@app.route('/ping')
def ping():
    ip = request.args.get('ip')
    # Unsafe command execution
    result = subprocess.check_output(f"ping -c 1 {ip}", shell=True)
    return result

# Insecure use of eval
@app.route('/calculate')
def calculate():
    expression = request.args.get('expr')
    # Dangerous use of eval
    result = eval(expression)
    return str(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Dependencies: `before/requirements.txt`**
```
Flask==3.0.3
```

### 1.2 Dockerfile

The initial Dockerfile uses a lightweight base image and a non-root user but lacks additional security features.

**Initial Dockerfile: `before/Dockerfile`**
```
FROM python:3.9-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

CMD ["python", "app.py"]
```

### 1.3 Docker Compose

Docker Compose defines a multi-service environment with a Flask app and PostgreSQL database, exposing ports without restrictions.

**Initial Docker Compose: `before/docker-compose.yml`**
```yaml
services:
  web:
    build: .
    image: mywebapp
    ports:
      - "15000:5000"
    depends_on:
      - db
    networks:
      - frontend
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    networks:
      - backend
networks:
  frontend:
  backend:
```

### 1.4 Makefile

The Makefile automates security checks, builds, and runtime operations, serving as a consistent tool across both vulnerable and secured versions.

**Makefile: `before/Makefile`**
```
# Pre-build security checks
check:
	@echo "Running code analysis with Bandit..."
	docker run --rm -v $(PWD):/app python:3.9-alpine sh -c "pip install bandit && bandit -r /app"
	@echo "Running dependency check with pip-audit..."
	docker run --rm -v $(PWD):/app python:3.9-alpine sh -c "pip install pip-audit && pip-audit -r /app/requirements.txt"

# Host security check
host-security:
	@echo "Running Docker Bench for Security..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker/docker-bench-security

# Build Docker image after security checks
dbuild: check
	docker build -t mywebapp .

# Run the container
run:
	docker run -p 6000:5000 mywebapp

# Scan the built image for vulnerabilities
scan:
	docker scout recommendations mywebapp:latest

# Docker Compose commands
build:
	docker compose build

start:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker system prune -f

restart: stop start
```

---

## 2. Cybersecurity Architect’s Perspective: Securing the Application

As a cybersecurity architect, your goal is to remediate vulnerabilities, harden the container environment, and implement a secure architecture. This section details the process from analysis to implementation.

### 2.1 Environment Setup and Initial Analysis

- **Application Review**: Examine `before/app.py`, `Dockerfile`, `docker-compose.yml`, and `Makefile` for vulnerabilities.
- **Assets Identified**: Flask app, PostgreSQL database, Docker images, and host system.
- **Security Goals**: Ensure confidentiality, integrity, and availability.
- **Initial Scans**: Use `make check`, `make scan`, and `make host-security` to identify issues like hardcoded credentials, command injection, and outdated images.

### 2.2 Threat Modeling

Conduct threat modeling using STRIDE and MITRE ATT&CK for Containers to identify risks and map controls.

#### STRIDE Analysis

| Threat Category       | Example                        | Impact                  | Mitigation            |
|-----------------------|--------------------------------|-------------------------|-----------------------|
| Spoofing              | No auth on `/calculate`        | Unauthorized access     | Add authentication    |
| Tampering             | Unsafe IP input to `ping`      | Command injection       | Input validation      |
| Repudiation           | No logging                     | Untraceable actions     | Implement logging     |
| Information Disclosure| Hardcoded passwords            | Credential exposure     | Use environment vars  |
| Denial of Service     | Unrestricted `ping` or `eval`  | Resource exhaustion     | Rate limiting         |
| Elevation of Privilege| Runs as root (potential)       | System compromise       | Non-root user         |

#### MITRE ATT&CK Mapping

| Tactic                | Technique ID | Technique Name                  | Relevance                  |
|-----------------------|--------------|---------------------------------|----------------------------|
| Initial Access        | T1190        | Exploit Public-Facing App       | Command injection in `/ping` |
| Execution             | T1059        | Command and Scripting Interpreter | Unsafe `eval()`          |
| Persistence           | T1525        | Implant Container Image         | No image validation       |
| Privilege Escalation  | T1611        | Escape to Host                  | Root user risks           |
| Defense Evasion       | T1211        | Exploitation for Defense Evasion | Poor isolation           |

#### Controls Mapping

| Issue                | Control                  | Framework Reference       |
|----------------------|--------------------------|---------------------------|
| Hardcoded secrets    | Use environment variables| NIST 800-53: SC-12, SC-28 |
| Root user            | Non-root user            | NIST 800-53: AC-6, CM-6   |
| Network exposure     | Restrict with networks   | NIST 800-53: SC-7         |
| Missing health check | Add `HEALTHCHECK`        | CIS Docker Benchmark      |
| Unvalidated inputs   | Strict validation        | OWASP Top 10: A1-Injection|

