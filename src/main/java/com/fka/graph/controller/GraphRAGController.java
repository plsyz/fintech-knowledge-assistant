package com.fka.graph.controller;

import com.fka.graph.service.GraphRAGService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/graph-rag")
public class GraphRAGController {

    private final GraphRAGService graphRAGService;

    public GraphRAGController(GraphRAGService graphRAGService) {
        this.graphRAGService = graphRAGService;
    }

    @GetMapping("/ask")
    public Map<String, String> ask(@RequestParam String question) {
        String answer = graphRAGService.answerWithGraphContext(question);
        return Map.of("question", question, "answer", answer);
    }
}
