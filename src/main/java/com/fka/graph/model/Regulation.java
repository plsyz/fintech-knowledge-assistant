package com.fka.graph.model;

import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;

import java.time.LocalDate;
import java.util.HashSet;
import java.util.Set;

@Node("Regulation")
public class Regulation {

    @Id
    @GeneratedValue
    private Long id;

    private String name;
    private String fullName;
    private String directiveNumber;
    private LocalDate effectiveDate;
    private String jurisdiction;

    @Relationship(type = "REQUIRES", direction = Relationship.Direction.OUTGOING)
    private Set<ComplianceRequirement> requirements = new HashSet<>();

    @Relationship(type = "SUPERSEDES", direction = Relationship.Direction.OUTGOING)
    private Regulation previousVersion;

    public Regulation() {
    }

    public Regulation(String name, String fullName, String directiveNumber,
                      LocalDate effectiveDate, String jurisdiction) {
        this.name = name;
        this.fullName = fullName;
        this.directiveNumber = directiveNumber;
        this.effectiveDate = effectiveDate;
        this.jurisdiction = jurisdiction;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public String getDirectiveNumber() { return directiveNumber; }
    public void setDirectiveNumber(String directiveNumber) { this.directiveNumber = directiveNumber; }

    public LocalDate getEffectiveDate() { return effectiveDate; }
    public void setEffectiveDate(LocalDate effectiveDate) { this.effectiveDate = effectiveDate; }

    public String getJurisdiction() { return jurisdiction; }
    public void setJurisdiction(String jurisdiction) { this.jurisdiction = jurisdiction; }

    public Set<ComplianceRequirement> getRequirements() { return requirements; }
    public void setRequirements(Set<ComplianceRequirement> requirements) { this.requirements = requirements; }

    public Regulation getPreviousVersion() { return previousVersion; }
    public void setPreviousVersion(Regulation previousVersion) { this.previousVersion = previousVersion; }
}
