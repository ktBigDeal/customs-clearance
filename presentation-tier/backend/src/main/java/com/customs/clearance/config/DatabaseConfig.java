package com.customs.clearance.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Database configuration for JPA repositories and transaction management
 */
@Configuration
@EnableJpaRepositories(basePackages = "com.customs.clearance.repository")
@EnableTransactionManagement
public class DatabaseConfig {
    // Additional database configuration can be added here
}