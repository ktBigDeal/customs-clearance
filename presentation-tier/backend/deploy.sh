#!/bin/bash
cd presentation-tier/backend
chmod +x mvnw
./mvnw clean package -DskipTests
java -Dserver.port=$PORT -jar target/*.jar
