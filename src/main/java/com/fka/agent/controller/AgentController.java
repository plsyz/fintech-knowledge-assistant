package com.fka.agent.controller;

import com.fka.agent.workflow.ComplianceCheckWorkflow;
import com.fka.agent.workflow.RegulationRouterWorkflow;
import com.fka.graph.service.GraphRAGService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/agent")
public class AgentController {

    private final ComplianceCheckWorkflow complianceCheckWorkflow;
    private final RegulationRouterWorkflow regulationRouterWorkflow;
    private final GraphRAGService graphRAGService;

    public AgentController(ComplianceCheckWorkflow complianceCheckWorkflow,
                           RegulationRouterWorkflow regulationRouterWorkflow,
                           GraphRAGService graphRAGService) {
        this.complianceCheckWorkflow = complianceCheckWorkflow;
        this.regulationRouterWorkflow = regulationRouterWorkflow;
        this.graphRAGService = graphRAGService;
    }

    // Chain workflow: 4-step compliance analysis pipeline
    @PostMapping("/compliance-check")
    public String complianceCheck(@RequestBody String transactionDescription) {
        return complianceCheckWorkflow.runComplianceCheck(transactionDescription);
    }

    // Routing workflow: classify question → route to domain expert
    @GetMapping("/ask")
    public String ask(@RequestParam String question) {
        return regulationRouterWorkflow.route(question);
    }

    // GraphRAG from Phase 2: knowledge graph + vector search combined
    @GetMapping("/ask/graph-rag")
    public String askGraphRag(@RequestParam String question) {
        return graphRAGService.answerWithGraphContext(question);
    }
}
