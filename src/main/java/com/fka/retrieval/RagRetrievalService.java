package com.fka.retrieval;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

@Service
public class RagRetrievalService {

    private final ChatClient chatClient;
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
                                .topK(5)              // Return 5 most similar chunks
                                .similarityThreshold(0.7) // Only chunks with >= 0.7 cosine similarity
                                .build())
                        .build())
                .build();
    }

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
