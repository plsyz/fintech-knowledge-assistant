#!/usr/bin/env python3
"""
Build the gold question set -> data/gold_questions.jsonl

Fields
  id            Q001 ...
  question
  answerable    true if the answer is in the ingested corpus (11 regulations, see README)
  regulation    canonical id (see REG_ALIASES) or null
  article       article reference the answer rests on (string) or null
  gold_answer   short reference answer used by the LLM judge
  key_facts     facts/numbers the answer must contain to count as correct
  passage_hint  phrase expected in the supporting chunk (retrieval-recall check)
  kind          definition | threshold | deadline | obligation | liability | scope | cross | unanswerable
  confidence    high | medium  (how sure the author is about the article reference; verify medium ones on EUR-Lex)
  why_unanswerable  for unanswerable items: not_in_corpus | fabricated | outside_law_text | false_premise

Article references were written from the author's knowledge of the directives and
regulations and MUST be spot-checked against the ingested PDFs before results are reported;
run_eval.py --check-retrieval reports which passage_hints are actually found in the corpus.
"""
import json
from pathlib import Path

# canonical id -> strings that count as a correct mention of that regulation in an answer
REG_ALIASES = {
    "PSD2":    ["PSD2", "PSD 2", "2015/2366", "Payment Services Directive"],
    "SCA-RTS": ["RTS", "2018/389", "regulatory technical standards", "Delegated Regulation"],
    "SEPA":    ["SEPA", "260/2012"],
    "MICA":    ["MiCA", "MICA", "2023/1114", "Markets in Crypto-Assets"],
    "DORA":    ["DORA", "2022/2554", "Digital Operational Resilience"],
    "EMD2":    ["EMD2", "EMD 2", "2009/110", "E-Money Directive", "Electronic Money Directive"],
    "AMLD5":   ["AMLD5", "AMLD 5", "2018/843", "5th Anti-Money Laundering", "Fifth Anti-Money Laundering", "2015/849"],
    "AMLD6":   ["AMLD6", "AMLD 6", "2018/1673", "6th Anti-Money Laundering", "Sixth Anti-Money Laundering"],
    "GDPR":    ["GDPR", "2016/679", "General Data Protection"],
    "IFR":     ["IFR", "2015/751", "Interchange Fee Regulation"],
}

Q = []


def q(question, regulation, article, gold, facts, hint, kind, confidence="high"):
    Q.append(dict(question=question, answerable=True, regulation=regulation, article=article,
                  gold_answer=gold, key_facts=facts, passage_hint=hint, kind=kind,
                  confidence=confidence, why_unanswerable=None))


def u(question, why, gold="The ingested regulations do not contain this information; the assistant should say so."):
    Q.append(dict(question=question, answerable=False, regulation=None, article=None,
                  gold_answer=gold, key_facts=[], passage_hint=None, kind="unanswerable",
                  confidence="high", why_unanswerable=why))


# ------------------------------------------------------------------ PSD2 (Directive (EU) 2015/2366)
q("What are the three categories of elements that strong customer authentication must be based on under PSD2?",
  "PSD2", "Art. 4(30)", "Knowledge (something only the user knows), possession (something only the user possesses) and inherence (something the user is), at least two independent elements.",
  ["knowledge", "possession", "inherence", "two or more"], "knowledge", "definition")
q("Within what period must a payment service user notify their payment service provider of an unauthorised transaction to obtain rectification under PSD2?",
  "PSD2", "Art. 71", "Without undue delay on becoming aware of it and no later than 13 months after the debit date.",
  ["13 months", "without undue delay"], "13 months", "deadline")
q("How quickly must a payment service provider refund an unauthorised payment transaction under PSD2?",
  "PSD2", "Art. 73", "Immediately, and in any event no later than by the end of the following business day, after noting or being notified of the transaction.",
  ["end of the following business day", "immediately"], "following business day", "liability")
q("What is the maximum amount a payer can be obliged to bear for losses from unauthorised transactions resulting from a lost or stolen payment instrument under PSD2?",
  "PSD2", "Art. 74(1)", "Up to a maximum of EUR 50, unless the payer acted fraudulently or with gross negligence.",
  ["EUR 50", "50"], "EUR 50", "liability")
q("Within what period can a payer request a refund of an authorised direct debit under PSD2, and how long does the provider have to respond?",
  "PSD2", "Art. 76-77", "The payer may request a refund within 8 weeks from the debit date; the provider must refund or justify refusal within 10 business days.",
  ["8 weeks", "10 business days"], "eight weeks", "deadline")
q("What is the maximum execution time for a credit transfer in euro within the EU under PSD2?",
  "PSD2", "Art. 83", "The payee's provider's account must be credited by the end of the next business day after receipt of the payment order (D+1); may be extended by one business day for paper-initiated transactions.",
  ["end of the following business day", "business day"], "following business day", "obligation")
q("Under PSD2, when must a payment service provider apply strong customer authentication?",
  "PSD2", "Art. 97(1)", "When the payer accesses its payment account online, initiates an electronic payment transaction, or carries out any action through a remote channel which may imply a risk of payment fraud or other abuses.",
  ["accesses", "payment account online", "electronic payment transaction", "remote channel"], "remote channel", "obligation")
