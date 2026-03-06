package com.fka.graph.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;

import java.util.HashSet;
import java.util.Set;

@Node("PaymentProvider")
public class PaymentProvider {

    @Id
    @GeneratedValue
    private Long id;

    private String name;
    private String type; // PSP, ASPSP, PISP, AISP
    private String country;
    private String licenseType;

    @Relationship(type = "REGULATED_BY", direction = Relationship.Direction.OUTGOING)
    @JsonIgnoreProperties({"requirements", "previousVersion"})
    private Set<Regulation> regulations = new HashSet<>();

    @Relationship(type = "SUPPORTS", direction = Relationship.Direction.OUTGOING)
    private Set<PaymentMethod> paymentMethods = new HashSet<>();

    public PaymentProvider() {
    }

    public PaymentProvider(String name, String type, String country, String licenseType) {
        this.name = name;
        this.type = type;
        this.country = country;
        this.licenseType = licenseType;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    public String getLicenseType() { return licenseType; }
    public void setLicenseType(String licenseType) { this.licenseType = licenseType; }

    public Set<Regulation> getRegulations() { return regulations; }
    public void setRegulations(Set<Regulation> regulations) { this.regulations = regulations; }

    public Set<PaymentMethod> getPaymentMethods() { return paymentMethods; }
    public void setPaymentMethods(Set<PaymentMethod> paymentMethods) { this.paymentMethods = paymentMethods; }
}
