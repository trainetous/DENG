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
