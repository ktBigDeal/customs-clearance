package com.customs.clearance.util;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import io.swagger.v3.oas.models.OpenAPI;
import jakarta.annotation.PostConstruct;

@Component
public class SwaggerBeanLogger {

    @Autowired(required = false)
    private OpenAPI openAPI;

    @PostConstruct
    public void log() {
        if(openAPI != null) {
            System.out.println("Swagger OpenAPI Bean is initialized!");
        } else {
            System.out.println("Swagger OpenAPI Bean is NOT initialized!");
        }
    }
}

