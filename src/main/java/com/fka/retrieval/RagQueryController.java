package com.fka.retrieval;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/rag")
public class RagQueryController {

    private final RagRetrievalService ragRetrievalService;

    public RagQueryController(RagRetrievalService ragRetrievalService) {
        this.ragRetrievalService = ragRetrievalService;
    }

    // GET /api/rag/ask?question=What is PSD2?
    @GetMapping("/ask")
    public Map<String, String> ask(@RequestParam String question) {
        String answer = ragRetrievalService.askQuestion(question);
        return Map.of("question", question, "answer", answer);
    }

    // GET /api/rag/ask/filtered?question=What is SCA?&regulation=PSD2
    @GetMapping("/ask/filtered")
    public Map<String, String> askFiltered(@RequestParam String question,
                                           @RequestParam String regulation) {
        String answer = ragRetrievalService.askQuestionWithFilter(question, regulation);
        return Map.of("question", question, "regulation", regulation, "answer", answer);
    }
}