q("What does 'dynamic linking' require for remote electronic payment transactions under PSD2?",
  "PSD2", "Art. 97(2)", "The authentication must include elements which dynamically link the transaction to a specific amount and a specific payee.",
  ["specific amount", "specific payee"], "dynamically link", "definition")
q("What is the initial capital requirement for a payment institution that only provides payment initiation services under PSD2?",
  "PSD2", "Art. 7(b)", "EUR 50 000.",
  ["50 000", "50,000", "50000"], "EUR 50 000", "threshold")
q("What is the initial capital requirement for a payment institution providing money remittance only under PSD2?",
  "PSD2", "Art. 7(a)", "EUR 20 000.",
  ["20 000", "20,000", "20000"], "EUR 20 000", "threshold")
q("What is the initial capital requirement for a payment institution providing the full range of payment services (points 1-5 of Annex I) under PSD2?",
  "PSD2", "Art. 7(c)", "EUR 125 000.",
  ["125 000", "125,000", "125000"], "EUR 125 000", "threshold")
q("Under PSD2, may an account servicing payment service provider deny an account information service provider access to a payment account?",
  "PSD2", "Art. 68(5)", "Only for objectively justified and duly evidenced reasons relating to unauthorised or fraudulent access; it must inform the payer and the competent authority.",
  ["objectively justified", "fraudulent"], "objectively justified", "obligation")
q("Does a payment initiation service provider need a contractual relationship with the account servicing payment service provider under PSD2?",
  "PSD2", "Art. 66(5)", "No. Provision of payment initiation services shall not be dependent on the existence of a contractual relationship between the PISP and the ASPSP.",
  ["not", "contractual relationship"], "contractual relationship", "obligation")
q("How many times may an account information service provider access account information without the user actively requesting it, according to the SCA RTS?",
  "SCA-RTS", "Art. 36(5)", "No more than four times in a 24-hour period, unless more frequent access is agreed with the ASPSP.",
  ["four times", "4 times", "24"], "four times", "threshold")
q("What is the deadline for a payment service provider to reply to a user's complaint under PSD2?",
  "PSD2", "Art. 101(2)", "Within an adequate timeframe and at the latest within 15 business days; in exceptional situations a holding reply and final reply within 35 business days.",
  ["15 business days", "35 business days"], "15 business days", "deadline")
q("By what date did Member States have to apply the measures transposing PSD2?",
  "PSD2", "Art. 115", "Member States adopted measures by 13 January 2018 and apply them from that date.",
  ["13 January 2018"], "13 January 2018", "deadline")
q("How much notice must a payment service provider give before changing the conditions of a framework contract under PSD2?",
  "PSD2", "Art. 54", "At least 2 months before the proposed date of application.",
  ["2 months", "two months"], "two months", "deadline")
q("What is the maximum notice period a framework contract may impose on a payment service user who wants to terminate it under PSD2?",
  "PSD2", "Art. 55(1)", "The notice period must not exceed 1 month.",
  ["1 month", "one month"], "one month", "deadline")
q("Under PSD2, must a payment service provider notify authorities of major operational or security incidents, and how quickly?",
  "PSD2", "Art. 96(1)", "Yes, without undue delay, to the competent authority in the home Member State.",
  ["without undue delay", "competent authority"], "without undue delay", "obligation")
q("Under PSD2, may a payee apply a surcharge for the use of payment instruments whose interchange fees are capped by the Interchange Fee Regulation?",
  "PSD2", "Art. 62(4)", "No. Payees may not request charges for the use of instruments for which interchange fees are regulated under Chapter II of the IFR, nor for SEPA credit transfers and direct debits.",
  ["shall not", "surcharge", "Interchange Fee"], "Interchange Fee", "cross")
q("Which PSD2 provision excludes 'limited network' instruments from the directive's scope?",
  "PSD2", "Art. 3(k)", "Article 3(k): instruments usable only in a limited way, e.g. within the issuer's premises or a limited network of providers, or for a very limited range of goods or services.",
  ["limited network", "3(k)"], "limited network", "scope")
q("Under PSD2, what is the maximum delay with which a payer's account may be debited relative to the execution of a transaction (value dating)?",
  "PSD2", "Art. 87", "The debit value date must be no earlier than the point in time at which the amount is debited; the credit value date must be no later than the business day the amount is credited to the payee's provider.",
  ["value date", "business day"], "value date", "obligation")
q("What does PSD2 require regarding the burden of proof when a payment service user denies having authorised a transaction?",
  "PSD2", "Art. 72", "The payment service provider must prove the transaction was authenticated, accurately recorded, entered in the accounts and not affected by a technical breakdown; use of an instrument alone is not necessarily sufficient to prove authorisation.",
  ["burden", "authenticated", "not necessarily sufficient"], "burden of proof", "liability", "medium")

