package com.fka.agent.config;

import com.fka.agent.tools.PaymentToolsService;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class McpServerConfig {

    @Bean
    public ToolCallbackProvider paymentToolCallbackProvider(PaymentToolsService paymentToolsService) {
        return MethodToolCallbackProvider.builder()
                .toolObjects(paymentToolsService)
                .build();
    }
}
