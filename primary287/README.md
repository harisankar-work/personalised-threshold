# Primary survey evaluation contract

Run from the repository root with Python 3.14.6 and install pandas==3.0.3, numpy==2.4.6 and scikit-learn==1.9.0 in an isolated research environment.

    python primary287/evaluate.py PATH_TO_AUTHORIZED_CSV_FOLDER

The folder must contain respondents_287.csv, advertisements_287.csv and ad_responses_287.csv obtained from the survey custodian with permission. Keep them outside the repository. The script reads them without editing, checks one-to-one joins, derives two research flags, and emits aggregate-only JSON. It exports no participant predictions or identifiers. The JSON includes exact input schemas and digests. Use a distinct --out path when reviewing a new dataset.

The six inputs listed in FEATURES are ad attributes, known when the creative is specified. LEVEL and FAMILY define comparisons and splits. Respondent flags are used for exclusions only. Primary targets are three 1–7 rating columns and two derived ≥5 labels. Other ratings are descriptive and cannot enter training. No customer attributes or predicted risks flow to campaign decisions.

The dashboard reads the aggregate JSON as a required deployment asset. Only level summaries and the research status are sent to the browser. Runtime inference and thresholds never import the training module. The JSON includes the fixed evaluation settings, estimated metrics and sensitivity results. It is the research artifact; no deployable fitted model is approved.
