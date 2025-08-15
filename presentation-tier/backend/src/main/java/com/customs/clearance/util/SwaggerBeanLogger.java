package com.customs.clearance.util;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import io.swagger.v3.oas.models.OpenAPI;
import jakarta.annotation.PostConstruct;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class SwaggerBeanLogger {

    private static final Logger log = LoggerFactory.getLogger(SwaggerBeanLogger.class);

    @Autowired(required = false)
    private OpenAPI openAPI;

    @PostConstruct
    public void log() {
        if(openAPI != null) {
            log.info("Swagger OpenAPI Bean is initialized!");
        } else {
            log.warn("Swagger OpenAPI Bean is NOT initialized!");
        }
    }
}


