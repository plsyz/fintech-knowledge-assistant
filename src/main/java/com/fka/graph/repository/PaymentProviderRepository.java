package com.fka.graph.repository;

import com.fka.graph.model.PaymentProvider;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;

import java.util.List;
import java.util.Optional;

public interface PaymentProviderRepository extends Neo4jRepository<PaymentProvider, Long> {

    Optional<PaymentProvider> findByName(String name);

    List<PaymentProvider> findByCountry(String country);

    @Query("MATCH (p:PaymentProvider)-[:REGULATED_BY]->(r:Regulation {name: $regulationName}) RETURN p")
    List<PaymentProvider> findByRegulation(String regulationName);
}