# ------------------------------------------------------------------ SCA RTS (Delegated Regulation (EU) 2018/389)
q("What is the per-transaction threshold for the contactless point-of-sale SCA exemption in the SCA RTS?",
  "SCA-RTS", "Art. 11", "EUR 50 per transaction, with a cumulative limit of EUR 150 or five consecutive transactions since the last SCA.",
  ["EUR 50", "150", "five"], "contactless", "threshold")
q("What is the threshold for the low-value remote electronic payment exemption from SCA?",
  "SCA-RTS", "Art. 16", "EUR 30 per transaction, provided the cumulative amount since the last SCA does not exceed EUR 100 or five consecutive transactions.",
  ["EUR 30", "100", "five"], "EUR 30", "threshold")
q("Under the transaction risk analysis exemption in the SCA RTS, what are the exemption threshold values and the corresponding reference fraud rates for remote card-based payments?",
  "SCA-RTS", "Art. 18 and Annex", "EUR 500 at a fraud rate of 0.01 %, EUR 250 at 0.06 % and EUR 100 at 0.13 %.",
  ["500", "250", "100", "0.13", "0.06", "0.01"], "reference fraud rate", "threshold")
q("How often may a user access payment account information through an AISP without SCA under the SCA RTS, before SCA must be re-applied?",
  "SCA-RTS", "Art. 10", "SCA is not required for viewing balance or 90 days of transaction history, but SCA must be applied at least every 90 days (original RTS; amended to 180 days by Regulation 2022/2360).",
  ["90 days"], "90 days", "threshold", "medium")
q("Which SCA RTS exemption covers payments at unattended terminals for transport fares and parking fees?",
  "SCA-RTS", "Art. 12", "Article 12: no SCA for electronic payment transactions at unattended payment terminals for transport fares or parking fees.",
  ["transport fare", "parking"], "parking fees", "scope")
q("How does the trusted beneficiaries exemption in the SCA RTS work?",
  "SCA-RTS", "Art. 13", "The payer may create or amend a list of trusted beneficiaries with SCA; subsequent payments to beneficiaries on that list are exempt from SCA.",
  ["trusted beneficiaries", "list"], "trusted beneficiaries", "obligation")
q("Under the SCA RTS, is SCA required for each payment in a series of recurring transactions?",
  "SCA-RTS", "Art. 14", "No. SCA applies when the series is created or amended; subsequent transactions of the same amount to the same payee are exempt.",
  ["recurring", "same amount", "same payee"], "recurring transactions", "scope")
q("Does the SCA RTS exempt credit transfers between accounts held by the same person?",
  "SCA-RTS", "Art. 15", "Yes, where payer and payee are the same natural or legal person and both accounts are held by the same ASPSP.",
  ["same natural or legal person", "same account servicing"], "same natural or legal person", "scope")
q("What must the authentication code generated under the SCA RTS satisfy?",
  "SCA-RTS", "Art. 4", "It must not reveal information about the underlying elements, must not be possible to generate a new code from knowledge of a previous one, and cannot be forged.",
  ["authentication code", "forge"], "authentication code", "definition", "medium")
q("What does the SCA RTS require regarding dynamic linking of authentication codes?",
  "SCA-RTS", "Art. 5", "The payer is made aware of the amount and payee; the code is specific to the amount and payee agreed; any change invalidates the code; confidentiality, authenticity and integrity of amount and payee are protected.",
  ["amount", "payee", "specific"], "dynamically links", "obligation")
q("From what date did the SCA RTS apply?",
  "SCA-RTS", "Art. 38", "14 September 2019 (18 months after entry into force).",
  ["14 September 2019"], "14 September 2019", "deadline")
q("Under the SCA RTS, what is a dedicated interface and what contingency must an ASPSP offer if it fails?",
  "SCA-RTS", "Art. 31-33", "An ASPSP may provide a dedicated interface for TPP access; it must offer a contingency mechanism (fallback to the customer interface) unless exempted by the competent authority, and the dedicated interface must meet availability and performance levels equal to the customer interface.",
  ["dedicated interface", "contingency"], "contingency", "obligation", "medium")

# ------------------------------------------------------------------ SEPA Regulation (EU) No 260/2012
q("What does the SEPA Regulation say about a payee requiring that the payer's account be located in a specific Member State?",
  "SEPA", "Art. 9", "A payee accepting credit transfers or direct debits may not specify the Member State in which the payer's account is located, provided the account is reachable (prohibition of IBAN discrimination).",
  ["Member State", "located", "shall not"], "Member State in which", "obligation")
q("Which identifier must be used to identify payment accounts under the SEPA Regulation?",
  "SEPA", "Art. 5", "The IBAN; BIC was required only until the end dates set out in the regulation.",
  ["IBAN"], "IBAN", "obligation")
q("What was the original end-date by which euro credit transfers and direct debits had to comply with SEPA requirements?",
  "SEPA", "Art. 6", "1 February 2014 (later extended to 1 August 2014 by Regulation 248/2014).",
  ["1 February 2014"], "1 February 2014", "deadline")
q("What does the SEPA Regulation provide about multilateral interchange fees per direct debit transaction?",
  "SEPA", "Art. 8", "No MIF per direct debit transaction may be applied for cross-border direct debits (and for national ones after 1 February 2017), except for R-transactions under strict conditions.",
  ["interchange fee", "R-transaction", "2017"], "R-transaction", "threshold", "medium")
