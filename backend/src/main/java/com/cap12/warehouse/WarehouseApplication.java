package com.cap12.warehouse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@SpringBootApplication
public class WarehouseApplication {

    private static final Logger logger = LoggerFactory.getLogger(WarehouseApplication.class);

    static {
        loadDotEnv();
    }

    public static void main(String[] args) {
        SpringApplication.run(WarehouseApplication.class, args);
    }

    /**
     * Securely searches for and loads configuration from .env into JVM System Properties
     * so that Spring Boot can resolve placeholders (${SNOWFLAKE_ACCOUNT}, ${SNOWFLAKE_USER}, etc.)
     * without needing credentials hardcoded in application.properties.
     */
    public static void loadDotEnv() {
        Path[] searchPaths = new Path[]{
            Paths.get(".env"),
            Paths.get("../.env"),
            Paths.get("../../.env")
        };

        for (Path path : searchPaths) {
            if (Files.isRegularFile(path)) {
                logger.info("Loading environment variables from: {}", path.toAbsolutePath().normalize());
                try (BufferedReader reader = Files.newBufferedReader(path)) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        line = line.trim();
                        if (line.isEmpty() || line.startsWith("#") || !line.contains("=")) {
                            continue;
                        }
                        int eqIdx = line.indexOf('=');
                        String key = line.substring(0, eqIdx).trim();
                        String val = line.substring(eqIdx + 1).trim();
                        if ((val.startsWith("\"") && val.endsWith("\"")) || (val.startsWith("'") && val.endsWith("'"))) {
                            val = val.substring(1, val.length() - 1).trim();
                        }
                        if (System.getProperty(key) == null && System.getenv(key) == null) {
                            System.setProperty(key, val);
                        }
                    }
                } catch (IOException e) {
                    logger.warn("Could not read .env file at {}: {}", path, e.getMessage());
                }
                break;
            }
        }
    }
}

