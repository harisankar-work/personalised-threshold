# Kiwadoi empirical model optimization

Release candidate: primary287_population_v2, local working tree based on 5bf70a6. Prior synthetic and primary287_v1 artifacts remain available. No publication, deployment or manuscript work in this change.

| Measure | Synthetic demonstration | Previous empirical forest | v2 choice | Empirical level baseline |
|---|---:|---:|---:|---:|
| Intrusion MAE / RMSE | Different target | 0.9055 / 1.1307 | 0.8768 / 1.1625 | 0.9070 / 1.1302 |
| Discomfort MAE / RMSE | 0.5123 / 0.6665 | 0.8391 / 1.0541 | 0.8225 / 1.1075 | 0.8363 / 1.0526 |
| Relevance MAE / RMSE | 0.6974 / 0.8698 | 0.9159 / 1.1205 | 0.9058 / 1.2008 | 0.9168 / 1.1209 |
| High intrusion recall / precision at 0.5 | Unavailable | 0.981 / 0.627 | 0.709 / 0.670 | 0.709 / 0.670 |
| False positives / false negatives at 0.5 | Unavailable | 60 / 2 | 36 / 30 | 36 / 30 |
| High intrusion Brier | Unavailable | 0.1312 | 0.1262 | 0.1262 |
| Validation | Fictional consumer split | Two complementary survey family folds | Same grouped internal folds and leave-one-family-out sensitivity | Same empirical folds |
| Coverage | Fictional scenarios | Research only | Five population estimates in the surveyed domain; zero individualized coverage | Population benchmark |

Rating estimates use fitted per-level medians. Compared with the previous empirical forest, intrusion MAE improved by 0.0287, discomfort by 0.0167 and relevance by 0.0101. Compared with level means the gains were 0.0301, 0.0138 and 0.0110. Conditional whole-family bootstrap gain intervals were respectively [-0.0076, 0.0672], [-0.0248, 0.0513] and [-0.0348, 0.0591]. The medians had worse RMSE, so this is a small MAE trade-off, with no established advantage on external data.

Risk estimates use observed high-rating shares by level. Their better Brier score than the forest does not establish a separate calibration gain. At 0.5 there were 24 fewer false positives and 28 more false negatives. The training-only recall policy on shrunk rates matched the forest's 101 true positives and 60 false positives; it did not improve the equal-recall trade-off. Logistic C=0.2 with level indicators and two creative cues, five pseudo-observation shrinkage, and grouped cross-fitted sigmoid calibration did not beat the raw level-risk Brier score. With only one peer family per level in each outer training partition, inner leave-family-out calibration often falls back to a pooled risk, making the learned mapping unstable. Held-out reliability bins, threshold policies and high-discomfort results are in the aggregate file. The app displays percentages and uses a user-entered risk limit rather than deploying a binary 0.5 classifier.

Prior six ad-attribute fields were constant within level. Privacy and pressure cues had only one to three distinct pairs per level. Fixed standardized Ridge alpha 20 using one-hot level and both cues underperformed level means on all three targets. Regularized ordinal cumulative proportions used five pooled pseudo-observations per cut point; they offered no consistent advantage. No verified pre-exposure questionnaire timings were available, so consumer covariates, composites and interactions were excluded. Added complexity showed no stable advantage. Ten independent families limit any estimate of overfitting. The reused sample is an internal comparison, with no fresh test set. Personalization, family and creative effects remain confounded.

The default browser POST selects empirical mode and reads the bundled population model. It returns medians, observed high-intrusion share, sample sizes and family ranges. The recommendation uses the worst observed family median discomfort and risk, and the lowest family median relevance. It also requires explicit survey-scenario acknowledgement, known costs, budget and confirmed targeting permissions including location where applicable. Missing confirmation or failure to satisfy the limits yields abstention. Ranges describe two observed families and do not quantify uncertainty for a new creative. The fictional workflow requires explicit selection. The evidence status of a real individual threshold remains insufficient_evidence.

Reproduce from the root with Python 3.14.6, pandas 3.0.3, NumPy 2.4.6 and scikit-learn 1.9.0:

    python -m primary287.optimize PATH_TO_AUTHORIZED_CSV_FOLDER

The command reuses the validated v1 joins, exclusions and labels. It writes results/primary287_population_v2.json and results/primary287_optimization_v2.json. The latter records checksums, fixed configurations documented in code, folds, per-family and per-level errors, and grouped sensitivity. Keep the three CSVs outside the repository. Regression verification: 93 tests passed. Chrome smoke verified the default estimates, initial abstention, a constraint-driven exploratory choice, optional synthetic mode, research panel and text-analysis API. The existing OCR regression tests are part of the suite. Production remains on the previously approved release.
