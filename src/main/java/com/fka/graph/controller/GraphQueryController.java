package com.fka.graph.controller;

import com.fka.graph.model.ComplianceRequirement;
import com.fka.graph.model.PaymentProvider;
import com.fka.graph.service.KnowledgeGraphService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/graph")
public class GraphQueryController {

    private final KnowledgeGraphService knowledgeGraphService;

    public GraphQueryController(KnowledgeGraphService knowledgeGraphService) {
        this.knowledgeGraphService = knowledgeGraphService;
    }

    @GetMapping("/providers")
    public List<PaymentProvider> getAllProviders() {
        return knowledgeGraphService.getAllProviders();
    }

    @GetMapping("/providers/{name}")
    public ResponseEntity<PaymentProvider> getProvider(@PathVariable String name) {
        return knowledgeGraphService.getProviderByName(name)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/providers/{name}/compliance")
    public List<ComplianceRequirement> getComplianceRequirements(@PathVariable String name) {
        return knowledgeGraphService.getComplianceRequirements(name);
    }

    @GetMapping("/regulations/{name}/providers")
    public List<PaymentProvider> getProvidersByRegulation(@PathVariable String name) {
        return knowledgeGraphService.getProvidersByRegulation(name);
    }

    @GetMapping("/regulations/{name}/chain")
    public List<Map<String, String>> getRegulationChain(@PathVariable String name) {
        return knowledgeGraphService.getRegulationChain(name);
    }
}
