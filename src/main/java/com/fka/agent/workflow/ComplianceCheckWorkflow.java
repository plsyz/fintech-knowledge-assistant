package com.fka.agent.workflow;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ComplianceCheckWorkflow {

    private static final Logger log = LoggerFactory.getLogger(ComplianceCheckWorkflow.class);

    private final ChatClient chatClient;

    // 4-step chain prompts — each has {input} placeholder replaced at runtime
    private static final List<String> CHAIN_PROMPTS = List.of(
        // Step 1: CLASSIFY — extract structured info from the transaction description
        """
        Analyze this financial transaction and extract the following in a structured format:
        - Payment type (CARD, SEPA_CT, SEPA_DD, BNPL, INSTANT, or OTHER)
        - Amount and currency
        - Whether it is cross-border (and which countries)
        - Parties involved (consumer, merchant, intermediary)
        - Transaction purpose (purchase, transfer, subscription, etc.)

        Transaction: {input}

        Respond in a clear structured format with labeled fields.""",

        // Step 2: FIND REGULATIONS — identify applicable EU regulations
        """
        Based on this transaction classification:

        {input}

        List ALL EU regulations that apply to this transaction. For each regulation, explain WHY it applies:
        - PSD2 (Payment Services Directive 2) — if payment services are involved
        - GDPR (General Data Protection Regulation) — if personal data is processed
        - AMLD5 (5th Anti-Money Laundering Directive) — if AML/KYC obligations apply
        - SEPA Regulation — if EUR payment in SEPA zone
        - Consumer Credit Directive — if credit/BNPL is involved
        - E-Money Directive — if e-money is involved

        For each applicable regulation, state the key articles that are relevant.""",

        // Step 3: CHECK REQUIREMENTS — list specific compliance obligations
        """
        For each applicable regulation identified below, list the SPECIFIC compliance requirements \
        that must be met for this transaction:

        {input}

        For each requirement include:
        - The specific article or section number
        - What must be done (e.g., SCA required, data consent needed)
        - Any exemptions that may apply
        - Deadlines or time limits

        Be precise and cite specific articles where possible.""",

        // Step 4: GENERATE REPORT — compile final structured report
        """
        Create a concise compliance report from the following analysis:

        {input}

        Format the report with these sections:
        1. EXECUTIVE SUMMARY — 2-3 sentence overview of compliance status
        2. TRANSACTION CLASSIFICATION — key facts about the transaction
        3. APPLICABLE REGULATIONS — list with brief relevance explanation
        4. KEY REQUIREMENTS — the most important compliance obligations
        5. RISK AREAS — potential compliance risks or areas needing attention
        6. RECOMMENDED ACTIONS — specific steps to ensure compliance

        Keep it professional and actionable."""
    );

    private static final List<String> STEP_NAMES = List.of(
        "CLASSIFY", "FIND REGULATIONS", "CHECK REQUIREMENTS", "GENERATE REPORT"
    );

    public ComplianceCheckWorkflow(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder
                .defaultSystem("You are a FinTech compliance expert specializing in EU payment regulations.")
                .build();
    }

    public String runComplianceCheck(String transactionDescription) {
        log.info("Starting compliance check chain for: {}", transactionDescription);

        String response = transactionDescription;

        for (int i = 0; i < CHAIN_PROMPTS.size(); i++) {
            String stepName = STEP_NAMES.get(i);
            log.info("Chain Step {}/4: {}", i + 1, stepName);

            String prompt = CHAIN_PROMPTS.get(i).replace("{input}", response);

            response = chatClient.prompt()
                    .user(prompt)
                    .call()
                    .content();

            log.info("Step {} complete — output length: {} chars", stepName, response.length());
        }

        log.info("Compliance check chain complete");
        return response;
    }
}
