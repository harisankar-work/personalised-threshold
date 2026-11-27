# Kiwadoi consumer feature evaluation

The supplied questionnaire documents Sections 1 and 2 before the ad, a neutral briefing and attention check, and ratings afterward. All eight named attitude columns use the documented 1–7 codes, all three ordinal behavior columns use 1–5, and the two categorical behavior columns contain Yes, No and Unsure. General trust and usefulness are separate from post-ad trust and relevance. The CSVs show one exposure per person, presentation order 1 and Main pool, with V01–V10 tied to families. This matches the instrument's one-ad option structurally. The exact administered form, display order, recruitment and assignment are not independently verified. The document also describes a five-ad option that does not match the records. Its neutral transition does not rule out same-session response bias.

The 276 included rows, original scores, derived ≥5 labels and complementary respondent- and family-disjoint folds are unchanged. We compared fixed standardized Ridge (alpha 20) and logistic (C 0.2) across consumer-only, ad-level-only, compact combined, all-attitude, behavior-extended and compact interaction designs. Categorical level indicators avoid assumed equal spacing. Compact variables are privacy concern, personalization preference and data-sharing willingness. The limited interactions multiply those traits by L2–L4 indicators. Disclosure was constant, so trust-by-disclosure cannot be estimated. Source indicators encode level here. We used no composite, identifiers, demographics, post-exposure values or administrative features. We did not expand to trees or tune against previously reviewed outcomes. LOFO repeats the same specifications. Intervals resample whole families within levels conditional on fixed out-of-fold predictions, with only two families per level.

| Target | Population loss | Compact combined loss | Gain (95% family interval) | Decision |
|---|---:|---:|---:|---|
| Intrusion MAE | 0.8768 | 0.8692 | 0.0076 [−0.0399, 0.0534] | Population |
| Discomfort MAE | 0.8225 | 0.8374 | −0.0150 [−0.0380, 0.0079] | Population |
| Relevance MAE | 0.9058 | 0.8969 | 0.0089 [0.0002, 0.0187] | Population; LOFO interval crosses zero |
| High intrusion Brier | 0.1262 | 0.1175 | 0.0087 [0.0062, 0.0112] | Compact research candidate only |
| High discomfort Brier | 0.1334 | 0.1316 | 0.0019 [−0.0009, 0.0048] | Population |

The all-attitude design had the lowest grouped relevance MAE (0.8920), with an interval crossing zero. For comparison, previous forest MAEs were 0.9055, 0.8391 and 0.9159. Added behavior and interactions did not consistently help. Privacy concern had positive standardized coefficients for intrusion in both compact fits (0.411 and 0.380) and high-intrusion risk (0.669 and 0.520). Preference and willingness coefficients were smaller or changed sign for intrusion. These are fitted associations, not causal effects or isolated ablation estimates. Compact grouped intrusion MAE exceeded in-fold MAEs of 0.856 and 0.824. Training metrics, RMSE, R², coefficients, per-family losses, classification metrics and calibration bins are preserved in the evaluation JSON.

High-intrusion Brier is better than the previous forest's 0.1312 and remains better in LOFO (0.1116). Brier combines calibration and discrimination. No separate calibration gain is established. At 0.5, compact logistic had 71 TP, 22 FP and 32 FN versus population 73 TP, 36 FP and 30 FN. At a training-only policy targeting at least 90% inner recall, both caught 101 cases on the outer folds, but compact had 78 FP versus 60. The training-only FPR-target policy did not yield comparable outer FPR: compact had 5 FP and 43 TP versus 48 FP and 85 TP. A lower error score does not resolve the practical high-recall trade-off.

The app retains population estimates for all outcomes. The compact high-risk artifact is fitted for reproducible local research and excluded from deployment. No consumer controls imply individualized risk. Personal thresholds remain unsupported because creative is nested within level and each person rates one ad. Administration confirmation would resolve a provenance question but would not establish an acceptable operating point.

Run from the root with the same environment and authorized CSV folder as v2:

    python -m primary287.consumer PATH_TO_AUTHORIZED_CSV_FOLDER

This writes aggregate held-out results and a JSON model with feature order, scaler and coefficients. No raw records are emitted. Application and manuscript publication are outside this candidate.
Verification: 93 regression tests passed. Local Chrome confirmed population fallback and abstention. Different profile payloads returned identical population results.
