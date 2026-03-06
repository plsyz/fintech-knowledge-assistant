package com.fka.graph.service;

import org.neo4j.driver.Driver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

@Component
public class GraphDataLoader implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(GraphDataLoader.class);
    private final Driver driver;

    public GraphDataLoader(Driver driver) {
        this.driver = driver;
    }

    @Override
    public void run(ApplicationArguments args) {
        try (var session = driver.session()) {
            // Check if data already exists — skip seeding if so
            var result = session.run("MATCH (n) RETURN count(n) AS count");
            long count = result.single().get("count").asLong();
            if (count > 0) {
                log.info("Knowledge graph already has {} nodes — skipping seed.", count);
                return;
            }

            log.info("Seeding knowledge graph...");

            // Block 1: Payment Providers (6 nodes)
            session.run("""
                MERGE (p:PaymentProvider {name: 'Riverty'})
                SET p.type = 'PSP', p.country = 'DE', p.licenseType = 'Payment Institution'
                """);
            session.run("""
                MERGE (p:PaymentProvider {name: 'Klarna'})
                SET p.type = 'PSP', p.country = 'SE', p.licenseType = 'Banking License'
                """);
            session.run("""
                MERGE (p:PaymentProvider {name: 'Adyen'})
                SET p.type = 'PSP', p.country = 'NL', p.licenseType = 'Banking License'
                """);
            session.run("""
                MERGE (p:PaymentProvider {name: 'Stripe'})
                SET p.type = 'PSP', p.country = 'IE', p.licenseType = 'E-Money Institution'
                """);
            session.run("""
                MERGE (p:PaymentProvider {name: 'Deutsche Bank'})
                SET p.type = 'ASPSP', p.country = 'DE', p.licenseType = 'Banking License'
                """);
            session.run("""
                MERGE (p:PaymentProvider {name: 'N26'})
                SET p.type = 'ASPSP', p.country = 'DE', p.licenseType = 'Banking License'
                """);
            log.info("Created 6 PaymentProvider nodes.");

            // Block 2: Regulations (5 nodes)
            session.run("""
                MERGE (r:Regulation {name: 'PSD2'})
                SET r.fullName = 'Payment Services Directive 2',
                    r.directiveNumber = '2015/2366',
                    r.effectiveDate = date('2018-01-13'),
                    r.jurisdiction = 'EU'
                """);
            session.run("""
                MERGE (r:Regulation {name: 'PSD1'})
                SET r.fullName = 'Payment Services Directive 1',
                    r.directiveNumber = '2007/64',
                    r.effectiveDate = date('2009-11-01'),
                    r.jurisdiction = 'EU'
                """);
            session.run("""
                MERGE (r:Regulation {name: 'SCA-RTS'})
                SET r.fullName = 'Regulatory Technical Standards on Strong Customer Authentication',
                    r.directiveNumber = '2018/389',
                    r.effectiveDate = date('2019-09-14'),
                    r.jurisdiction = 'EU'
                """);
            session.run("""
                MERGE (r:Regulation {name: 'GDPR'})
                SET r.fullName = 'General Data Protection Regulation',
                    r.directiveNumber = '2016/679',
                    r.effectiveDate = date('2018-05-25'),
                    r.jurisdiction = 'EU'
                """);
            session.run("""
                MERGE (r:Regulation {name: 'AMLD5'})
                SET r.fullName = '5th Anti-Money Laundering Directive',
                    r.directiveNumber = '2018/843',
                    r.effectiveDate = date('2020-01-10'),
                    r.jurisdiction = 'EU'
                """);
            log.info("Created 5 Regulation nodes.");

            // Block 3: Compliance Requirements (3 nodes connected to PSD2)
            session.run("""
                MERGE (c:ComplianceRequirement {name: 'Strong Customer Authentication'})
                SET c.article = 'Article 97',
                    c.description = 'Payment service providers must apply strong customer authentication where the payer initiates an electronic payment transaction, accesses its payment account online, or carries out any action through a remote channel which may imply a risk of payment fraud.',
                    c.category = 'SECURITY'
                """);
            session.run("""
                MERGE (c:ComplianceRequirement {name: 'Third Party Provider Access'})
                SET c.article = 'Articles 66-67',
                    c.description = 'Account servicing payment service providers must allow payment initiation service providers and account information service providers to access payment accounts, provided the customer has given explicit consent.',
                    c.category = 'OPENNESS'
                """);
            session.run("""
                MERGE (c:ComplianceRequirement {name: 'Payment Transparency'})
                SET c.article = 'Title III',
                    c.description = 'Payment service providers must provide clear and comprehensive information to payment service users about charges, exchange rates, and execution time before and after payment transactions.',
                    c.category = 'TRANSPARENCY'
                """);
            // Connect requirements to PSD2
            session.run("""
                MATCH (r:Regulation {name: 'PSD2'}), (c:ComplianceRequirement {name: 'Strong Customer Authentication'})
                MERGE (r)-[:REQUIRES]->(c)
                """);
            session.run("""
                MATCH (r:Regulation {name: 'PSD2'}), (c:ComplianceRequirement {name: 'Third Party Provider Access'})
                MERGE (r)-[:REQUIRES]->(c)
                """);
            session.run("""
                MATCH (r:Regulation {name: 'PSD2'}), (c:ComplianceRequirement {name: 'Payment Transparency'})
                MERGE (r)-[:REQUIRES]->(c)
                """);
            log.info("Created 3 ComplianceRequirement nodes and linked to PSD2.");

            // Block 4: Payment Methods (5 nodes)
            session.run("""
                MERGE (m:PaymentMethod {name: 'SEPA Credit Transfer'}) SET m.type = 'PUSH'
                """);
            session.run("""
                MERGE (m:PaymentMethod {name: 'SEPA Direct Debit'}) SET m.type = 'PULL'
                """);
            session.run("""
                MERGE (m:PaymentMethod {name: 'Card Payment'}) SET m.type = 'PULL'
                """);
            session.run("""
                MERGE (m:PaymentMethod {name: 'Buy Now Pay Later'}) SET m.type = 'DEFERRED'
                """);
            session.run("""
                MERGE (m:PaymentMethod {name: 'Instant Payment'}) SET m.type = 'PUSH'
                """);
            log.info("Created 5 PaymentMethod nodes.");

            // Block 5: Relationships

            // All 6 providers REGULATED_BY PSD2
            session.run("""
                MATCH (p:PaymentProvider), (r:Regulation {name: 'PSD2'})
                MERGE (p)-[:REGULATED_BY]->(r)
                """);
            // All 6 providers REGULATED_BY GDPR
            session.run("""
                MATCH (p:PaymentProvider), (r:Regulation {name: 'GDPR'})
                MERGE (p)-[:REGULATED_BY]->(r)
                """);
            // PSD2 SUPERSEDES PSD1
            session.run("""
                MATCH (psd2:Regulation {name: 'PSD2'}), (psd1:Regulation {name: 'PSD1'})
                MERGE (psd2)-[:SUPERSEDES]->(psd1)
                """);

            // Provider SUPPORTS payment methods
            session.run("""
                MATCH (p:PaymentProvider {name: 'Riverty'}), (m:PaymentMethod {name: 'Buy Now Pay Later'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Riverty'}), (m:PaymentMethod {name: 'SEPA Direct Debit'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Klarna'}), (m:PaymentMethod {name: 'Buy Now Pay Later'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Klarna'}), (m:PaymentMethod {name: 'Card Payment'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Adyen'}), (m:PaymentMethod {name: 'Card Payment'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Adyen'}), (m:PaymentMethod {name: 'Instant Payment'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Stripe'}), (m:PaymentMethod {name: 'Card Payment'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            session.run("""
                MATCH (p:PaymentProvider {name: 'Stripe'}), (m:PaymentMethod {name: 'SEPA Credit Transfer'})
                MERGE (p)-[:SUPPORTS]->(m)
                """);
            log.info("Created all relationships (REGULATED_BY, SUPPORTS, SUPERSEDES).");

            log.info("Knowledge graph seeding complete!");
        }
    }
}
