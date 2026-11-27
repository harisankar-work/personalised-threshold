# Final faculty feedback resolution

Evidence source: the supplied 49C-V2 Second Review Feedback, marked 24.9/30. The candidate is a local change set based on 5bf70a6. Public release and deployment require approval after review.

| Review issue | Change and evidence | Status and remaining limit |
|---|---|---|
| Direct response outcomes | Audit of 287 joined ad-specific ratings, 276 included; separate ≥5 flags. See evaluation report and aggregate JSON. | Partially resolved. Collection was reported by the owner; questionnaire and assignment records have not been independently verified. |
| High-intrusion recall and calibration | Family-disjoint classifiers, confusion matrices, Brier scores and reliability bins. Forest caught 101/103 with 60 false positives. | Partially resolved. Internal grouped validation only, with worse forest Brier score than level risk. |
| Same-questionnaire overlap | Candidate predictors use ad attributes only. Consumer timing was undocumented. | Resolved and verified for these candidate inputs. Individual consumer features remain unvalidated. |
| Person- and creative-disjoint evaluation | Complementary folds and leave-one-family-out sensitivity, with explicit disjointness assertions. | Resolved and verified internally. External evaluation remains unresolved. |
| Five-level individual thresholds | One rating per person and two families nested per level; no counterfactual observations. | Blocked by available evidence. |
| Financial and threshold demonstrations | Observed research ratings are separate from the fictional simulator and existing scenario arithmetic. | Partially resolved. No conversion or financial uplift outcomes. |
| Abstention | Research-only candidates, zero operational coverage, no active empirical prediction. | Partially resolved. Selective prediction error cannot be established at zero coverage. |
| Reproducibility and access | Versioned code, checksums, splits, aggregate metrics, feature contract, and local data-access instructions. | Partially resolved. Public release still needs approval. Raw files remain private. |
| Release alignment | Final candidate and publication gate documented. | Unresolved until an approved exact commit is pushed, deployed and verified. |
