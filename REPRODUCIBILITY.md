# Reproducibility during development

This guide covers the Kiwadoi application, the separate secondary-data analyses, and the fictional consumer simulation. The app baseline for this work was `a2fe394f6011fea12b74295af8316cb15fda4790` on `main`. The reviewed source snapshot and the hosted deployment have separate provenance. A final deployed commit, release and reviewer access check are pending.

The five-page manuscript assessed in the **49C-V2 second review** was unavailable. This is a provisional mapping from the earlier [6 November V2 draft](https://github.com/harisankar-work/personalised-threshold/blob/19c04024c16f0e92debc5b7eb7fa88b95b0d6486/49C_V2_DRAFT.md), the second-review feedback, the [location-study report](CORE_DATASET_RESOLUTION_AND_MODEL_RESULTS.md), the [model validation report](PHASE5_MODEL_VALIDATION_REPORT.md), the [application completion report](49C_FINAL_PROJECT_REPORT.md) and saved research results. Add the submitted manuscript's exact table, figure and claim numbers when that file is available.

## Components

| Component | Entry points | Evidence |
| --- | --- | --- |
| Local and hosted app | `marketer_app.py`, `web/`, `api/`, `vercel.json` | The local app and existing tests can run from a clean working tree. Research screens read saved aggregates. |
| Research analyses | [research/analyses](research/analyses) | Original scripts recovered from development commit `4431ea741422470ba77081e9056df41bde703dd3`. The interaction audit has new input/output arguments and defaults to aggregate-only export. Its matching, modeling and metrics are unchanged. |
| Synthetic simulation | [synthetic_demo](synthetic_demo) | Generator, data and fitted model. The app serves fictional predictions and descriptive fictional segment averages. |
| Research output evidence | [results/](results) and [research/evidence](research/evidence/README.md) | Versioned historical summaries and a dated replay report. Outputs from the location and surveillance evaluations are historical. |

## Tested environment and setup

The commands below use Bash from the repository root. The November replay used Linux x86-64, Python **3.12.14**, Node.js **24.22.3** and npm **11.19.1**. The pinned environment includes NumPy **2.3.5**, pandas **3.0.1**, Pillow **12.3.0**, openpyxl **3.1.5**, pyreadstat **1.3.7**, scikit-learn **1.9.0** and their tested dependencies. This is the replay environment. Historical analyses recorded different host environments in some reports.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r research/requirements-replay.txt
python -m pip check
npm ci
```

Node and npm are used for the app and OCR. Python-only research replay needs no JavaScript setup. On Windows PowerShell, the environment activation path is `.\.venv\Scripts\Activate.ps1`. The replay instructions were executed in Bash.

### Local application

```bash
python marketer_app.py --no-browser --port 8774
python -m unittest discover -q
```

Start the server in one terminal and run the suite in another. Open `http://127.0.0.1:8774/` for the planner, `/simulation` for fictional consumers and `/research` for saved study summaries. The dated replay records the local routes exercised. The app has no external dataset requirement for these views.

## Replay commands

Use the [data inventory](research/DATA.md) for filenames, placements, checksums and access terms. Give each run a new private directory so that historical references remain usable for comparison. The restored survey and secondary-analysis scripts have original directory-relative paths, so stage copies of the scripts in that run directory.

```bash
run_dir="$(mktemp -d)"
cp research/analyses/*.py "$run_dir/"
export OPENBLAS_NUM_THREADS=1
```

### UPAD join, association and recorded-action model

Place the six UPAD files directly in `$run_dir`, then run from the repository root.

```bash
python research/analyses/analysis.py --data-dir "$run_dir" --output-dir "$run_dir/results"
python research/compare_json.py research/evidence/audit.json "$run_dir/results/audit.json"
python research/compare_json.py research/evidence/associations.json "$run_dir/results/associations.json"
python research/compare_json.py results/baseline.json "$run_dir/results/baseline.json"
```

The audit reads the original files and refuses to overwrite an existing result. It writes three aggregate JSONs. The optional `--write-event-rows` flag restores the original `clean_events.csv` and `excluded_events.csv` exports. Use it only in approved private scratch because those CSVs contain identifiers. The [identifier audit below](#identifier-audit) records the rules and totals.

### Secondary surveys and profiles

Place the survey inputs under the exact paths given in the inventory. The V1 script needs both Romano–Han and Gen Z inputs. V2 and V3 depend on the earlier survey runs. Run only the analysis commands relevant to the inputs acquired.

```bash
python "$run_dir/survey_phase_v1.py"
python "$run_dir/survey_phase_v2.py"
python "$run_dir/survey_phase_v3_uncertainty.py"
python "$run_dir/phase7_segmentation.py"
python "$run_dir/ad_blockers_intrusion_v1.py"
python "$run_dir/vietnam_privacy_trust_v1.py"
```

Each writes its namesake JSON in `$run_dir/results/`. The segmentation file is named `phase7_segmentation_v1.json`. Survey V1–V3 and the ad-blocker benchmark also write private fitted arrays under `$run_dir/models/`. Compare each JSON with the version in `results/` using `python research/compare_json.py EXPECTED_JSON REPLAY_JSON`. The comparer checks the JSON structure and counts, uses `rtol=1e-11` and `atol=1e-12` for floating-point fields, and normalizes Windows/POSIX separators only in `source_file` fields.

### Criteo

Place the matching v2.1 gzip in the private input tree before preparing the sample. The preparation script checks the archive SHA-256 and the row count. The model and ranking commands were replayed using the historical derived sample and its preparation audit. Full archive preparation remains unverified. The archive was unavailable in this environment.

```bash
python "$run_dir/criteo_uplift_prepare.py"
python "$run_dir/criteo_visit_uplift.py" --split feature-group
python "$run_dir/criteo_uplift_validation.py"
```

Compare `criteo_visit_uplift_v3.json` and `criteo_uplift_validation_v3.json` under `$run_dir/results/` with the same names in `results/`. The fitted model written to `$run_dir/models/` is private research output.

### Location and surveillance experiments

The CLI entry points were checked. Numerical replay requires the original source files and the permitted access route in the [inventory](research/DATA.md). Set the two shell variables in the example to those local approved paths. The commands write aggregate JSON to a fresh destination.

```bash
python research/analyses/location_condition_research_v1.py --root "$location_root" --output "$run_dir/results/location_condition_research_v1.json"
python research/analyses/replication_crosscheck_v1.py --root "$location_root" --output "$run_dir/results/replication_crosscheck_v1.json"
python research/analyses/local_surveillance_v1.py --archive "$surveillance_zip" --output "$run_dir/results/local_surveillance_v1.json"
```

The location cross-check reads original response IDs locally to test linkage and emits aggregate counts. The location condition model and surveillance script have separate outcome definitions and do not share records or coefficients.

### Historical creative-screen diagnostic

The earlier V2 diagnostic depends on its version of the cue rubric. The current app may produce different outputs. For the after-abstention diagnostic and the 60-copy screen, use the historical code and English OCR asset with the current locked npm installation. Supply the UPAD ad CSV and the UW label CSV and screenshots as described in the [inventory](research/DATA.md). These scripts emit creative-level CSVs, which stay in the private run directory.

```bash
creative_dir="$(mktemp -d)"
git archive 19c04024c16f0e92debc5b7eb7fa88b95b0d6486 intrusive_ad_model.py threshold_engine.py VERSION ocr_ad.cjs models/eng.traineddata | tar -x -C "$creative_dir"
ln -s "$PWD/node_modules" "$creative_dir/node_modules"
cp research/analyses/screen_dataset.py research/analyses/external_screen_audit.py "$creative_dir/"
python "$creative_dir/screen_dataset.py"
python "$creative_dir/external_screen_audit.py"
python research/compare_json.py research/evidence/external_creative_audit.json "$creative_dir/results/external_creative_audit.json"
```

The historical before-abstention result is retained as an aggregate reference. Its exact earlier cue implementation was unavailable for this replay.

### Synthetic demonstration

A temporary directory protects the tracked model. The existing generator writes a longer filename, which must be renamed to the name the trainer reads.

```bash
demo_dir="$(mktemp -d)"
cp synthetic_demo/generate_49c_synthetic.py synthetic_demo/train.py "$demo_dir/"
python "$demo_dir/generate_49c_synthetic.py"
mv "$demo_dir/49c_synthetic_consumer_exposures.csv" "$demo_dir/exposures.csv"
python "$demo_dir/train.py"
python research/compare_json.py synthetic_demo/model.json "$demo_dir/model.json"
```

The fitted coefficients and metrics can differ in their last printed decimals across numerical environments. All outcomes are simulated. The synthetic CSV cannot reproduce any real-study result.

## Results-to-code mapping

For regression, MAE is mean absolute prediction error and RMSE is root mean squared prediction error on the stated target scale. A high rating means an observed outcome ≥5 on that study's 1–7 scale. The missed-high count is the number of those cases with a point prediction below 5, unless the row explicitly refers to the interval upper bound. Baselines use training data. Result rows below describe separate populations and targets.

| Result or claim | Input, original script and key configuration | Output and verification |
| --- | --- | --- |
| Earlier V2 §2 data table and join diagram, §3 ad-summary reconciliation | UPAD six original CSVs → [analysis.py](research/analyses/analysis.py). Exact key filtering and many-to-one privacy join. [Counts below](#identifier-audit). | [Audit JSON](research/evidence/audit.json), keys `sources`, `joins`, `ad_summary_reconciliation`. Replayed and compared with the earlier draft. |
| Earlier V2 §4–5 conditional click fractions, Cramér's V, holdout table and class counts | Same script and inputs. Target code 35 vs 32–34. Sort distinct users and shuffle with NumPy seed 49 for an 80/20 user split. Ad ID, sharing, privacy-setting and consent codes use indicators, dropping each reference category. Category levels come from the valid table. Full-batch logistic fit uses step size 2, L2 0.002 on non-intercept terms and up to 500 iterations. Baseline is the training click fraction. | [Associations](research/evidence/associations.json) and [baseline](results/baseline.json). Replayed. Model versus constant ROC-AUC 0.4993 vs 0.5000, Brier 0.18824 vs 0.18820, log loss 0.56398 vs 0.56387, accuracy 0.7486 for both and recall 0 for both at 0.5. No positive predictions at that cutoff, so precision is undefined. |
| Survey V1 MAE, baseline, ablations, descriptive and calibration tables | Romano–Han plus Gen Z workbook for the separate descriptive block → [survey_phase_v1.py](research/analyses/survey_phase_v1.py). Target mean of `I1`–`I6`. Exact full answer-vector groups, seed 49, 670/167 rows, training-only scaling, ridge α=10 with an unpenalized intercept. Predeclared fit uses age, gender, usage, mean benefits and mean privacy. Baseline is mean training intrusion. Same-survey predictors overlap with the construct. | [V1 JSON](results/survey_phase_v1.json). Replayed. Combined model MAE **0.521** vs **0.815** baseline. The same file records reliability, associations, quintiles and bootstrap intervals. |
| Survey V2 ablations, selection, error subgroups and missed highs | Romano–Han and V1 → [survey_phase_v2.py](research/analyses/survey_phase_v2.py). Reuses V1's holdout. Five grouped training folds (seed 4903) select candidate and α from 0.1, 1, 10, 100. Paired holdout bootstrap seed 4904. | [V2 JSON](results/survey_phase_v2.json). Replayed. MAE 0.509, gain over V1 95% interval −0.0033 to 0.0282. V1 missed 18/126 high ratings, V2 missed 25/126. |
| Survey V3 conformal coverage, width, subgroups and upper-bound misses | Romano–Han and V1/V2 → [survey_phase_v3_uncertainty.py](research/analyses/survey_phase_v3_uncertainty.py). Exact answer-vector groups. Split original training into 536 fit and 134 calibration rows, seed 4905. Model selection within fit rows. Use the ceiling of `(n_cal + 1) × 0.90` as the sorted calibration residual rank, absolute for two-sided and signed for upper-only. Clip bounds to 1–7 and evaluate inclusive coverage on the original 167-row holdout. | [V3 JSON](results/survey_phase_v3_uncertainty.json). Replayed. Two-sided 149/167 (89.2%), median width 2.342, mean width 2.193, below-neutral coverage 5/10. Upper-only 143/167 (85.6%); upper bound below 5 for 6/126 observed high cases. |
| Location experiments' condition descriptives, held-out error and missed highs | Verenkotte–Spann Studies 1 and 2 separately → [location_condition_research_v1.py](research/analyses/location_condition_research_v1.py). `PPI` target, 75/25 splits stratified by targeting × disclosure, seeds 4900/4901, five-fold checks on training only, condition mean vs global training mean, 2,000 paired bootstraps. One independent row per respondent within each study. | Historical [`location_condition_research_v1.json`](https://github.com/harisankar-work/personalised-threshold/blob/4431ea741422470ba77081e9056df41bde703dd3/results/location_condition_research_v1.json), summarized in the [location report](CORE_DATASET_RESOLUTION_AND_MODEL_RESULTS.md). Model vs baseline MAE 1.302 vs 1.389 and 1.222 vs 1.233. All 18/18 and 11/11 high cases missed. No numerical replay. Group-mean bootstrap intervals in this analysis describe condition means. |
| Location pooled-source linkage, PPI disagreement, field click and reach counts | Same sources plus pooled workbook, Study 3 and original R scripts → [replication_crosscheck_v1.py](research/analyses/replication_crosscheck_v1.py). Match exact `ResponseId` values across original and pooled files. Check one-hot `Pers` codes and composites and items. | Historical [`replication_crosscheck_v1.json`](https://github.com/harisankar-work/personalised-threshold/blob/4431ea741422470ba77081e9056df41bde703dd3/results/replication_crosscheck_v1.json) and [location report](CORE_DATASET_RESOLUTION_AND_MODEL_RESULTS.md). 810 IDs match, 14 Study 2 `PPI` composites differ, Study 3 has four aggregate ad sets. No numerical replay. |
| Perceived surveillance condition means, MAE, missed highs and conformal width | Zhang et al. archive → [local_surveillance_v1.py](research/analyses/local_surveillance_v1.py). Mean `ps_1`–`ps_4`. Condition-stratified 60/20/20 row splits, seeds 612/613. Training-only standardization and one-hot encodings, ridge α=10, condition-mean baseline, paired bootstrap seed 614. 90% order statistic of absolute calibration errors; clip intervals to 1–7. | Historical [`local_surveillance_v1.json`](https://github.com/harisankar-work/personalised-threshold/blob/4431ea741422470ba77081e9056df41bde703dd3/results/local_surveillance_v1.json) in development history. MAE 1.401 vs 1.418, 95/97 high cases missed by ridge, test coverage 92.46%, mean interval width 5.172. No numerical replay. |
| Independent ad-blocker survey MAE, tail failure and uncertainty | Redondo–Aznar XLSX → [ad_blockers_intrusion_v1.py](research/analyses/ad_blockers_intrusion_v1.py). Mean `ioa_1`–`ioa_4`, exact-answer groups, seed 1049, 1,209 train/302 test, five grouped folds for training-only selection, scaled ridge vs training-mean baseline. | [Ad-blocker JSON](results/ad_blockers_intrusion_v1.json). Replayed. MAE 0.840 vs 0.955, with low-tail diagnostic (MAE 2.528 for 26 observed negative scores). |
| Criteo per-arm visit metrics, ranking and uncertainty | 200k v2.1 sample → [preparation](research/analyses/criteo_uplift_prepare.py), [fit](research/analyses/criteo_visit_uplift.py), [validation](research/analyses/criteo_uplift_validation.py). Seed 49 for sample and split. Group exact 12-feature vectors, since no user ID is available. Training-only scaling and two L2-logistic visit fits vs training-arm rates. Difference between treatment/control predictions ranks uplift, compared with random ranking. | [Visit JSON](results/criteo_visit_uplift_v3.json), [ranking JSON](results/criteo_uplift_validation_v3.json). Model and ranking replayed on derived sample. Test n=39,983; control/treatment AUC 0.9448/0.9259; AUUC gain 0.00158 (95% interval −0.00063 to 0.00378). |
| Descriptive Gen Z, Romano–Han profiles and Vietnam privacy/trust scales | Gen Z workbook → [V1](research/analyses/survey_phase_v1.py). Gen Z and Romano–Han separately → [phase7_segmentation.py](research/analyses/phase7_segmentation.py) for privacy × relevance/benefits quadrants, counts and share intervals. Vietnam CSV → [vietnam_privacy_trust_v1.py](research/analyses/vietnam_privacy_trust_v1.py) for six scales and four Spearman associations with seeded 2,000-resample bootstrap. | [V1](results/survey_phase_v1.json), [profiles](results/phase7_segmentation_v1.json), [Vietnam](results/vietnam_privacy_trust_v1.json). Replayed. The apps' survey counts (296 and 837) describe source samples. |
| Earlier V2 §6 creative rubric counts, coverage and sanity cases | UPAD ad copies → [screen_dataset.py](research/analyses/screen_dataset.py). UW opinion labels and screenshots → [external_screen_audit.py](research/analyses/external_screen_audit.py), seed 49, 30 high (≥0.5) and 30 low (≤0.1), using the maximum opinion share. Earlier cue rules/OCR were version-dependent. Fictional A–F cases are in [survey_sanity_cases.json](survey_sanity_cases.json). | Historical aggregate [after](research/evidence/external_creative_audit.json) and [before abstention](research/evidence/external_creative_audit_before_abstention.json). The after-abstention UW summary matched in replay (59 zero-cue images), as did the 60/60 UPAD copies in the low tier. One aggressive-image demonstration requires its exact image and original score variant for a figure-level comparison. See the dated run record for replay scope. |
| L0–L4 synthetic dataset, regression table, MAE by level, high-discomfort check and descriptive segments | Generated exposures → [generator](synthetic_demo/generate_49c_synthetic.py), seed 49026, every fifth fictional consumer wholly held out. [Trainer](synthetic_demo/train.py) fits degree-2 polynomial features on four simulated traits, intensity and disclosure, ridge α=10, no second intercept, clipped predictions, and training level-mean baselines. IDs, segments and outcomes are excluded from predictors. | [Fictional model JSON](synthetic_demo/model.json), `metrics` and `segments`. Replayed. Discomfort MAE 0.5123 vs 0.7654, relevance 0.6974 vs 0.8326. Two of three high-discomfort test exposures are predicted below 5. Segment counts 100/75/76/49 are descriptive. |
| App verification and evidence-gated recommendation | Version-specific app tests, fixture/configured checks and rule logic in `marketer_app.py`, `threshold_engine.py`, `synthetic_simulation.py` and `test_*.py`. Research and simulation screens have separate sources. | [Current replay](research/evidence/README.md) and historical [completion report](49C_FINAL_PROJECT_REPORT.md). Historical browser counts describe other snapshots. There is no conducted five-condition causal study or verified real L0–L4 threshold. |

## Identifier audit

This is the repair implemented in the recovered analysis. It makes unmatched events explicit and avoids duplicating events on a repeated behavior key. It does not infer replacement IDs. Input CSV line one is the source table label and line two is the header. Leading/trailing spaces in column names are stripped and internal spaces are replaced with underscores.

| Step | Historical and replayed counts |
| --- | --- |
| Establish lookup keys | `UserTable.csv` has 50,000 unique `User_ID` values. `Privacy-Related_Features.csv` has 50,000 unique matching `User_ID` values. `AdCharacteristicsTable.csv` has 60 unique `Ad_ID` values. |
| Inspect event key | `User_Interaction_Table.csv` starts with 300,000 rows and 300,000 distinct event `ID` values. There are 288,091 distinct `(User_ID, Ad_ID)` pairs and 11,909 additional pair occurrences across the original table. Repeated pairs remain distinct action events. No timestamp or exposure key establishes a deduplication rule. |
| Exact filter and optional exclusion file | All 300,000 events match an ad. 249,831 match both a user and an ad. 50,169 are excluded for unknown users and zero for unknown ads. When row export is enabled, `unknown_user` takes precedence if both keys are missing from the lookups, and all other excluded events get `unknown_ad`. |
| Attach privacy features | A validated many-to-one inner merge on `User_ID` retains all 249,831 matched events from 49,690 users. The optional clean CSV renames event `ID` to `Event_ID`. |
| Keep behavior out of event join | All 50,000 behavior rows have known users, but only 31,600 distinct users. 13,183 users have multiple behavior rows and 18,400 rows are in excess of one per user. Behavior has no verified per-exposure key. |
| Keep aggregate counts out of event join | `interaction.csv` has 60 rows. Zero ads match the event-table count for any of the four action types, four report more clicks than impressions, and 31 report more total actions than impressions. Summary rows were audited and excluded from modeling. |

The earlier `Intrusiveness_Threshold_Data_Audit.xlsx` independently lists the same 249,831 retained and 50,169 excluded row counts. It separately describes dropping two error rows from a 1,125-row exploratory privacy workbook and generating several team-prepared CSVs. Its workbook-to-export logic is not the recovered UPAD script and was not replayed.

Published UPAD event counts before filtering were 74,782 likes, 74,978 shares, 75,086 comments, and 75,154 clicks. The model uses 199,891 events from 39,752 users for training and 49,940 events from 9,938 distinct holdout users for testing. It estimates a recorded action type, which has no impression-level denominator. The earlier draft's clean-event flowchart can be derived directly from the audit JSON.

## Gaps before submission

- Obtain the exact manuscript assessed in the second review and map every table, figure, caption and numerical claim to its output field. Record any changed rounded values, endpoints and inputs.
- Confirm an independent reviewer access route with the relevant source terms for the original location workbooks and surveillance archive. Rerun the two experiment families and compare the results to the submitted version. Keep raw records and model derivatives private.
- Repeat the replay from the original provider downloads in a clean environment, including the Criteo preparation path if still cited. Verify signed-out access separately for the repository, instructions, hosted application and each shareable data route.
- Review historical Git retention with the repository owner. Older commits contain source and row-level derivative files that were removed from the current tree. Removing a path from the latest tree does not remove it from reachable history. Confirm permissions and address any affected history before final public verification.
- Identify the exact deployed commit in Vercel, reconcile it with the submission commit and research outputs, then freeze and record the final release after development ends.
