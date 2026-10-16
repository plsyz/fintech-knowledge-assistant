# FinTech Knowledge Assistant evaluation summary

Judged records: 375 across conditions ['vector', 'graph-rag', 'no-retrieval']

## 1. Answerable questions

| condition | n | accuracy | key-fact recall | regulation cited | article correct (of cited) | cited any article | unsupported claims / answer | hallucinated specifics | abstained (wrongly) |
|---|---|---|---|---|---|---|---|---|---|
| vector | 105 | 0.762 | 0.808 | 1.000 | 0.882 | 0.886 | 0.16 | 0.095 | 0.076 |
| graph-rag | 105 | 0.667 | 0.695 | 1.000 | 0.792 | 0.686 | 0.25 | 0.133 | 0.114 |
| no-retrieval | 105 | 0.743 | 0.835 | 1.000 | 0.783 | 0.876 | 2.20 | 0.295 | 0.048 |

## 2. Unanswerable questions (abstention)

| condition | n | correct abstention | hallucinated an answer | false-premise corrected |
|---|---|---|---|---|
| vector | 20 | 0.950 | 0.050 | 0.800 |
| graph-rag | 20 | 0.800 | 0.200 | 0.800 |
| no-retrieval | 20 | 0.950 | 0.050 | 0.800 |

### By reason

| condition | reason | n | correct abstention |
|---|---|---|---|
| vector | fabricated | 2 | 1.000 |
| vector | false_premise | 5 | 0.800 |
| vector | not_in_corpus | 9 | 1.000 |
| vector | outside_law_text | 4 | 1.000 |
| graph-rag | fabricated | 2 | 0.500 |
| graph-rag | false_premise | 5 | 0.800 |
| graph-rag | not_in_corpus | 9 | 0.778 |
| graph-rag | outside_law_text | 4 | 1.000 |
| no-retrieval | fabricated | 2 | 1.000 |
| no-retrieval | false_premise | 5 | 0.800 |
| no-retrieval | not_in_corpus | 9 | 1.000 |
| no-retrieval | outside_law_text | 4 | 1.000 |

## 3. Contamination check

A question the model answers correctly closed-book (no-retrieval) does not measure retrieval.
Retrieval conditions are therefore re-scored on the non-contaminated subset.

Closed-book solvable (contaminated): 78 of 105 answerable questions (0.743).

| condition | accuracy all | accuracy contaminated | accuracy non-contaminated (retrieval-dependent) |
|---|---|---|---|
| vector | 0.762 | 0.936 | 0.259 |
| graph-rag | 0.667 | 0.795 | 0.296 |
| no-retrieval | 0.743 | 1.000 | 0.000 |

### Closed-book solvable share by regulation

| regulation | n | closed-book accuracy |
|---|---|---|
| AMLD5 | 7 | 0.714 |
| AMLD6 | 6 | 0.667 |
| DORA | 11 | 0.636 |
| EMD2 | 8 | 0.750 |
| GDPR | 12 | 0.917 |
| IFR | 8 | 0.625 |
| MICA | 13 | 0.846 |
| PSD2 | 22 | 0.773 |
| SCA-RTS | 13 | 0.846 |
| SEPA | 5 | 0.200 |

## 4. Retrieval recall (gold passage hint found in similarity search)

n = 105; hit@5 = 0.705; hit@15 = 0.857

| regulation | n | hit@5 | hit@15 |
|---|---|---|---|
| AMLD5 | 7 | 0.571 | 0.857 |
| AMLD6 | 6 | 0.500 | 0.833 |
| DORA | 11 | 0.727 | 0.909 |
| EMD2 | 8 | 0.750 | 0.875 |
| GDPR | 12 | 0.833 | 0.917 |
| IFR | 8 | 0.500 | 0.625 |
| MICA | 13 | 0.923 | 1.000 |
| PSD2 | 22 | 0.727 | 0.818 |
| SCA-RTS | 13 | 0.692 | 0.846 |
| SEPA | 5 | 0.400 | 0.800 |

### Accuracy split by retrieval hit (vector uses top-15, graph-rag top-5)

| condition | hit | n | accuracy |
|---|---|---|---|
| vector | False | 15 | 0.533 |
| vector | True | 90 | 0.800 |
| graph-rag | False | 31 | 0.323 |
| graph-rag | True | 74 | 0.811 |

## 5. Accuracy by regulation (answerable)

| regulation   |   graph-rag |   no-retrieval |   vector |
|:-------------|------------:|---------------:|---------:|
| AMLD5        |       0.714 |          0.714 |    0.857 |
| AMLD6        |       0.833 |          0.667 |    0.667 |
| DORA         |       0.545 |          0.636 |    0.727 |
| EMD2         |       0.5   |          0.75  |    0.75  |
| GDPR         |       0.917 |          0.917 |    0.833 |
| IFR          |       0.5   |          0.625 |    0.5   |
| MICA         |       0.615 |          0.846 |    0.846 |
| PSD2         |       0.818 |          0.773 |    0.818 |
| SCA-RTS      |       0.615 |          0.846 |    0.769 |
| SEPA         |       0.2   |          0.2   |    0.6   |

## 6. Accuracy by question kind (answerable)

| kind       |   graph-rag |   no-retrieval |   vector |
|:-----------|------------:|---------------:|---------:|
| cross      |       0.6   |          0.4   |    0.4   |
| deadline   |       0.706 |          0.588 |    0.588 |
| definition |       0.714 |          0.857 |    0.786 |
| liability  |       1     |          1     |    1     |
| obligation |       0.7   |          0.775 |    0.825 |
| scope      |       0.5   |          0.875 |    1     |
| threshold  |       0.556 |          0.722 |    0.722 |

## 7. Accuracy by gold-reference confidence (answerable)

Low accuracy on 'medium' items may indicate a gold-set error rather than a system error; verify those on EUR-Lex.

| confidence   |   graph-rag |   no-retrieval |   vector |
|:-------------|------------:|---------------:|---------:|
| high         |       0.663 |          0.739 |    0.772 |
| medium       |       0.692 |          0.769 |    0.692 |