q("Under the SEPA Regulation, what does 'reachability' require of a payer's payment service provider?",
  "SEPA", "Art. 3", "A PSP reachable for national credit transfers or direct debits must also be reachable for those initiated through any PSP located in the Union.",
  ["reachable"], "reachable", "obligation")

# ------------------------------------------------------------------ MiCA (Regulation (EU) 2023/1114)
q("How does MiCA define an 'asset-referenced token'?",
  "MICA", "Art. 3(1)(6)", "A crypto-asset that is not an e-money token and that purports to maintain a stable value by referencing another value or right, or a combination thereof, including one or more official currencies.",
  ["stable value", "referencing"], "asset-referenced token", "definition")
q("How does MiCA define an 'e-money token'?",
  "MICA", "Art. 3(1)(7)", "A crypto-asset that purports to maintain a stable value by referencing the value of one official currency.",
  ["one official currency"], "e-money token", "definition")
q("Who may issue e-money tokens under MiCA?",
  "MICA", "Art. 48", "Only persons authorised as a credit institution or as an electronic money institution, who must also publish a white paper.",
  ["credit institution", "electronic money institution"], "credit institution", "obligation")
q("What must an offeror of a crypto-asset (other than an ART or EMT) do before offering it to the public under MiCA?",
  "MICA", "Art. 4-6", "Be a legal person, draw up and notify a crypto-asset white paper with the required content and publish it; no authorisation is required for the offer itself.",
  ["white paper"], "white paper", "obligation")
q("Which MiCA article sets the authorisation requirement for crypto-asset service providers?",
  "MICA", "Art. 59", "Article 59: no person may provide crypto-asset services in the Union unless it is a legal person authorised as a CASP under Article 63, or a listed financial entity under Article 60.",
  ["59", "authoris"], "crypto-asset service provider", "obligation")
q("Under MiCA's transitional provisions, until when may crypto-asset service providers operating under national law before 30 December 2024 continue without a MiCA authorisation?",
  "MICA", "Art. 143(3)", "Until 1 July 2026 or until they are granted or refused an authorisation, whichever is sooner; Member States may shorten this period.",
  ["1 July 2026"], "1 July 2026", "deadline")
q("From what dates does MiCA apply?",
  "MICA", "Art. 149", "Titles III and IV (asset-referenced tokens and e-money tokens) apply from 30 June 2024; the regulation as a whole applies from 30 December 2024.",
  ["30 June 2024", "30 December 2024"], "30 December 2024", "deadline")
q("What does MiCA require regarding the safekeeping of clients' crypto-assets and funds by CASPs?",
  "MICA", "Art. 70", "CASPs holding clients' crypto-assets or funds must make adequate arrangements to safeguard ownership rights, must not use them for their own account, and must place clients' funds with a credit institution or central bank by the end of the next business day.",
  ["own account", "credit institution"], "safeguard", "obligation", "medium")
q("Does MiCA prohibit insider dealing in crypto-assets?",
  "MICA", "Art. 89", "Yes. Article 89 prohibits using inside information to acquire or dispose of crypto-assets, and recommending or inducing others to do so.",
  ["insider dealing", "inside information"], "inside information", "obligation")
q("Does MiCA prohibit market manipulation in crypto-asset markets?",
  "MICA", "Art. 91", "Yes. Article 91 prohibits engaging in or attempting to engage in market manipulation.",
  ["market manipulation"], "market manipulation", "obligation")
q("What are the components of the reserve of assets that an issuer of asset-referenced tokens must maintain under MiCA?",
  "MICA", "Art. 36", "A reserve of assets segregated from the issuer's own assets, composed and managed so as to cover the risks of the referenced assets and the liquidity risks of redemption rights.",
  ["reserve of assets", "segregated"], "reserve of assets", "obligation", "medium")
q("What redemption right do holders of asset-referenced tokens have under MiCA?",
  "MICA", "Art. 39", "A permanent right of redemption against the issuer at any time, at market value or by delivery of the referenced assets, free of fees other than those necessary.",
  ["redemption", "at any time"], "right of redemption", "obligation", "medium")
q("What are the main categories of crypto-asset services listed in MiCA?",
  "MICA", "Art. 3(1)(16)", "Custody and administration, operation of a trading platform, exchange for funds, exchange for other crypto-assets, execution of orders, placing, reception and transmission of orders, advice, portfolio management, and transfer services.",
  ["custody", "trading platform", "exchange", "execution", "advice", "portfolio management", "transfer"], "crypto-asset service", "definition")

# ------------------------------------------------------------------ DORA (Regulation (EU) 2022/2554)
q("From what date does DORA apply?",
  "DORA", "Art. 64", "17 January 2025.",
  ["17 January 2025"], "17 January 2025", "deadline")
