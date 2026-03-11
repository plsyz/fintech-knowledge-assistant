package com.fka.agent.tools;

import com.fka.graph.model.ComplianceRequirement;
import com.fka.graph.model.PaymentProvider;
import com.fka.graph.service.KnowledgeGraphService;
import com.fka.retrieval.RagRetrievalService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class PaymentToolsService {

    private static final Logger log = LoggerFactory.getLogger(PaymentToolsService.class);

    private final KnowledgeGraphService knowledgeGraphService;
    private final RagRetrievalService ragService;

    public PaymentToolsService(KnowledgeGraphService knowledgeGraphService,
                               @Lazy RagRetrievalService ragService) {
        this.knowledgeGraphService = knowledgeGraphService;
        this.ragService = ragService;
    }

    // Tool 1: Graph tool — compliance requirements for a provider
    @Tool(description = "Look up compliance requirements for a specific payment provider such as Riverty, Klarna, Adyen, Stripe, Deutsche Bank, or N26")
    public String getComplianceRequirements(
            @ToolParam(description = "Name of the payment provider, e.g. Riverty, Klarna") String providerName) {
        log.info("Tool called: getComplianceRequirements({})", providerName);
        try {
            List<ComplianceRequirement> requirements = knowledgeGraphService.getComplianceRequirements(providerName);
            if (requirements.isEmpty()) {
                return "No compliance requirements found for provider: " + providerName;
            }
            StringBuilder sb = new StringBuilder();
            sb.append("Compliance requirements for ").append(providerName).append(":\n");
            for (ComplianceRequirement req : requirements) {
                sb.append(String.format("- %s (Article: %s, Category: %s): %s\n",
                        req.getName(), req.getArticle(), req.getCategory(), req.getDescription()));
            }
            return sb.toString();
        } catch (Exception e) {
            log.error("Error in getComplianceRequirements: {}", e.getMessage());
            return "Error looking up compliance requirements: " + e.getMessage();
        }
    }

    // Tool 2: Deterministic + RAG tool — SCA check mixing business rules with regulation details
    @Tool(description = "Check if a specific payment type and amount requires Strong Customer Authentication (SCA) under PSD2. Applies exemption logic and enriches with regulation details.")
    public String checkScaRequirement(
            @ToolParam(description = "Payment type: CARD, SEPA_CT, SEPA_DD, or BNPL") String paymentType,
            @ToolParam(description = "Transaction amount in EUR") double amount) {
        log.info("Tool called: checkScaRequirement({}, {})", paymentType, amount);
        try {
            // Deterministic business rules first
            StringBuilder result = new StringBuilder();
            result.append(String.format("SCA Analysis for %s payment of %.2f EUR:\n", paymentType, amount));

            boolean scaRequired = true;
            String exemptionReason = null;

            if ("CARD".equalsIgnoreCase(paymentType) && amount < 30) {
                scaRequired = false;
                exemptionReason = "Low-value exemption: contactless payments under 30 EUR may be exempt, " +
                        "but note the cumulative limit of 100 EUR or 5 consecutive transactions without SCA.";
            } else if ("SEPA_CT".equalsIgnoreCase(paymentType)) {
                result.append("- SEPA Credit Transfers initiated by the payer typically require SCA.\n");
            } else if ("SEPA_DD".equalsIgnoreCase(paymentType)) {
                scaRequired = false;
                exemptionReason = "SEPA Direct Debits are generally exempt from SCA as they are " +
                        "payee-initiated (merchant-initiated) transactions covered by the mandate.";
            } else if ("BNPL".equalsIgnoreCase(paymentType)) {
                result.append("- BNPL transactions may require SCA depending on implementation.\n");
            }

            if (!scaRequired && exemptionReason != null) {
                result.append("- SCA may NOT be required. Reason: ").append(exemptionReason).append("\n");
            } else {
                result.append("- SCA IS required for this transaction.\n");
            }

            // Enrich with RAG for detailed PSD2 context
            String ragContext = ragService.askQuestionWithFilter(
                    String.format("What are the SCA requirements for %s payments of %.2f EUR under PSD2?",
                            paymentType, amount),
                    "PSD2");
            result.append("\nDetailed PSD2 context:\n").append(ragContext);

            return result.toString();
        } catch (Exception e) {
            log.error("Error in checkScaRequirement: {}", e.getMessage());
            return "Error checking SCA requirement: " + e.getMessage();
        }
    }

    // Tool 3: Pure RAG tool — find regulations for a scenario
    @Tool(description = "Find which EU payment regulations apply to a specific transaction scenario. Searches regulation documents for applicable rules.")
    public String findApplicableRegulations(
            @ToolParam(description = "Transaction scenario description, e.g. 'cross-border BNPL payment of 500 EUR from Germany to France'") String scenario) {
        log.info("Tool called: findApplicableRegulations({})", scenario);
        try {
            return ragService.askQuestion(
                    "Which EU payment regulations apply to this scenario: " + scenario +
                    ". List each applicable regulation, why it applies, and key requirements.");
        } catch (Exception e) {
            log.error("Error in findApplicableRegulations: {}", e.getMessage());
            return "Error finding applicable regulations: " + e.getMessage();
        }
    }

    // Tool 4: Pure graph tool — provider relationship map
    @Tool(description = "Get the full relationship map of a payment provider from the knowledge graph, including regulations, compliance requirements, and supported payment methods")
    public String getProviderGraph(
            @ToolParam(description = "Name of the payment provider, e.g. Riverty, Klarna") String providerName) {
        log.info("Tool called: getProviderGraph({})", providerName);
        try {
            Optional<PaymentProvider> providerOpt = knowledgeGraphService.getProviderByName(providerName);
            if (providerOpt.isEmpty()) {
                return "Provider not found in knowledge graph: " + providerName;
            }
            String context = knowledgeGraphService.formatProviderContext(providerName);
            if (context.isEmpty()) {
                return "No relationship data found for provider: " + providerName;
            }
            return "Knowledge Graph for " + providerName + ":\n" + context;
        } catch (Exception e) {
            log.error("Error in getProviderGraph: {}", e.getMessage());
            return "Error querying provider graph: " + e.getMessage();
        }
    }

    // Tool 5: Filtered RAG tool — processing timeline
    @Tool(description = "Calculate payment processing timeline based on PSD2 regulation requirements for execution time limits")
    public String getProcessingTimeline(
            @ToolParam(description = "Payment type: CARD, SEPA_CT, SEPA_DD, BNPL, or INSTANT") String paymentType,
            @ToolParam(description = "Whether the payment is cross-border (true/false)") boolean crossBorder) {
        log.info("Tool called: getProcessingTimeline({}, crossBorder={})", paymentType, crossBorder);
        try {
            String context = crossBorder ? "cross-border" : "domestic";
            String question = String.format(
                    "What are the PSD2 execution time requirements and processing timeline for %s %s payments? " +
                    "Include maximum execution times, value dating rules, and any relevant deadlines.",
                    context, paymentType);
            return ragService.askQuestionWithFilter(question, "PSD2");
        } catch (Exception e) {
            log.error("Error in getProcessingTimeline: {}", e.getMessage());
            return "Error getting processing timeline: " + e.getMessage();
        }
    }
}
