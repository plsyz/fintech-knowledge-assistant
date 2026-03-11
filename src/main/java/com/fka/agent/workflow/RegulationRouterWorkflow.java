package com.fka.agent.workflow;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class RegulationRouterWorkflow {

    private static final Logger log = LoggerFactory.getLogger(RegulationRouterWorkflow.class);

    private final ChatClient chatClient;

    private static final String CLASSIFICATION_PROMPT = """
            Classify this query into exactly ONE of these categories:
            SCA_AUTHENTICATION, TPP_ACCESS, CONSUMER_RIGHTS, LICENSING, AML_KYC, GENERAL

            Rules:
            - SCA_AUTHENTICATION: questions about strong customer authentication, two-factor, payment authentication, contactless limits, SCA exemptions
            - TPP_ACCESS: questions about third party providers, open banking, APIs, XS2A, AISP, PISP, account access
            - CONSUMER_RIGHTS: questions about refunds, chargebacks, liability, disputes, unauthorized transactions, consumer protection
            - LICENSING: questions about payment institution licenses, authorization, own funds, passporting, regulatory approval
            - AML_KYC: questions about anti-money laundering, KYC, customer due diligence, suspicious transactions, beneficial ownership
            - GENERAL: anything that doesn't clearly fit the above categories

            Query: {query}

            Respond with ONLY the category name, nothing else.""";

    private static final Map<String, String> EXPERT_PROMPTS = Map.of(
        "SCA_AUTHENTICATION", """
            You are an SCA (Strong Customer Authentication) expert specializing in PSD2 Article 97 \
            and the Regulatory Technical Standards (RTS) under Delegated Regulation (EU) 2018/389. \
            Focus on authentication requirements, exemptions (low-value under 30 EUR, recurring \
            transactions, trusted beneficiaries, merchant-initiated transactions), contactless limits, \
            and implementation timelines. Always cite specific articles when possible. \
            Explain both the requirements and the practical implications for payment providers.""",

        "TPP_ACCESS", """
            You are an Open Banking and Third Party Provider (TPP) access expert. Focus on PSD2 \
            Articles 66-67, XS2A (Access to Account) interfaces, dedicated vs fallback access \
            mechanisms, AISP (Account Information Service Provider) and PISP (Payment Initiation \
            Service Provider) rights and obligations, API performance requirements, and the \
            regulatory framework for open banking. Cite specific articles and explain practical \
            implementation requirements.""",

        "CONSUMER_RIGHTS", """
            You are a consumer protection expert in EU payment services. Focus on PSD2 Title III \
            (transparency of conditions) and Title IV (rights and obligations for payment services), \
            unauthorized transaction liability (Article 73-74), refund rights for direct debits \
            (Article 76), execution time limits, value dating, and complaint procedures. Cite \
            specific articles and explain consumer rights clearly.""",

        "LICENSING", """
            You are a payment institution licensing expert. Focus on PSD2 Title II (payment service \
            providers), authorization requirements (Articles 5-10), own funds requirements \
            (Article 7-9), passporting procedures for cross-border services, registration vs \
            authorization thresholds, and the European Banking Authority (EBA) role. Cite specific \
            articles and explain the licensing process.""",

        "AML_KYC", """
            You are an Anti-Money Laundering and KYC expert. Focus on the 5th Anti-Money Laundering \
            Directive (AMLD5/Directive 2018/843), risk-based approach to customer due diligence, \
            enhanced due diligence for high-risk situations, beneficial ownership requirements, \
            suspicious transaction reporting (STR), politically exposed persons (PEP) screening, \
            and record-keeping obligations. Cite specific articles and explain practical compliance steps.""",

        "GENERAL", """
            You are a FinTech regulation expert with broad knowledge of EU payment regulations \
            including PSD2, GDPR, AMLD5, SEPA Regulation, E-Money Directive, and the Consumer \
            Credit Directive. Provide comprehensive answers drawing on your knowledge of the full \
            regulatory landscape. Cite specific regulations and articles where relevant."""
    );

    public RegulationRouterWorkflow(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    public String route(String userQuery) {
        // Step 1: Classify the question
        String category = classify(userQuery);
        log.info("Query classified as: {} for question: {}", category, userQuery);

        // Step 2: Get the expert prompt for that category (fallback to GENERAL)
        String expertPrompt = EXPERT_PROMPTS.getOrDefault(category, EXPERT_PROMPTS.get("GENERAL"));

        // Step 3: Call LLM with expert system prompt + user question
        String answer = chatClient.prompt()
                .system(expertPrompt)
                .user(userQuery)
                .call()
                .content();

        log.info("Routed answer length: {} chars", answer.length());
        return answer;
    }

    private String classify(String userQuery) {
        String prompt = CLASSIFICATION_PROMPT.replace("{query}", userQuery);

        String classification = chatClient.prompt()
                .user(prompt)
                .call()
                .content();

        // Clean up LLM response — trim whitespace, extract category name
        String cleaned = classification.trim().toUpperCase().replaceAll("[^A-Z_]", "");

        // Validate it's one of our known categories
        if (EXPERT_PROMPTS.containsKey(cleaned)) {
            return cleaned;
        }

        // Try partial match (e.g., LLM returned "SCA_AUTHENTICATION." with punctuation)
        for (String key : EXPERT_PROMPTS.keySet()) {
            if (cleaned.contains(key)) {
                return key;
            }
        }

        log.warn("Could not classify query, defaulting to GENERAL. LLM returned: '{}'", classification);
        return "GENERAL";
    }
}
