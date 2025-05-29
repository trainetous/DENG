import os
import json
import yaml
import subprocess

# Paths to files (adjust as necessary)
DAEMON_JSON_PATH = '/etc/docker/daemon.json'
DOCKERFILE_PATH = 'Dockerfile'
DOCKER_COMPOSE_PATH = 'docker-compose.yml'

def update_daemon_json():
    """Update or create daemon.json with security settings."""
    settings = {
        "icc": False,
        "userns-remap": "default",
        "live-restore": True,
        "userland-proxy": False
    }
    if os.path.exists(DAEMON_JSON_PATH):
        with open(DAEMON_JSON_PATH, 'r') as f:
            current_settings = json.load(f)
        current_settings.update(settings)
    else:
        current_settings = settings
    with open(DAEMON_JSON_PATH, 'w') as f:
        json.dump(current_settings, f, indent=4)
    print(f"Updated {DAEMON_JSON_PATH} with security settings.")

def update_dockerfile():
    """Modify Dockerfile to add non-root user and health check."""
    with open(DOCKERFILE_PATH, 'r') as f:
        lines = f.readlines()
    # Insert non-root user and health check if not present
    if not any('RUN adduser -D appuser' in line for line in lines):
        lines.insert(1, 'RUN adduser -D appuser\n')
    if not any('HEALTHCHECK' in line for line in lines):
        lines.insert(-1, 'HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:5000/ || exit 1\n')
    if not any('USER appuser' in line for line in lines):
        lines.insert(-1, 'USER appuser\n')
    with open(DOCKERFILE_PATH, 'w') as f:
        f.writelines(lines)
    print(f"Updated {DOCKERFILE_PATH} with non-root user and health check.")

def update_docker_compose():
    """Update docker-compose.yml with security settings for containers."""
    with open(DOCKER_COMPOSE_PATH, 'r') as f:
        compose_data = yaml.safe_load(f)
    for service in compose_data.get('services', {}).values():
        service['mem_limit'] = '512m'
        service['read_only'] = True
        service['security_opt'] = ['no-new-privileges:true']
        service['pids_limit'] = 100
        if 'ports' in service:
            for i, port in enumerate(service['ports']):
                if port.startswith('0.0.0.0'):
                    service['ports'][i] = port.replace('0.0.0.0', '127.0.0.1')
    with open(DOCKER_COMPOSE_PATH, 'w') as f:
        yaml.dump(compose_data, f)
    print(f"Updated {DOCKER_COMPOSE_PATH} with security settings.")

def main():
    print("Applying Docker security fixes...")
    update_daemon_json()
    update_dockerfile()
    update_docker_compose()
    print("Security fixes applied. Please review the changes and restart Docker services as necessary.")

if __name__ == "__main__":
    main()
