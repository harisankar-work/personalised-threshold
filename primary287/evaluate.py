"""Reproduce the aggregate-only primary survey evaluation with authorized local CSVs."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, f1_score, mean_absolute_error,
    precision_score, r2_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LEVEL = "conceptual_level_l0_l4"
FAMILY = "creative_family_id"
RATINGS = ["intrusiveness_score", "discomfort_score", "relevance_score",
           "surveillance_score", "trust_score", "purchase_intent",
           "avoidance_intent", "acceptability_score"]
FEATURES = ["location_used", "browsing_history_used", "purchase_history_used",
            "contextual_data_used", "number_of_data_sources", "disclosure_present"]
SEED = 49287
NAMES = ("respondents", "advertisements", "ad_responses")


def load(folder):
    paths = {n: folder / f"{n}_287.csv" for n in NAMES}
    tables = {n: pd.read_csv(p) for n, p in paths.items()}
    r, a, y = (tables[n] for n in NAMES)
    if any(t.isna().any().any() for t in tables.values()):
        raise ValueError("Missing values require a documented handling decision")
    for t, key in [(r, "respondent_id"), (a, "ad_id"), (y, "respondent_id"), (y, "ad_id")]:
        if not t[key].is_unique:
            raise ValueError(f"Duplicate {key}; this release requires one exposure per respondent and ad record")
    if set(r.respondent_id) != set(y.respondent_id) or set(a.ad_id) != set(y.ad_id):
        raise ValueError("Unmatched join keys")
    d = y.merge(r, on="respondent_id", validate="one_to_one").merge(
        a, on="ad_id", validate="one_to_one", suffixes=("", "_ad"))
    if not d.assigned_pool.eq(d.assigned_pool_ad).all() or not d.presentation_order.eq(1).all():
        raise ValueError("Pool mismatch or unexpected presentation sequence")
    if not d[RATINGS].apply(lambda x: x.between(1, 7)).all().all():
        raise ValueError("Outcome outside 1–7")
    if not d[["consent_given", "attention_check_passed", "is_pilot",
              "high_intrusion", "high_discomfort"] + [c for c in FEATURES if c != "number_of_data_sources"]].isin([0, 1]).all().all():
        raise ValueError("Invalid binary encoding")
    family_levels = d.groupby(FAMILY)[LEVEL].unique()
    if any(len(v) != 1 for v in family_levels) or set(d[LEVEL]) != {f"L{i}" for i in range(5)}:
        raise ValueError("Unexpected family/level design")
    if not family_levels.str[0].value_counts().eq(2).all():
        raise ValueError("Expected two families per level")
    for flag, target in zip(("high_intrusion", "high_discomfort"), RATINGS[:2]):
        d[flag + "_ge5"] = d[target].ge(5).astype(int)
    audit = {n: {"rows": len(t), "columns": list(t.columns), "missing": int(t.isna().sum().sum()),
                 "duplicate_rows": int(t.duplicated().sum()),
                 "sha256": hashlib.sha256(paths[n].read_bytes()).hexdigest()} for n, t in tables.items()}
    return d, audit


def describe(d, key):
    out = {}
    for name, rows in d.groupby(key):
        out[name] = {"n":len(rows), "means":rows[RATINGS].mean().to_dict(),
                     "sd":rows[RATINGS].std().to_dict(),
                     "high_intrusion":int(rows.high_intrusion_ge5.sum()),
                     "high_discomfort":int(rows.high_discomfort_ge5.sum())}
    return out


def scores(y, p, binary):
    if binary:
        pred = p >= .5
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
        bins = []
        for lo in np.arange(0, 1, .2):
            mask = (p >= lo) & (p < lo + .2 if lo < .8 else p <= 1)
            if mask.any():
                bins.append({"n":int(mask.sum()), "pred":float(p[mask].mean()), "observed":float(y[mask].mean())})
        return {"auc":roc_auc_score(y,p) if len(set(y))==2 else None,
                "ap":average_precision_score(y,p) if len(set(y))==2 else None,
                "brier":brier_score_loss(y,p), "recall":recall_score(y,pred,zero_division=0),
                "precision":precision_score(y,pred,zero_division=0),
                "specificity":float(tn/max(1,tn+fp)), "f1":f1_score(y,pred,zero_division=0),
                "balanced_accuracy":balanced_accuracy_score(y,pred),
                "confusion":[int(v) for v in (tn,fp,fn,tp)], "reliability":bins}
    high = y >= 5
    return {"mae":mean_absolute_error(y,p), "rmse":float(np.sqrt(np.mean((p-y)**2))),
            "r2":r2_score(y,p), "bias":float(np.mean(p-y)),
            "error_quantiles":np.quantile(p-y,[.1,.5,.9]).tolist(),
            "high":int(high.sum()), "missed_high":int((high & (p<5)).sum())}


def evaluate(d, leave_one=False):
    family = d[FAMILY]
    pairs = [sorted(g[FAMILY].unique()) for _, g in d.groupby(LEVEL)]
    folds = [[x] for x in sorted(family.unique())] if leave_one else list(map(list, zip(*pairs)))
    x = d[FEATURES].to_numpy()
    output = {}
    details = []
    for held in folds:
        test = family.isin(held).to_numpy()
        train = ~test
        assert set(family[train]).isdisjoint(family[test])
        assert set(d.respondent_id[train]).isdisjoint(d.respondent_id[test])
        details.append({"held_out":held, "train_families":sorted(family[train].unique()),
                        "train_n":int(train.sum()), "test_n":int(test.sum()),
                        "levels":describe(d[test],LEVEL)})
    for target in RATINGS[:3] + ["high_intrusion_ge5", "high_discomfort_ge5"]:
        y = d[target].to_numpy()
        binary = target.endswith("_ge5")
        variants = ("mean","level_mean","logistic","forest") if binary else ("mean","level_mean","ridge","forest")
        predictions = {v:np.empty(len(y)) for v in variants}
        for held in folds:
            test = family.isin(held).to_numpy()
            train = ~test
            predictions["mean"][test] = y[train].mean()
            means = d[train].groupby(LEVEL)[target].mean()
            predictions["level_mean"][test] = d.loc[test,LEVEL].map(means).fillna(y[train].mean())
            linear = (make_pipeline(StandardScaler(), LogisticRegression(C=1)) if binary
                      else make_pipeline(StandardScaler(), Ridge(alpha=10)))
            forest_type = RandomForestClassifier if binary else RandomForestRegressor
            extra = {"class_weight":"balanced"} if binary else {}
            models = [(variants[2],linear), ("forest",forest_type(
                n_estimators=100,max_depth=3,min_samples_leaf=12,random_state=SEED,**extra))]
            for name, model in models:
                model.fit(x[train],y[train])
                predictions[name][test] = (model.predict_proba(x[test])[:,1] if binary
                                           else model.predict(x[test]).clip(1,7))
        output[target] = {name:scores(y,p,binary) for name,p in predictions.items()}
        if not binary:
            # Resample whole creative families within level. The interval is
            # conditional on fixed out-of-fold predictions, with two families
            # per level, and does not estimate external predictive coverage.
            units = [np.flatnonzero(family.eq(fam)) for pair in pairs for fam in pair]
            rng = np.random.default_rng(SEED)
            draws = (np.arange(0, len(units), 2)[None,:,None]
                     + rng.integers(0, 2, size=(2000,len(pairs),2))).reshape(2000,-1)
            for name, p in predictions.items():
                output[target][name]["mae_gain_vs_level_mean"] = (
                    output[target]["level_mean"]["mae"] - output[target][name]["mae"])
                gain = abs(y-predictions["level_mean"]) - abs(y-p)
                sums = np.array([gain[idx].sum() for idx in units])
                counts = np.array([len(idx) for idx in units])
                output[target][name]["conditional_family_bootstrap_gain_95"] = np.quantile(
                    sums[draws].sum(axis=1)/counts[draws].sum(axis=1), [.025,.975]).tolist()
            output[target]["by_family"] = {
                fam:{k:scores(y[family.eq(fam)],p[family.eq(fam)],False)
                     for k,p in predictions.items()} for fam in sorted(family.unique())}
            output[target]["by_level"] = {
                level:{k:scores(y[d[LEVEL].eq(level)],p[d[LEVEL].eq(level)],False)
                       for k,p in predictions.items()} for level in sorted(d[LEVEL].unique())}
        else:
            for name, p in predictions.items():
                output[target][name]["threshold_sensitivity"] = {
                    str(t):{"recall":recall_score(y,p>=t,zero_division=0),
                            "false_positive_rate":float((p[y==0]>=t).mean())}
                    for t in (.35,.5,.65)}
    return {"folds":details,"targets":output}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results/primary287_v1.json"))
    args = parser.parse_args()
    d, audit = load(args.data_dir)
    base = d[d.consent_given.eq(1) & d.is_pilot.eq(0)].copy()
    use = base[base.attention_check_passed.eq(1)].copy()
    traits = ["privacy_concern","personalization_preference","data_sharing_willingness"]
    correlation = lambda frame,a,b: float(frame[a].rank().corr(frame[b].rank()))
    pairs = [("intrusiveness_score","acceptability_score"),("privacy_concern","intrusiveness_score"),
             ("data_sharing_willingness","acceptability_score")]
    results = {
        "version":"primary287_v1", "scope":"Research only. User-reported primary collection; documentation not independently verified.",
        "seed":SEED, "dependencies":{"python":platform.python_version(),"pandas":pd.__version__,
                                      "numpy":np.__version__,"sklearn":sklearn.__version__},
        "files":audit, "joined":len(d), "eligible":len(use), "attention_failed":int(len(base)-len(use)),
        "consent_yes":int(d.consent_given.sum()), "pilots":int(d.is_pilot.sum()),
        "time_sec":d.completion_time_sec.describe().to_dict(),
        "pools":d.assigned_pool.value_counts().to_dict(),
        "versions_per_family":d.groupby(FAMILY).survey_version.nunique().to_dict(),
        "family_design":{fam:{"level":g[LEVEL].iloc[0],"n_texts":g.ad_text.nunique(),
            "n_files":g.creative_filename.nunique(),"n_disclosed":int(g.disclosure_present.sum())}
            for fam,g in d.groupby(FAMILY)},
        "flags":{flag:{key:{"disagreements":int(g[flag].ne(g[flag+"_ge5"]).sum()),
                             "supplied_high":int(g[flag].sum()),"derived_high":int(g[flag+"_ge5"].sum())}
                      for key,g in [("all",d),("included",use)]}
                 for flag in ("high_intrusion","high_discomfort")},
        "demographics":{c:use[c].value_counts().to_dict() for c in ["age_group","gender","occupation"]},
        "traits":use[traits].describe().to_dict(),
        "associations":{a+" / "+b:{"pooled_rho":correlation(use,a,b),
            "family_rho":[correlation(g,a,b) for _,g in use.groupby(FAMILY)]} for a,b in pairs},
        "by_level":describe(use,LEVEL), "by_family":describe(use,FAMILY),
        "including_attention_failures":describe(base,LEVEL),
        "features":FEATURES, "coverage":0, "abstention":"No deployable empirical prediction or individual threshold",
        "grouped":evaluate(use), "leave_one_family_out":evaluate(use,True),
        "attention_sensitivity_targets":evaluate(base)["targets"]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(results,indent=2,allow_nan=False,default=lambda x:x.item())+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
