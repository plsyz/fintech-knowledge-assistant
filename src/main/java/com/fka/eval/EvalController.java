package com.fka.eval;

import com.fka.graph.service.GraphRAGService;
import com.fka.retrieval.RagRetrievalService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Evaluation endpoints. Enabled only with {@code fka.eval.enabled=true}.
 *
 * Exposes the three answering conditions compared in the evaluation, each returning the
 * context that was actually used, so that citation accuracy and grounding can be scored:
 *
 *   /api/eval/ask/vector         vector RAG (QuestionAnswerAdvisor, top-15 chunks) + retrieved chunks
 *   /api/eval/ask/graph-rag      GraphRAG fusion (knowledge graph + top-5 chunks) + both contexts
 *   /api/eval/ask/no-retrieval   closed-book baseline: same model and system prompt, no context
 *   /api/eval/search             raw similarity search (retrieval-recall check for gold passages)
 */
@RestController
@RequestMapping("/api/eval")
@ConditionalOnProperty(name = "fka.eval.enabled", havingValue = "true")
public class EvalController {

    private final RagRetrievalService ragRetrievalService;
    private final GraphRAGService graphRAGService;

    public EvalController(RagRetrievalService ragRetrievalService, GraphRAGService graphRAGService) {
        this.ragRetrievalService = ragRetrievalService;
        this.graphRAGService = graphRAGService;
    }

    @GetMapping("/ask/vector")
    public Map<String, Object> askVector(@RequestParam String question) {
        RagRetrievalService.AnswerWithSources r = ragRetrievalService.askQuestionWithSources(question);
        return Map.of("condition", "vector", "question", question,
                "answer", r.answer(), "sources", r.sources());
    }

    @GetMapping("/ask/graph-rag")
    public Map<String, Object> askGraphRag(@RequestParam String question) {
        GraphRAGService.GraphRAGResult r = graphRAGService.answerWithGraphContextDetailed(question);
        return Map.of("condition", "graph-rag", "question", question,
                "answer", r.answer(), "extractedEntities", r.extractedEntities(),
                "graphContext", r.graphContext(), "sources", r.sources());
    }

    @GetMapping("/ask/no-retrieval")
    public Map<String, Object> askNoRetrieval(@RequestParam String question) {
        return Map.of("condition", "no-retrieval", "question", question,
                "answer", ragRetrievalService.askQuestionWithoutRetrieval(question), "sources", List.of());
    }

    @GetMapping("/search")
    public Map<String, Object> search(@RequestParam String question,
                                      @RequestParam(defaultValue = "15") int topK) {
        return Map.of("question", question, "topK", topK,
                "chunks", ragRetrievalService.search(question, topK));
    }
}
