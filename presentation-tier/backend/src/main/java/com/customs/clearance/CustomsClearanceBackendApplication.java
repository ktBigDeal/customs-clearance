package com.customs.clearance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Main application class for Customs Clearance Backend API Gateway
 * 
 * This application serves as the presentation tier API gateway in a 3-tier architecture
 * for customs clearance operations.
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 */
@SpringBootApplication
@EnableJpaAuditing
@EnableTransactionManagement
public class CustomsClearanceBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(CustomsClearanceBackendApplication.class, args);
    }
}