q("What are the five main pillars of DORA's requirements for financial entities?",
  "DORA", "Chapters II-VI", "ICT risk management; ICT-related incident management, classification and reporting; digital operational resilience testing; managing ICT third-party risk; and information-sharing arrangements.",
  ["risk management", "incident", "testing", "third-party", "information"], "digital operational resilience testing", "scope")
q("How often must financial entities perform threat-led penetration testing under DORA?",
  "DORA", "Art. 26(1)", "At least every three years, for entities identified by competent authorities as significant.",
  ["three years", "3 years"], "threat-led penetration testing", "threshold")
q("What reports must a financial entity submit to its competent authority for a major ICT-related incident under DORA?",
  "DORA", "Art. 19(4)", "An initial notification, an intermediate report when the status changes or on request, and a final report when the root cause analysis is complete.",
  ["initial notification", "intermediate", "final report"], "intermediate report", "obligation")
q("Which body is responsible for the ICT risk management framework under DORA?",
  "DORA", "Art. 5", "The management body of the financial entity bears ultimate responsibility for managing ICT risk and must define, approve and oversee the framework.",
  ["management body"], "management body", "obligation")
q("What key contractual provisions does DORA require in contracts with ICT third-party service providers?",
  "DORA", "Art. 30", "Among others: description of functions and services, locations of data processing, data protection provisions, service levels, incident assistance, cooperation with authorities, termination rights and exit strategies, and audit and access rights.",
  ["termination", "service level", "audit", "location"], "contractual arrangements", "obligation")
q("Does DORA provide a simplified ICT risk management framework for smaller entities?",
  "DORA", "Art. 16", "Yes. Article 16 provides a simplified framework for small and non-interconnected investment firms, exempted payment and e-money institutions, and certain other small entities.",
  ["simplified", "small"], "simplified ICT risk management", "scope")
q("Under DORA, who designates ICT third-party service providers as critical, and based on what?",
  "DORA", "Art. 31", "The European Supervisory Authorities (through the Joint Committee, on recommendation of the Oversight Forum), based on criteria such as systemic impact, systemic importance of the entities relying on the provider, reliance on the provider, and substitutability.",
  ["critical", "ESA", "Supervisory Authorit", "substitut"], "critical ICT third-party", "obligation", "medium")
q("What does DORA require financial entities to do regarding backup policies?",
  "DORA", "Art. 12", "Develop and document backup policies and restoration and recovery procedures, with backup systems that can be activated without jeopardising security, and test them periodically.",
  ["backup", "recovery"], "backup policies", "obligation")
q("How must financial entities classify ICT-related incidents under DORA?",
  "DORA", "Art. 18", "Based on criteria such as number of clients affected, duration, geographical spread, data losses, criticality of services affected and economic impact.",
  ["clients", "duration", "geographical", "economic impact"], "geographical spread", "obligation")

# ------------------------------------------------------------------ EMD2 (Directive 2009/110/EC)
q("What is the initial capital requirement for an electronic money institution under EMD2?",
  "EMD2", "Art. 4", "Not less than EUR 350 000.",
  ["350 000", "350,000", "350000"], "350 000", "threshold")
q("What minimum own funds must an electronic money institution hold in respect of e-money issuance under EMD2?",
  "EMD2", "Art. 5(3)", "At least 2 % of the average outstanding electronic money.",
  ["2 %", "2%", "average outstanding"], "average outstanding electronic money", "threshold")
q("At what value and when must an e-money issuer redeem electronic money under EMD2?",
  "EMD2", "Art. 11", "At par value, at any time upon request of the holder.",
  ["par value", "at any time"], "par value", "obligation")
q("May an electronic money institution pay interest on electronic money under EMD2?",
  "EMD2", "Art. 12", "No. Granting interest or any other benefit related to the length of time e-money is held is prohibited.",
  ["interest", "prohibit"], "interest", "obligation")
q("What is the average outstanding e-money ceiling for the optional small-institution exemption under EMD2?",
  "EMD2", "Art. 9", "Average outstanding electronic money not exceeding EUR 5 million (Member States may set a lower limit).",
  ["5 million", "5 000 000"], "5 million", "threshold")
q("How does EMD2 define electronic money?",
  "EMD2", "Art. 2(2)", "Electronically (including magnetically) stored monetary value, represented by a claim on the issuer, issued on receipt of funds for making payment transactions, and accepted by persons other than the issuer.",
  ["claim on the issuer", "stored", "accepted"], "monetary value", "definition")
q("What safeguarding options does EMD2 give electronic money institutions for funds received in exchange for e-money?",
  "EMD2", "Art. 7", "They must safeguard funds in accordance with the PSD safeguarding rules: segregation and deposit or investment in secure, liquid low-risk assets, or coverage by an insurance policy or comparable guarantee.",
  ["safeguard", "insurance", "segregat"], "safeguard", "obligation", "medium")

# ------------------------------------------------------------------ AMLD5 (Directive (EU) 2018/843) and AMLD6 (Directive (EU) 2018/1673)
q("Which crypto-related businesses did AMLD5 bring within the scope of the EU anti-money-laundering framework?",
  "AMLD5", "Art. 1(1)(c) amending Art. 2(1)(3) of 2015/849", "Providers engaged in exchange services between virtual currencies and fiat currencies, and custodian wallet providers.",
  ["virtual currenc", "custodian wallet"], "custodian wallet", "scope")
