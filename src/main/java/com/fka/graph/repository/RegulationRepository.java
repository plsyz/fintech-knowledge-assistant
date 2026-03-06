package com.fka.graph.repository;

import com.fka.graph.model.ComplianceRequirement;
import com.fka.graph.model.Regulation;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;

import java.util.List;
import java.util.Optional;

public interface RegulationRepository extends Neo4jRepository<Regulation, Long> {

    Optional<Regulation> findByName(String name);

    @Query("MATCH (r:Regulation {name: $name})-[:REQUIRES]->(c:ComplianceRequirement) RETURN c")
    List<ComplianceRequirement> findRequirementsByRegulationName(String name);
}
