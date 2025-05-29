import os
import json
import yaml
import platform

# Paths to files (adjust as necessary)
DOCKERFILE_PATH = 'Dockerfile'
DOCKER_COMPOSE_PATH = 'docker-compose.yml'

def update_daemon_json():
    """Update Docker daemon configuration for macOS."""
    print("Skipping daemon.json update on macOS.")
    print("For Docker Desktop on Mac, configure daemon settings through:")
    print("1. Open Docker Desktop")
    print("2. Go to Settings (gear icon)")
    print("3. Navigate to Docker Engine")
    print("4. Add the following JSON configuration:")
    
    recommended_settings = {
        "icc": False,
        "no-new-privileges": True,
        "userland-proxy": False,
        "live-restore": True
    }
    
    print(json.dumps(recommended_settings, indent=2))
    print("\n5. Click 'Apply & Restart'")

def update_dockerfile():
    """Modify Dockerfile to add non-root user and health check."""
    if not os.path.exists(DOCKERFILE_PATH):
        print(f"Warning: {DOCKERFILE_PATH} not found. Skipping.")
        return
        
    print(f"Checking {DOCKERFILE_PATH}...")
    
    with open(DOCKERFILE_PATH, 'r') as f:
        content = f.read()
        lines = content.splitlines()
    
    # Check what's already in the Dockerfile
    has_adduser = any('adduser' in line for line in lines)
    has_user = any('USER' in line for line in lines)
    has_healthcheck = any('HEALTHCHECK' in line for line in lines)
    
    if has_adduser and has_user and has_healthcheck:
        print("✓ Dockerfile already contains non-root user and health check")
        return
    
    # If modifications are needed
    modified_lines = []
    for i, line in enumerate(lines):
        modified_lines.append(line)
        
        # Add non-root user after FROM line
        if line.startswith('FROM') and not has_adduser:
            modified_lines.append('RUN adduser -D appuser')
            has_adduser = True
        
        # Add health check before USER line or CMD
        if (line.startswith('USER') or line.startswith('CMD')) and not has_healthcheck:
            modified_lines.append('HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:5000/ || exit 1')
            has_healthcheck = True
        
        # Ensure USER line exists before CMD
        if line.startswith('CMD') and not has_user:
            modified_lines.insert(-1, 'USER appuser')
            has_user = True
    
    # Write back the modified Dockerfile
    with open(DOCKERFILE_PATH, 'w') as f:
        f.write('\n'.join(modified_lines) + '\n')
    
    print(f"✓ Updated {DOCKERFILE_PATH}")

def update_docker_compose():
    """Update docker-compose.yml with security settings for containers."""
    if not os.path.exists(DOCKER_COMPOSE_PATH):
        print(f"Warning: {DOCKER_COMPOSE_PATH} not found. Skipping.")
        return
        
    print(f"Updating {DOCKER_COMPOSE_PATH}...")
    
    with open(DOCKER_COMPOSE_PATH, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    # Update each service with security settings
    for service_name, service in compose_data.get('services', {}).items():
        print(f"  Updating service: {service_name}")
        
        # Add memory and CPU limits
        service['mem_limit'] = '512m'
        service['cpu_shares'] = 512
        
        # Add security options
        service['security_opt'] = service.get('security_opt', [])
        if 'no-new-privileges:true' not in service['security_opt']:
            service['security_opt'].append('no-new-privileges:true')
        
        # Set PID limit
        service['pids_limit'] = 100
        
        # Set restart policy
        service['restart'] = 'on-failure:5'
        
        # Update port bindings to use localhost instead of 0.0.0.0
        if 'ports' in service:
            for i, port in enumerate(service['ports']):
                if isinstance(port, str) and ':' in port:
                    if port.startswith('0.0.0.0:') or not port.split(':')[0]:
                        host_port = port.split(':')[1]
                        service['ports'][i] = f"127.0.0.1:{host_port}:5000"
                        print(f"    ✓ Updated port binding to localhost")
        
        # Add health check for database service
        if service_name == 'db' and service.get('image', '').startswith('postgres'):
            service['healthcheck'] = {
                'test': ['CMD-SHELL', 'pg_isready -U postgres'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 5
            }
            print(f"    ✓ Added health check for database")
    
    # Write back the modified docker-compose.yml
    with open(DOCKER_COMPOSE_PATH, 'w') as f:
        yaml.dump(compose_data, f, default_flow_style=False)
    
    print(f"✓ Updated {DOCKER_COMPOSE_PATH}")

def main():
    print("Applying Docker security fixes for macOS...")
    print("=" * 50)
    
    update_daemon_json()
    print("-" * 50)
    
    update_dockerfile()
    print("-" * 50)
    
    update_docker_compose()
    print("-" * 50)
    
    print("\nSummary:")
    print("1. Review and apply Docker daemon settings through Docker Desktop GUI")
    print("2. Container security settings have been updated in docker-compose.yml")
    print("3. Dockerfile security enhancements have been applied")
    print("\nNext steps:")
    print("1. Export DOCKER_CONTENT_TRUST=1 in your shell profile")
    print("2. Run 'make stop && make build && make start' to apply changes")
    print("3. Run 'make host-security' to verify improvements")

if __name__ == "__main__":
    main()