q("How does AMLD5 define 'virtual currencies'?",
  "AMLD5", "Art. 1(2)(d) adding Art. 3(18) of 2015/849", "A digital representation of value that is not issued or guaranteed by a central bank or public authority, is not necessarily attached to a legally established currency, does not possess legal status of currency or money, but is accepted as a means of exchange and can be transferred, stored and traded electronically.",
  ["digital representation of value", "central bank"], "digital representation of value", "definition")
q("What change did AMLD5 make to public access to beneficial ownership information of companies?",
  "AMLD5", "Art. 1(15) amending Art. 30(5) of 2015/849", "Beneficial ownership information on corporate and other legal entities must be accessible to any member of the general public.",
  ["general public", "beneficial owner"], "any member of the general public", "obligation")
q("What is the transposition deadline set by AMLD5?",
  "AMLD5", "Art. 4", "10 January 2020.",
  ["10 January 2020"], "10 January 2020", "deadline")
q("To what amount did AMLD5 lower the threshold below which anonymous prepaid instruments may be exempted from customer due diligence?",
  "AMLD5", "Art. 1(7) amending Art. 12 of 2015/849", "From EUR 250 to EUR 150 (and EUR 50 for remote payment transactions).",
  ["150", "50"], "EUR 150", "threshold")
q("What enhanced due diligence measures does AMLD5 require for business relationships involving high-risk third countries?",
  "AMLD5", "Art. 1(11) adding Art. 18a of 2015/849", "Obtaining additional information on the customer and beneficial owners, the intended nature of the relationship, source of funds and wealth, reasons for transactions, senior management approval, and enhanced monitoring.",
  ["source of funds", "senior management", "high-risk third countr"], "high-risk third countries", "obligation", "medium")
q("What minimum maximum term of imprisonment must Member States provide for money laundering offences under AMLD6?",
  "AMLD6", "Art. 5(2)", "Punishable by a maximum term of imprisonment of at least four years.",
  ["four years", "4 years"], "four years", "threshold")
q("Does AMLD6 require Member States to criminalise self-laundering?",
  "AMLD6", "Art. 3(5)", "Yes, for conversion/transfer and concealment/disguise of property derived from one's own criminal activity.",
  ["self-laundering", "own criminal activity"], "own criminal activity", "obligation", "medium")
q("What conduct constitutes a money laundering offence under AMLD6?",
  "AMLD6", "Art. 3(1)", "Conversion or transfer of property derived from criminal activity to conceal its origin; concealment or disguise of its nature, source or ownership; and acquisition, possession or use of such property knowing it derives from criminal activity.",
  ["conversion", "conceal", "acquisition"], "conversion or transfer", "definition")
q("Does AMLD6 provide for liability of legal persons for money laundering?",
  "AMLD6", "Art. 7-8", "Yes. Legal persons can be held liable for offences committed for their benefit by persons in a leading position, with sanctions including fines and exclusion from public benefits.",
  ["legal person", "liable"], "legal persons", "obligation")
q("What is the transposition deadline set by AMLD6?",
  "AMLD6", "Art. 13", "3 December 2020.",
  ["3 December 2020"], "3 December 2020", "deadline")
q("Does AMLD6 list tax crimes among the predicate offences for money laundering?",
  "AMLD6", "Art. 2(1)(q)", "Yes. Tax crimes relating to direct and indirect taxes are among the listed categories of criminal activity.",
  ["tax crime"], "tax crimes", "scope")

# ------------------------------------------------------------------ GDPR (Regulation (EU) 2016/679)
q("Within what period must a controller notify a personal data breach to the supervisory authority under the GDPR?",
  "GDPR", "Art. 33(1)", "Without undue delay and, where feasible, not later than 72 hours after having become aware of it, unless unlikely to result in a risk.",
  ["72 hours"], "72 hours", "deadline")
q("What is the maximum administrative fine under the GDPR for infringing the basic principles of processing?",
  "GDPR", "Art. 83(5)", "Up to EUR 20 million or 4 % of total worldwide annual turnover of the preceding financial year, whichever is higher.",
  ["20 000 000", "20 million", "4 %", "4%"], "4 % of the total worldwide annual turnover", "threshold")
q("What are the lawful bases for processing personal data under the GDPR?",
  "GDPR", "Art. 6(1)", "Consent, performance of a contract, legal obligation, vital interests, public task/official authority, and legitimate interests.",
  ["consent", "contract", "legal obligation", "vital interests", "legitimate interests"], "legitimate interests", "definition")
q("What is the right to data portability under the GDPR?",
  "GDPR", "Art. 20", "The right to receive personal data provided to a controller in a structured, commonly used and machine-readable format and to transmit it to another controller, where processing is based on consent or contract and carried out by automated means.",
  ["machine-readable", "another controller"], "machine-readable", "definition")
