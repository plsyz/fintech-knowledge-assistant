package com.fka.graph.model;

import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;

@Node("PaymentMethod")
public class PaymentMethod {

    @Id
    @GeneratedValue
    private Long id;

    private String name;
    private String type; // PUSH, PULL, DEFERRED

    public PaymentMethod() {
    }

    public PaymentMethod(String name, String type) {
        this.name = name;
        this.type = type;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
}
