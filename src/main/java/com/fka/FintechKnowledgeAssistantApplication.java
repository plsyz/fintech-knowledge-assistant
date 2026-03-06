package com.fka;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.ai.model.ollama.autoconfigure.OllamaChatAutoConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.neo4j.repository.config.EnableNeo4jRepositories;

@SpringBootApplication(exclude = { OllamaChatAutoConfiguration.class })
@EnableJpaRepositories(basePackages = {"com.fka.ingestion", "com.fka.retrieval"})
@EnableNeo4jRepositories(basePackages = "com.fka.graph", transactionManagerRef = "neo4jTransactionManager")
@EntityScan(basePackages = {"com.fka.ingestion", "com.fka.retrieval"})
public class FintechKnowledgeAssistantApplication {

	public static void main(String[] args) {
		SpringApplication.run(FintechKnowledgeAssistantApplication.class, args);
	}

}
