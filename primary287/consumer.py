"""Fixed consumer-feature ablation on the existing grouped survey splits."""
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from primary287.evaluate import FAMILY, LEVEL, RATINGS, SEED, load, scores

ATTITUDES = ["privacy_awareness", "privacy_control", "privacy_concern",
             "privacy_behaviour", "personalization_preference",
             "data_sharing_willingness", "general_trust", "perceived_usefulness"]
COMPACT = ["privacy_concern", "personalization_preference", "data_sharing_willingness"]
BEHAVIOR = ["online_hours", "shopping_frequency", "ad_exposure_frequency"]
CATEGORIES = ["ad_blocker", "opt_out_history"]
TARGETS = RATINGS[:3] + ["high_intrusion_ge5", "high_discomfort_ge5"]


def features(d):
    if not d[ATTITUDES].isin(range(1, 8)).all().all():
        raise ValueError("Invalid 1-7 attitude coding")
    if not d[BEHAVIOR].isin(range(1, 6)).all().all():
        raise ValueError("Invalid 1-5 behavior coding")
    if not d[CATEGORIES].isin(["Yes", "No", "Unsure"]).all().all():
        raise ValueError("Invalid behavior category")
    level = pd.DataFrame({lv: d[LEVEL].eq(lv).astype(int) for lv in [f"L{i}" for i in range(5)]})
    choices = pd.DataFrame({f"{key}_{value}":d[key].eq(value).astype(int)
                            for key in CATEGORIES for value in ["Yes", "Unsure"]})
    # Use separate level indicators, never equal distances between levels.
    interactions = pd.DataFrame({f"{trait}:{lv}": (d[trait]-4)*level[lv]
                                 for trait in COMPACT for lv in ["L2","L3","L4"]})
    return {"consumer_only":d[ATTITUDES], "ad_only":level,
            "compact_combined":level.join(d[COMPACT]),
            "attitude_combined":level.join(d[ATTITUDES]),
            "behavior_combined":level.join(d[ATTITUDES+BEHAVIOR]).join(choices),
            "interaction_combined":level.join(d[COMPACT]).join(interactions)}


def estimator(binary):
    return make_pipeline(StandardScaler(),
                         LogisticRegression(C=.2) if binary else Ridge(alpha=20))


