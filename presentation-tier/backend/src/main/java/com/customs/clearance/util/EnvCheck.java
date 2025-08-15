package com.customs.clearance.util;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class EnvCheck {

    @Value("${MYSQLUSER:NOT_FOUND}")
    private String mysqlUser;

    @Value("${MYSQLHOST:NOT_FOUND}")
    private String mysqlHost;

    @PostConstruct
    public void logEnv() {
        System.out.println("===== ENV CHECK =====");
        System.out.println("MYSQLUSER = " + mysqlUser);
        System.out.println("MYSQLHOST = " + mysqlHost);
        System.out.println("=====================");
    }
}