q("When is a data protection impact assessment required under the GDPR?",
  "GDPR", "Art. 35", "Where processing, in particular using new technologies, is likely to result in a high risk to the rights and freedoms of natural persons, e.g. systematic and extensive profiling, large-scale processing of special categories, or systematic monitoring of public areas.",
  ["high risk", "profiling", "large scale"], "high risk", "obligation")
q("When must a controller or processor designate a data protection officer under the GDPR?",
  "GDPR", "Art. 37(1)", "When processing is carried out by a public authority, when core activities involve regular and systematic monitoring of data subjects on a large scale, or when core activities consist of large-scale processing of special categories or criminal conviction data.",
  ["public authority", "large scale", "systematic monitoring"], "data protection officer", "obligation")
q("What rights does a data subject have regarding decisions based solely on automated processing under the GDPR?",
  "GDPR", "Art. 22", "The right not to be subject to a decision based solely on automated processing, including profiling, producing legal or similarly significant effects, with exceptions for contract necessity, legal authorisation or explicit consent, and safeguards including human intervention.",
  ["solely on automated", "profiling", "human intervention"], "solely on automated processing", "definition")
q("Within what time must a controller respond to a data subject access request under the GDPR?",
  "GDPR", "Art. 12(3)", "Without undue delay and in any event within one month of receipt, extendable by two further months where necessary.",
  ["one month", "two further months"], "one month", "deadline")
q("What conditions must consent meet to be valid under the GDPR?",
  "GDPR", "Art. 4(11) and Art. 7", "Freely given, specific, informed and unambiguous; demonstrable by the controller; as easy to withdraw as to give.",
  ["freely given", "specific", "informed", "unambiguous"], "freely given", "definition")
q("From what date does the GDPR apply?",
  "GDPR", "Art. 99(2)", "25 May 2018.",
  ["25 May 2018"], "25 May 2018", "deadline")
q("What does the GDPR require regarding 'data protection by design and by default'?",
  "GDPR", "Art. 25", "Controllers must implement appropriate technical and organisational measures (e.g. pseudonymisation, data minimisation) at the time of determining the means and at the time of processing, and by default process only data necessary for each specific purpose.",
  ["by design", "by default", "pseudonymisation"], "by design", "obligation")
q("What categories of personal data are 'special categories' under the GDPR?",
  "GDPR", "Art. 9(1)", "Racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data for unique identification, health data, and data concerning sex life or sexual orientation.",
  ["ethnic origin", "political opinions", "genetic", "biometric", "health"], "biometric data", "definition")

# ------------------------------------------------------------------ IFR (Regulation (EU) 2015/751)
q("What is the interchange fee cap for consumer debit card transactions under the Interchange Fee Regulation?",
  "IFR", "Art. 3(1)", "0.2 % of the value of the transaction.",
  ["0.2 %", "0.2%", "0,2"], "0,2 %", "threshold")
q("What is the interchange fee cap for consumer credit card transactions under the Interchange Fee Regulation?",
  "IFR", "Art. 4", "0.3 % of the value of the transaction.",
  ["0.3 %", "0.3%", "0,3"], "0,3 %", "threshold")
q("Does the Interchange Fee Regulation require the separation of payment card schemes and processing entities?",
  "IFR", "Art. 7", "Yes. Schemes and processing entities must be independent in terms of accounting, organisation and decision-making processes.",
  ["independent", "accounting", "organisation"], "processing entities", "obligation")
q("What does the Interchange Fee Regulation say about 'Honour All Cards' rules?",
  "IFR", "Art. 10", "Schemes and providers may not oblige payees accepting one card-based instrument to also accept other instruments issued within the same scheme (e.g. accepting debit does not oblige accepting credit), but all cards of the same brand and category must be treated equally.",
  ["Honour All Cards", "same brand"], "Honour All Cards", "obligation")
q("From what date did the interchange fee caps in the Interchange Fee Regulation apply?",
  "IFR", "Art. 18", "9 December 2015 (six months after entry into force).",
  ["9 December 2015"], "9 December 2015", "deadline")
q("What does the Interchange Fee Regulation require regarding 'unblending' of merchant service charges?",
  "IFR", "Art. 9", "Acquirers must offer and charge payees merchant service charges individually specified for different categories and brands of cards with different interchange fee levels, unless the payee requests blended charges in writing.",
  ["individually", "categories", "brands"], "individually specified", "obligation")
q("Does the Interchange Fee Regulation allow co-badging of two or more payment brands on one card?",
  "IFR", "Art. 8", "Yes. Scheme rules may not hinder co-badging, and the payer must be able to choose which brand or application to use at the point of sale.",
  ["co-badg", "choose"], "co-badging", "obligation")

# ------------------------------------------------------------------ Cross-regulation questions
q("Which EU regulation caps interchange fees, and which directive prohibits surcharging for the cards covered by those caps?",
  "IFR", "IFR Art. 3-4; PSD2 Art. 62(4)", "The Interchange Fee Regulation (2015/751) caps the fees; PSD2 (2015/2366) Article 62(4) prohibits surcharging for those instruments.",
  ["Interchange Fee", "62"], "Interchange Fee", "cross")
