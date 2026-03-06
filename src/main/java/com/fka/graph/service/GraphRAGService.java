package com.fka.graph.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class GraphRAGService {

    private static final Logger log = LoggerFactory.getLogger(GraphRAGService.class);

    private final KnowledgeGraphService knowledgeGraphService;
    private final VectorStore vectorStore;
    private final ChatClient chatClient;

    public GraphRAGService(KnowledgeGraphService knowledgeGraphService,
                           VectorStore vectorStore,
                           ChatClient.Builder chatClientBuilder) {
        this.knowledgeGraphService = knowledgeGraphService;
        this.vectorStore = vectorStore;
        this.chatClient = chatClientBuilder
                .defaultSystem("""
                    You are a FinTech regulation expert. You will receive TWO types of context:

                    1. STRUCTURED KNOWLEDGE from a knowledge graph showing entities and their relationships
                       (providers, regulations, compliance requirements, payment methods).
                    2. DOCUMENT CONTEXT from actual EU regulation documents with relevant paragraphs.

                    Use BOTH to provide comprehensive, well-cited answers. The structured knowledge gives you
                    the relationships and facts, while the document context gives you the legal detail and exact wording.
                    If structured knowledge is empty for an entity, rely on document context alone.
                    Synthesize information from both sources — do not just list them separately.
                    """)
                .build();
    }

    public String answerWithGraphContext(String question) {
        // Step 1: Extract entities from the question using LLM
        String extractedEntities = extractEntities(question);
        log.info("Extracted entities: {}", extractedEntities);

        // Step 2: Query knowledge graph for structured context
        String graphContext = buildGraphContext(extractedEntities);
        log.info("Graph context length: {} chars", graphContext.length());

        // Step 3: Query PGVector for document context
        String documentContext = buildDocumentContext(question);
        log.info("Document context length: {} chars", documentContext.length());

        // Step 4: Build combined prompt
        String combinedPrompt = buildCombinedPrompt(question, graphContext, documentContext);

        // Step 5: Call LLM with combined context
        return chatClient.prompt()
                .user(combinedPrompt)
                .call()
                .content();
    }

    private String extractEntities(String question) {
        return chatClient.prompt()
                .user("""
                    Extract the main entity names from this question that might exist in a FinTech knowledge graph.
                    The graph contains: PaymentProviders (Riverty, Klarna, Adyen, Stripe, Deutsche Bank, N26),
                    Regulations (PSD2, PSD1, SCA-RTS, GDPR, AMLD5), ComplianceRequirements (Strong Customer Authentication,
                    Third Party Provider Access, Payment Transparency), and PaymentMethods (SEPA Credit Transfer,
                    SEPA Direct Debit, Card Payment, Buy Now Pay Later, Instant Payment).

                    Return ONLY the matching entity names from the list above, comma-separated. No explanations.
                    If no entities match, return "NONE".

                    Question: """ + question)
                .call()
                .content();
    }

    private String buildGraphContext(String extractedEntities) {
        if (extractedEntities == null || extractedEntities.trim().equalsIgnoreCase("NONE")) {
            return "";
        }

        StringBuilder context = new StringBuilder();
        String[] entities = extractedEntities.split(",");

        for (String entity : entities) {
            String name = entity.trim();
            if (name.isEmpty()) continue;

            // Try as provider
            String providerContext = knowledgeGraphService.formatProviderContext(name);
            if (!providerContext.isEmpty()) {
                context.append(providerContext);
                continue;
            }

            // Try as regulation — show providers under it and its chain
            var providers = knowledgeGraphService.getProvidersByRegulation(name);
            if (!providers.isEmpty()) {
                context.append(String.format("- Regulation: %s\n", name));
                context.append(String.format("  - Providers regulated: %s\n",
                        providers.stream().map(p -> p.getName()).collect(Collectors.joining(", "))));

                var chain = knowledgeGraphService.getRegulationChain(name);
                if (chain.size() > 1) {
                    context.append("  - Regulation history: ");
                    context.append(chain.stream()
                            .map(m -> m.get("name") + " (" + m.get("directiveNumber") + ")")
                            .collect(Collectors.joining(" -> ")));
                    context.append("\n");
                }

                // Get compliance requirements
                var reqs = knowledgeGraphService.getComplianceRequirements(providers.get(0).getName());
                if (!reqs.isEmpty()) {
                    for (var req : reqs) {
                        context.append(String.format("  - Requires: %s (%s) [%s]\n",
                                req.getName(), req.getArticle(), req.getCategory()));
                    }
                }
            }
        }

        return context.toString();
    }

    private String buildDocumentContext(String question) {
        List<Document> documents = vectorStore.similaritySearch(
                SearchRequest.builder()
                        .query(question)
                        .topK(5)
                        .similarityThreshold(0.0)
                        .build());

        if (documents == null || documents.isEmpty()) {
            return "";
        }

        return documents.stream()
                .map(doc -> {
                    String regulation = doc.getMetadata().getOrDefault("regulation", "Unknown").toString();
                    return String.format("[Source: %s]\n%s", regulation, doc.getText());
                })
                .collect(Collectors.joining("\n\n---\n\n"));
    }

    private String buildCombinedPrompt(String question, String graphContext, String documentContext) {
        StringBuilder prompt = new StringBuilder();

        if (!graphContext.isEmpty()) {
            prompt.append("STRUCTURED KNOWLEDGE (from knowledge graph):\n");
            prompt.append(graphContext);
            prompt.append("\n");
        }

        if (!documentContext.isEmpty()) {
            prompt.append("DOCUMENT CONTEXT (from regulation documents):\n");
            prompt.append(documentContext);
            prompt.append("\n");
        }

        if (graphContext.isEmpty() && documentContext.isEmpty()) {
            prompt.append("No structured or document context was found for this question.\n\n");
        }

        prompt.append("\nQuestion: ").append(question);

        return prompt.toString();
    }
}
