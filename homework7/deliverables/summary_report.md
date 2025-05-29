# Summary Report



---
# Cybersecurity Architect: Securing a Containerized Application


In this security assessment, we identified five critical vulnerabilities in the original Flask application: command injection in the `/ping` endpoint allowing arbitrary OS commands through unsanitized user input, code execution vulnerability in the `/calculate` endpoint using the dangerous `eval()` function, hard-coded credentials stored in source code, insufficient input validation in the root route that only checked alphanumeric characters, and insecure configuration running on all interfaces without TLS/HTTPS.

We tested the application endpoints (`/`, `/ping?ip=8.8.8.8`, and `/calculate?expr=2+3`) and conducted security scanning using `make check`, `make scan`, and `make host-security` commands. Initial scans revealed multiple vulnerabilities and misconfigurations that required immediate attention.

To remediate these issues, we created an improved version that implements proper input validation, replaces command injection-vulnerable code with safer alternatives using argument arrays instead of shell execution, eliminates the dangerous `eval()` function by replacing it with `ast.literal_eval()`, moves credentials to environment variables managed through `.env` files, adds logging and error handling, and includes better configuration management with environment-based settings and a health check endpoint. Due to macOS compatibility issues, we maintained the original interface binding configuration to prevent connectivity loss, though we attempted to restrict Flask to localhost where possible.
We then retested the secured applications against the endpoints and got the expected results. 
With results from our `make scan` and `make check` we were able to apply some of the suggested controls.

We secured the containerized application using a minimal base image (python:3.13-alpine), ensuring the app runs as a non-root user with proper `HEALTHCHECK` directives. The Dockerfile was enhanced with multi-stage builds where applicable to reduce attack surface. The docker-compose.yml was hardened with read-only filesystems, security options, memory limits, process limits, and port exposure restricted to `127.0.0.1`.

After resolving macOS-specific issues with the security script (which attempted to modify Linux-specific paths unavailable on Docker Desktop for Mac), we implemented iterative security improvements: updating Docker daemon settings, implementing read-only filesystems, binding ports to localhost only, and enabling Docker Content Trust. These measures improved the Docker Bench for Security score from 6 to 25 by configuring memory limits, CPU shares, process limits, and security options like no-new-privileges.

We then performed comprehensive threat modeling using STRIDE analysis, mapped vulnerabilities using MITRE ATT&CK for Containers to identify relevant techniques, and aligned findings with NIST 800-53 controls. The threat analysis was documented in `deliverables/threat_model.md`. An architectural diagram showing the hardened application infrastructure was generated and saved as `deliverables/architecture_diagram.png`. The auto-hardening Python script (`docker_security_fixes.py`) was developed to automatically update `daemon.json` with hardening flags and inject security configurations into Dockerfile and Compose files.