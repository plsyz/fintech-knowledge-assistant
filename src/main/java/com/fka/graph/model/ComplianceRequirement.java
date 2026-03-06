package com.fka.graph.model;

import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;

@Node("ComplianceRequirement")
public class ComplianceRequirement {

    @Id
    @GeneratedValue
    private Long id;

    private String name;
    private String article;
    private String description;
    private String category; // SECURITY, TRANSPARENCY, LICENSING, OPENNESS

    public ComplianceRequirement() {
    }

    public ComplianceRequirement(String name, String article, String description, String category) {
        this.name = name;
        this.article = article;
        this.description = description;
        this.category = category;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getArticle() { return article; }
    public void setArticle(String article) { this.article = article; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
}