q("A fintech wants to offer crypto-to-fiat exchange and custodian wallets in the EU. Which AML directive brought these activities into scope, and which regulation now governs their authorisation?",
  "AMLD5", "AMLD5 Art. 1(1)(c); MiCA Art. 59", "AMLD5 (2018/843) brought virtual currency exchange and custodian wallet providers under AML obligations; MiCA (2023/1114) now requires CASP authorisation under Article 59.",
  ["AMLD5", "MiCA", "59"], "custodian wallet", "cross")
q("A payment institution suffers a major ICT incident. Which two EU instruments require it to report the incident, and within what framework?",
  "DORA", "PSD2 Art. 96; DORA Art. 19", "PSD2 Article 96 (major operational or security incidents, without undue delay to the home competent authority) and DORA Article 19 (initial, intermediate and final reports for major ICT-related incidents).",
  ["96", "19", "DORA", "PSD2"], "major ICT-related incident", "cross")
q("Which directive provides the safeguarding regime that electronic money institutions must follow under EMD2?",
  "EMD2", "EMD2 Art. 7 (referring to the Payment Services Directive)", "The Payment Services Directive's safeguarding rules (PSD, now PSD2 Article 10): segregation and deposit/investment of funds or insurance coverage.",
  ["Payment Services Directive", "safeguard"], "safeguard", "cross", "medium")

# ------------------------------------------------------------------ Unanswerable (not in corpus / fabricated / outside law text / false premise)
u("What changes does PSD3 make to the liability rules for authorised push payment fraud?", "not_in_corpus")
u("Under the Instant Payments Regulation (EU) 2024/886, how quickly must an instant credit transfer be executed?", "not_in_corpus")
u("Which obligations does the EU AI Act impose on credit-scoring systems used by banks?", "not_in_corpus")
u("What is the 'travel rule' information that crypto-asset service providers must transmit under Regulation (EU) 2023/1113?", "not_in_corpus")
u("What does the UK Payment Services Regulations 2017 say about SCA exemptions for contactless payments?", "not_in_corpus")
u("Under US Regulation E, how long does a consumer have to report an unauthorised electronic fund transfer?", "not_in_corpus")
u("What does Article 160 of PSD2 require from payment institutions?", "fabricated",
  "PSD2 has no Article 160 (it ends at Article 117); the assistant should say the article does not exist.")
u("What is the SCA exemption for payments initiated by a 'certified merchant' under Article 19a of the SCA RTS?", "fabricated",
  "There is no 'certified merchant' exemption in the SCA RTS; the assistant should say it cannot find such a provision.")
u("How large was the administrative fine imposed on N26 by BaFin in 2021 for AML failures?", "outside_law_text")
u("What was Klarna's total payment volume in 2024?", "outside_law_text")
u("Which EU Member State was the first to transpose AMLD6?", "outside_law_text")
u("What is the current EUR/USD exchange rate used by the ECB for MiCA reserve valuation today?", "outside_law_text")
u("Under PSD3, what is the new per-transaction threshold for the contactless SCA exemption?", "false_premise",
  "PSD3 is not in the corpus and contactless thresholds are set in the SCA RTS; the assistant should not invent a PSD3 figure.")
u("What is the maximum fine under DORA, expressed as a percentage of global turnover?", "false_premise",
  "DORA leaves administrative penalties to Member States (Article 50) and sets no turnover-based maximum; the assistant should not invent a percentage.")
u("Which article of the GDPR sets the 48-hour breach notification deadline?", "false_premise",
  "The GDPR deadline is 72 hours (Article 33), not 48; the assistant should correct the premise rather than confirm it.")
u("What minimum capital does MiCA require for a utility token issuer?", "false_premise",
  "MiCA sets no capital requirement for offerors of utility tokens (only a white paper); the assistant should say so.")
u("What interest rate must e-money institutions pay to holders under EMD2?", "false_premise",
  "EMD2 Article 12 prohibits paying interest on e-money; the assistant should correct the premise.")
u("What does the eIDAS Regulation require for qualified electronic signatures on payment mandates?", "not_in_corpus")
u("What does the Consumer Credit Directive say about BNPL affordability checks?", "not_in_corpus")
u("What is the Basel III leverage ratio requirement for payment institutions?", "not_in_corpus")


def main():
    out = Path("data")
    out.mkdir(exist_ok=True)
    with (out / "gold_questions.jsonl").open("w") as f:
        for i, item in enumerate(Q, 1):
            f.write(json.dumps({"id": f"Q{i:03d}", **item}) + "\n")
    (out / "regulation_aliases.json").write_text(json.dumps(REG_ALIASES, indent=2))
    n_ans = sum(x["answerable"] for x in Q)
    by_reg = {}
    for x in Q:
        by_reg[x["regulation"]] = by_reg.get(x["regulation"], 0) + 1
    print(f"{len(Q)} questions: {n_ans} answerable, {len(Q) - n_ans} unanswerable")
    print("by regulation:", by_reg)
    print("medium-confidence references to verify:", [f"Q{i+1:03d}" for i, x in enumerate(Q) if x["confidence"] == "medium"])


if __name__ == "__main__":
    main()
