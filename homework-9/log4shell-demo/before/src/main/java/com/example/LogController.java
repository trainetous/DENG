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