def assess(d, designs, folds):
    family = d[FAMILY].to_numpy()
    levels = d[LEVEL].to_numpy()
    out = {}
    groups = [np.flatnonzero(family == f) for f in sorted(set(family))]
    rng = np.random.default_rng(SEED)
    pairs = np.array([[i for i,idx in enumerate(groups) if levels[idx[0]]==lv]
                      for lv in sorted(set(levels))])
    draw = pairs[np.arange(len(pairs))[None,:,None],
                 rng.integers(0,2,(2000,len(pairs),2))].reshape(2000,-1)
    masks = [np.isin(family, hold) for hold in folds]
    if not np.all(np.sum(masks,axis=0)==1):
        raise ValueError("Each case must be evaluated exactly once")
    for target in TARGETS:
        y = d[target].to_numpy()
        binary = target.endswith("_ge5")
        pred = {n: np.empty(len(d)) for n in ["population",*designs]}
        coefficients = {n:[] for n in designs}
        training = {n:[] for n in designs}
        decisions = {n:{key:np.zeros(len(d),dtype=bool) for key in ("recall","fpr")}
                     for n in pred} if binary else {}

        def population(fit, test):
            fn = np.mean if binary else np.median
            means = {lv:fn(y[fit & (levels==lv)]) for lv in set(levels[fit])}
            return np.array([means.get(lv, fn(y[fit])) for lv in levels[test]])

        def predict(name, fit, test):
            if name == "population":
                return population(fit,test)
            x = designs[name]
            m = estimator(binary).fit(x[fit],y[fit])
            return m.predict_proba(x[test])[:,1] if binary else m.predict(x[test]).clip(1,7)

        for test in masks:
            fit = ~test
            assert set(family[fit]).isdisjoint(family[test])
            assert set(d.respondent_id[fit]).isdisjoint(d.respondent_id[test])
            pred["population"][test] = population(fit,test)
            for name,x in designs.items():
                model = estimator(binary).fit(x[fit],y[fit])
                def estimate(mask):
                    return (model.predict_proba(x[mask])[:,1] if binary
                            else model.predict(x[mask]).clip(1,7))
                pred[name][test] = estimate(test)
                fitted = estimate(fit)
                training[name].append(float(np.mean((y[fit]-fitted)**2) if binary
                                             else np.mean(abs(y[fit]-fitted))))
                coefficients[name].append(dict(zip(x.columns,model[-1].coef_.ravel().tolist())))
            if binary:
                for name in pred:
                    inner = np.zeros(len(y))
                    for f in set(family[fit]):
                        validation = fit & (family==f)
                        inner[validation] = predict(name,fit & ~validation,validation)
                    positives = fit & (y==1)
                    negatives = fit & (y==0)
                    grid = np.linspace(0,1,101)
                    recall = [(inner[positives]>=t).mean() for t in grid]
                    fpr = [(inner[negatives]>=t).mean() for t in grid]
                    candidates = [i for i,t in enumerate(grid) if recall[i]>=.9]
                    ri = max(candidates)
                    candidates = [i for i,t in enumerate(grid) if fpr[i]<=.25]
                    fi = min(candidates,key=lambda i:(-recall[i],fpr[i],i))
                    decisions[name]["recall"][test] = pred[name][test]>=grid[ri]
                    decisions[name]["fpr"][test] = pred[name][test]>=grid[fi]
        loss = lambda p: (p-y)**2 if binary else abs(p-y)
        result = {}
        for name,p in pred.items():
            row = scores(y,p,binary)
            delta = loss(pred["population"])-loss(p)
            sums = np.array([delta[idx].sum() for idx in groups])
            counts = np.array([len(idx) for idx in groups])
            row["gain"] = float(delta.mean())
            row["family_gain_interval"] = np.quantile(
                sums[draw].sum(axis=1)/counts[draw].sum(axis=1), [.025,.975]).tolist()
            row["by_family"] = {family[i[0]]:float(loss(p)[i].mean()) for i in groups}
            if name in designs:
                row["training_loss"] = training[name]
                row["standardized_coefficients"] = coefficients[name]
            if binary:
                row["training_operating_policies"] = {
                    key:scores(y,decision.astype(float),True)["confusion"]
                    for key,decision in decisions[name].items()}
            result[name] = row
        out[target] = result
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("data_dir",type=Path)
    p.add_argument("--out",type=Path,default=Path("results/primary287_consumer_v3.json"))
    args=p.parse_args()
    d,audit=load(args.data_dir)
    d=d[d.consent_given.eq(1)&d.is_pilot.eq(0)&d.attention_check_passed.eq(1)].reset_index(drop=True)
    pairs=[sorted(g[FAMILY].unique()) for _,g in d.groupby(LEVEL)]
    folds=list(map(list,zip(*pairs)))
    designs=features(d)
    output={"version":"primary287_consumer_v3","files":audit,
            "dependencies":{"python":platform.python_version(),"numpy":np.__version__,
                            "pandas":pd.__version__,"sklearn":sklearn.__version__},
            "seed":SEED,"folds":folds,"n":len(d),
            "designs":{name:list(x.columns) for name,x in designs.items()},
            "grouped":assess(d,designs,folds),
            "leave_one_family_out":assess(d,designs,[[f] for pair in pairs for f in pair])}
    # Fit the most useful compact research specification after evaluation.
    # This aggregate artifact stays outside the application's deployment allowlist.
    x = designs["compact_combined"]
    fitted = estimator(True).fit(x,d["high_intrusion_ge5"])
    scaler,model = fitted
    artifact = {"version":"primary287_consumer_risk_v3", "status":"research_only",
                "target":"high_intrusion_ge5", "features":list(x.columns),
                "center":scaler.mean_.tolist(), "scale":scaler.scale_.tolist(),
                "coefficients":model.coef_[0].tolist(), "intercept":float(model.intercept_[0]),
                "n":len(d), "reason":"Administration and high-recall operating performance remain unresolved"}
    artifact_path = args.out.with_name("primary287_consumer_risk_v3.json")
    artifact_path.write_text(json.dumps(artifact,indent=2)+"\n",encoding="utf-8")
    args.out.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
