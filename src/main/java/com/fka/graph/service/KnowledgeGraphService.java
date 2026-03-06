package com.fka.graph.service;

import com.fka.graph.model.ComplianceRequirement;
import com.fka.graph.model.PaymentProvider;
import com.fka.graph.model.Regulation;
import com.fka.graph.repository.PaymentProviderRepository;
import com.fka.graph.repository.RegulationRepository;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class KnowledgeGraphService {

    private final PaymentProviderRepository providerRepository;
    private final RegulationRepository regulationRepository;
    private final Driver driver;

    public KnowledgeGraphService(PaymentProviderRepository providerRepository,
                                  RegulationRepository regulationRepository,
                                  Driver driver) {
        this.providerRepository = providerRepository;
        this.regulationRepository = regulationRepository;
        this.driver = driver;
    }

    public List<PaymentProvider> getAllProviders() {
        return providerRepository.findAll();
    }

    public Optional<PaymentProvider> getProviderByName(String name) {
        return providerRepository.findByName(name);
    }

    public List<ComplianceRequirement> getComplianceRequirements(String providerName) {
        // Traverse: Provider -> REGULATED_BY -> Regulation -> REQUIRES -> ComplianceRequirement
        try (var session = driver.session()) {
            var result = session.run("""
                MATCH (p:PaymentProvider {name: $name})-[:REGULATED_BY]->(r:Regulation)-[:REQUIRES]->(c:ComplianceRequirement)
                RETURN c.name AS name, c.article AS article, c.description AS description, c.category AS category, r.name AS regulation
                """, Map.of("name", providerName));

            return result.list(record -> {
                ComplianceRequirement req = new ComplianceRequirement(
                    record.get("name").asString(),
                    record.get("article").asString(),
                    record.get("description").asString(),
                    record.get("category").asString()
                );
                return req;
            });
        }
    }

    public List<PaymentProvider> getProvidersByRegulation(String regulationName) {
        return providerRepository.findByRegulation(regulationName);
    }

    public List<Map<String, String>> getRegulationChain(String regulationName) {
        // Follow SUPERSEDES chain up to 5 hops
        try (var session = driver.session()) {
            var result = session.run("""
                MATCH path = (r:Regulation {name: $name})-[:SUPERSEDES*0..5]->(older:Regulation)
                RETURN older.name AS name, older.fullName AS fullName, older.directiveNumber AS directiveNumber,
                       toString(older.effectiveDate) AS effectiveDate
                ORDER BY older.effectiveDate DESC
                """, Map.of("name", regulationName));

            return result.list(record -> Map.of(
                "name", record.get("name").asString(),
                "fullName", record.get("fullName").asString(),
                "directiveNumber", record.get("directiveNumber").asString(),
                "effectiveDate", record.get("effectiveDate").asString()
            ));
        }
    }

    // Format graph context as readable text for the LLM
    public String formatProviderContext(String providerName) {
        StringBuilder sb = new StringBuilder();

        Optional<PaymentProvider> providerOpt = providerRepository.findByName(providerName);
        if (providerOpt.isEmpty()) return "";

        PaymentProvider provider = providerOpt.get();
        sb.append(String.format("- Provider: %s (type: %s, country: %s, license: %s)\n",
                provider.getName(), provider.getType(), provider.getCountry(), provider.getLicenseType()));

        // Regulations and their requirements
        if (provider.getRegulations() != null) {
            for (Regulation reg : provider.getRegulations()) {
                sb.append(String.format("  - Regulated by: %s (%s, effective %s)\n",
                        reg.getName(), reg.getFullName(),
                        reg.getEffectiveDate() != null ? reg.getEffectiveDate().toString() : "N/A"));

                // Fetch requirements for this regulation
                List<ComplianceRequirement> reqs = regulationRepository.findRequirementsByRegulationName(reg.getName());
                for (ComplianceRequirement req : reqs) {
                    sb.append(String.format("    - Requires: %s (%s) [%s]\n",
                            req.getName(), req.getArticle(), req.getCategory()));
                }
            }
        }

        // Payment methods
        if (provider.getPaymentMethods() != null && !provider.getPaymentMethods().isEmpty()) {
            for (var method : provider.getPaymentMethods()) {
                sb.append(String.format("  - Supports: %s (%s)\n", method.getName(), method.getType()));
            }
        }

        return sb.toString();
    }
}
