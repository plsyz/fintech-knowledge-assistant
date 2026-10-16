package com.fka.retrieval;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

@Service
public class RagRetrievalService {

    private final ChatClient chatClient;
    private final ChatClient noRetrievalChatClient;
    private final VectorStore vectorStore;

    // Build ChatClient with system prompt + QuestionAnswerAdvisor that handles
    // embedding the question, searching PGVector for top-5 chunks, and augmenting the prompt
    public RagRetrievalService(ChatClient.Builder chatClientBuilder, VectorStore vectorStore,
                               @Value("classpath:prompts/system-prompt.st") Resource systemPromptResource) {
        this.vectorStore = vectorStore;
        this.chatClient = chatClientBuilder
                .defaultSystem(systemPromptResource)
                .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore)
                        .searchRequest(SearchRequest.builder()
                                .topK(15)             // Return 15 most similar chunks
                                .similarityThreshold(0.0) // No threshold — return top-K regardless, let LLM judge relevance
                                .build())
                        .build())
                .build();
        // Same model and system prompt, no retrieval. Used as the closed-book baseline:
        // if the model answers a corpus question correctly without any context, the
        // question does not measure retrieval (benchmark contamination check).
        this.noRetrievalChatClient = chatClientBuilder
                .defaultSystem(systemPromptResource)
                .build();
    }

    /** Vector RAG answer plus the chunks that were actually retrieved for it. */
    public AnswerWithSources askQuestionWithSources(String question) {
        ChatResponse response = chatClient.prompt()
                .user(question)
                .call()
                .chatResponse();
        List<Document> retrieved = response.getMetadata().get(QuestionAnswerAdvisor.RETRIEVED_DOCUMENTS);
        return new AnswerWithSources(
                response.getResult().getOutput().getText(),
                toSources(retrieved));
    }

    /** Closed-book baseline: same system prompt, no retrieved context. */
    public String askQuestionWithoutRetrieval(String question) {
        return noRetrievalChatClient.prompt()
                .user(question)
                .call()
                .content();
    }

    /** Raw similarity search, for retrieval-recall checks against a gold passage. */
    public List<RetrievedChunk> search(String question, int topK) {
        List<Document> docs = vectorStore.similaritySearch(
                SearchRequest.builder().query(question).topK(topK).similarityThreshold(0.0).build());
        return toSources(docs);
    }

    public static List<RetrievedChunk> toSources(List<Document> docs) {
        if (docs == null) return List.of();
        return docs.stream()
                .map(d -> new RetrievedChunk(
                        String.valueOf(d.getMetadata().getOrDefault("regulation", "Unknown")),
                        d.getMetadata().get("page_number") == null ? null : String.valueOf(d.getMetadata().get("page_number")),
                        d.getScore(),
                        d.getText()))
                .collect(Collectors.toList());
    }

    public record RetrievedChunk(String regulation, String page, Double score, String text) {}

    public record AnswerWithSources(String answer, List<RetrievedChunk> sources) {}

    // Ask a question — searches ALL ingested documents
    public String askQuestion(String question) {
        return chatClient.prompt()
                .user(question)
                .call()
                .content();
    }

    // Ask a question — restricted to a specific regulation via metadata filter
    public String askQuestionWithFilter(String question, String regulation) {
        return chatClient.prompt()
                .user(question)
                .advisors(advisor -> advisor.param(
                        QuestionAnswerAdvisor.FILTER_EXPRESSION,
                        "regulation == '" + regulation + "'"))
                .call()
                .content();
    }
}
