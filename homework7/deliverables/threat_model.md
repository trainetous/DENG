# Threat Model: Secure Containerized Microservices

## 1. Overview

This document outlines the threat modeling exercise performed on the initial insecure application, utilizing both the STRIDE and MITRE ATT&CK methodologies to systematically identify, categorize, and assess potential security threats.

 
---

### 2.  STRIDE Analysis

| Threat Category | Example | Threat | Mitigation | Risk | Impact|
|----------------|---------|--------|------------|-------|-------|
| Spoofing        | Lack of auth on `/calculate` | Unauthorized access,Weak password policy | Add auth/token check | High | High|
| Tampering       | Unsafe IP input to `ping` | Command injection, malicious code during build/deploy | Input validation | Critical | Critical|
| Repudiation     | No logging | Difficult to audit usage | Implement access logs | High | Medium|
| Information Disclosure | Hardcoded passwords | Credential leak | Use env variables | Critical | Critical!
| Denial of Service | Unrestricted `ping` or `eval` | Resource exhaustion | Rate limiting | High | High|
| Elevation of Privilege | Runs as root , Shell Access| Full system compromise | Use non-root user | Critical | Critical|

---

### 3. MITRE ATT&CK Mapping (Containers)

| Tactic         | Technique ID | Technique Name | Application Relevance |   Risk  | Impact | Mitigation |
|----------------|--------------|----------------|------------------------|---------|--------|-----------|
| Initial Access | T1190         | Exploit Public-Facing Application | Command injection in `/ping` | High | High | Input validation,Rate limiting,API gateway|Patch|
| Execution      | T1059         | Command and Scripting Interpreter | Use of `eval()` | High | High | Input sanitization |
| Persistence    | T1525         | Implant Container Image | No image signing or validation | Critical | Critical| Image signing and validation: Docker Scout,Trivy|
| Privilege Escalation | T1611  | Escape to Host | Root container user | High | High| Container security policies, segmentation|
| Defense Evasion | T1211        | Exploitation for Defense Evasion | Lack of file system isolation | Medium| Medium | Patching,Application hardening,Least Privilege,segmentation| 
| Credential Access | T1552 | Credentials in Files | Unauthorized access, Credential in code| High | High| Secure secret management (KMS) |
| Collection  | T1005 | Data from Local System | Access to local files| High | High | Data protection, Segmentation, Least Privilege|

---

### 4. Controls Mapping (NIST 800-53)

| Issue | Recommended Control | Framework Reference |
|-------|---------------------|---------------------|
| Hardcoded secrets | Environment secrets | NIST 800-53: SC-12, SC-28 |
| Root container user | Add `USER appuser` | NIST 800-53: AC-6, CM-6 |
| No network restrictions | Isolate with Docker networks | NIST 800-53: SC-7 |
| Missing health check | Add `HEALTHCHECK` | CIS Docker Benchmark |
| Unvalidated inputs | Strict input validation | OWASP Top 10: A1-Injection |
| Logging Monitoring| Automated log analysis | AU-6,SI-4|

---

### 5. Risk Rating Summary

| Threat | Risk | Likelihood | Impact | Mitigation Priority |
|--------|------|------------|--------|----------------------|
| Command Injection | High | High | Critical | Immediate |
| Credential Exposure | Medium | High | Medium | High |
| Eval-based execution | High | Medium | High | Immediate |
| Root user in container | High | Medium | Critical | Immediate |
| No input validation | Critical | Medium | High | Immediate|
| No logging | High | Medium | Medium | High|

## 6. Conclusion

This threat model identifies the major flaws in the system and informs the remediation and architecture redesign. Not all the vulnerabilities were eliminated,but the final implementation significantly reduces the attack surface , eliminates root access and enforces least privilege, defense in depth, secure defaults , and logging and monitoring
By applying STRIDE, we analyze the application for Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege risks. The MITRE ATT&CK framework is used to map real-world adversarial techniques relevant to containerized environments, providing a comprehensive view of possible attack vectors. This approach enables us to prioritize risks, recommend effective mitigations, and guide the secure redesign of the application architecture.

