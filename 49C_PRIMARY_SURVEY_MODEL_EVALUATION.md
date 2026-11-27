# 49-C primary survey model evaluation

The supplied files were described by the project owner as primary survey data. The three CSVs establish their internal structure, but recruitment, collection dates, consent wording, assignment, questionnaire timing and the presented creatives could not be independently verified. All records are in Main. Each survey version maps to one creative family, and every family to one level. Neither provenance nor randomized assignment can be inferred from that structure.

## Audit and outcomes

All three files contain 287 rows, zero missing cells and zero duplicate rows. Validated one-to-one joins retain all 287 exposures. Each respondent and ad record appears once. All consent flags are 1, no records are marked pilot, and 11 failed attention checks, leaving 276. Completion time spans 97–687 seconds (median 409); no time cutoff was imposed without documentation. All ads have disclosure_present=0. Each of ten families has one filename, one category and 28–29 distinct texts before exclusions. The labels are derived at score ≥5; the original columns are preserved.

| Label | All disagreements | Included disagreements | Included high / total |
|---|---:|---:|---:|
| high_intrusion | 43 | 41 | 103 / 276 |
| high_discomfort | 57 | 53 | 91 / 276 |

| Level | N | Intrusion | Discomfort | Relevance | High intrusion | High discomfort |
|---|---:|---:|---:|---:|---:|---:|
| L0 | 57 | 2.12 | 2.12 | 3.47 | 1 | 2 |
| L1 | 58 | 2.79 | 2.64 | 4.67 | 1 | 2 |
| L2 | 52 | 4.27 | 4.06 | 4.87 | 25 | 16 |
| L3 | 54 | 4.65 | 4.06 | 5.28 | 27 | 23 |
| L4 | 55 | 5.91 | 5.53 | 4.62 | 49 | 48 |

Privacy concern, personalization preference and willingness distributions and demographic counts are in the aggregate JSON. Intrusion and acceptability had pooled Spearman rho −0.748 (family range −0.826 to −0.326). Privacy concern and intrusion had rho 0.244 (family range 0.078–0.633), which does not identify moderation. Sharing willingness and acceptability had rho 0.091 (family range −0.209 to 0.357). These are descriptive same-survey associations. Other ratings and standard deviations are saved by level and family.

## Grouped validation

The primary split has two complementary folds, each holding out one family per level. Both respondent and family overlap are checked. The sensitivity analysis holds out each family in turn and repeats the two-fold evaluation with attention failures included. The dataset supplies no separate test pool. The six pre-exposure ad attributes are the four source flags, source count and disclosure. Consumer and combined models were excluded because measurement timing is undocumented. Identifiers, categories tied to creative family, filenames, survey metadata and post-exposure outcomes are excluded. Fixed ridge alpha 10 and logistic C=1 use training-only standardization. Forests use 100 trees, depth 3 and 12 minimum leaf records. Classification forests use class weighting. No held-out tuning was performed.

| Continuous target | Global MAE | Level MAE | Ridge MAE | Forest MAE | Forest misses / high |
|---|---:|---:|---:|---:|---:|
| intrusiveness_score | 1.4685 | 0.9070 | 0.9455 | 0.9055 | 54/103 |
| discomfort_score | 1.3608 | 0.8363 | 0.8621 | 0.8391 | 43/91 |
| relevance_score | 1.0472 | 0.9168 | 1.0021 | 0.9159 | 89/145 |

| Binary target | Model | Recall | Specificity | Precision | Brier | AUROC | TN/FP/FN/TP |
|---|---|---:|---:|---:|---:|---:|---|
| high_intrusion_ge5 | mean | 0.000 | 1.000 | 0.000 | 0.235 | 0.483 | 173/0/103/0 |
| high_intrusion_ge5 | level_mean | 0.709 | 0.792 | 0.670 | 0.126 | 0.869 | 137/36/30/73 |
| high_intrusion_ge5 | logistic | 0.583 | 0.879 | 0.741 | 0.125 | 0.873 | 152/21/43/60 |
| high_intrusion_ge5 | forest | 0.981 | 0.653 | 0.627 | 0.131 | 0.869 | 113/60/2/101 |
| high_discomfort_ge5 | mean | 0.000 | 1.000 | 0.000 | 0.221 | 0.499 | 185/0/91/0 |
| high_discomfort_ge5 | level_mean | 0.626 | 0.870 | 0.704 | 0.133 | 0.850 | 161/24/34/57 |
| high_discomfort_ge5 | logistic | 0.626 | 0.870 | 0.704 | 0.133 | 0.852 | 161/24/34/57 |
| high_discomfort_ge5 | forest | 0.835 | 0.692 | 0.571 | 0.144 | 0.850 | 128/57/15/76 |

The forest marginally reduces intrusion MAE against the level mean and misses the same 54 of 103 high cases at the continuous rating boundary. Its high-intrusion classifier catches 101 of 103 but yields 60 false positives and a worse Brier score than the level-risk baseline. In one occupied probability bin, mean predicted risk was 0.666 and observed frequency was 0.423 (26 cases). Disclosure was constant and ad attributes varied only by level, limiting predictive resolution. Family-resampled gain intervals condition on the fitted out-of-fold predictions and have just two families per level. No external prediction intervals or safety guarantees are supported. Thresholds 0.35, 0.5 and 0.65 are sensitivity diagnostics, not selected operating points.

## Release decision

Research only. The production decision abstains for every empirical prediction request because exposure timing, generalization and probability reliability are insufficiently established. Operational coverage is 0%; selective error is undefined. Offline validation reports all cases and does not simulate credibility by dropping difficult rows. A single exposure per respondent and family nested within level do not identify individual counterfactuals or a causal effect. Existing permission, budget and creative-screening decisions remain independent. The candidate adds only aggregated observed means to Research Evidence. No model binary or participant rows are published.

Reproduce from the repository root with python primary287/evaluate.py PATH_TO_AUTHORIZED_CSV_FOLDER. Check hashes, versions, fold membership, all scores, reliability bins and sensitivity diagnostics in results/primary287_v1.json.
