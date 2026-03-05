package com.fka;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.ai.model.ollama.autoconfigure.OllamaChatAutoConfiguration;

@SpringBootApplication(exclude = { OllamaChatAutoConfiguration.class })
public class FintechKnowledgeAssistantApplication {

	public static void main(String[] args) {
		SpringApplication.run(FintechKnowledgeAssistantApplication.class, args);
	}

}
