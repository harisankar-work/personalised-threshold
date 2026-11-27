"""Fixed candidate comparison; all transformations are fit inside family folds."""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from primary287.evaluate import FAMILY, LEVEL, RATINGS, SEED, load, scores
from intrusive_ad_model import classify

TARGETS = RATINGS[:3] + ["high_intrusion_ge5", "high_discomfort_ge5"]


def evaluate(d, folds, x):
    family = d[FAMILY].to_numpy()
    level = d[LEVEL].to_numpy()
    groups = [np.flatnonzero(family == f) for f in sorted(set(family))]
    rng = np.random.default_rng(SEED)
    draws = rng.integers(len(groups), size=(2000, len(groups)))
    output = {}
    for target in TARGETS:
        y = d[target].to_numpy()
        binary = target.endswith("_ge5")
        names = ["level", "cue_linear", "shrink_risk", "sigmoid_risk"] if binary else [
            "level", "median", "cue_linear", "ordinal"]
        arrays = {name: np.empty(len(d)) for name in names}
        operating = np.empty(len(d), dtype=bool)
        thresholds = []
        for held in folds:
            test = np.isin(family, held)
            train = ~test
            assert set(d.respondent_id[train]).isdisjoint(d.respondent_id[test])

            def lookup(fit, values, median=False, shrink=0):
                default = values[fit].mean()
                stats = {}
                for lv in set(level):
                    v = values[fit & (level == lv)]
                    stats[lv] = ((np.median(v) if median else
                                  (v.sum() + shrink*default)/(len(v)+shrink))
                                 if len(v) else default)
                return np.array([stats[lv] for lv in level])

            arrays["level"][test] = lookup(train, y)[test]
            m = make_pipeline(StandardScaler(), LogisticRegression(C=.2) if binary else Ridge(alpha=20))
            m.fit(x[train], y[train])
            arrays["cue_linear"][test] = (m.predict_proba(x[test])[:,1] if binary
                                          else m.predict(x[test]).clip(1,7))
            if binary:
                raw = lookup(train, y, shrink=5)
                arrays["shrink_risk"][test] = raw[test]
                inner = np.zeros(len(d))
                for f in set(family[train]):
                    valid = train & (family == f)
                    inner[valid] = lookup(train & ~valid, y, shrink=5)[valid]
                cal = LogisticRegression(C=1).fit(inner[train,None], y[train])
                arrays["sigmoid_risk"][test] = cal.predict_proba(raw[test,None])[:,1]
                # Recall objective applied only to cross-fitted training cases.
                candidates = [.15,.25,.35,.45,.5,.55,.65]
                okay = [t for t in candidates if (inner[train & (y==1)]>=t).mean()>=.95]
                threshold = max(okay, default=0.0)
                thresholds.append(threshold)
                operating[test] = raw[test] >= threshold
            else:
                arrays["median"][test] = lookup(train,y,median=True)[test]
                probs = np.stack([lookup(train,(y>=k).astype(float),shrink=5)[test]
                                  for k in range(2,8)])
                arrays["ordinal"][test] = 1 + probs.sum(axis=0)
        result = {}
        baseline = arrays["level"]
        for name, p in arrays.items():
            score = scores(y,p,binary)
            loss = (lambda a: (a-y)**2) if binary else (lambda a: abs(a-y))
            delta = loss(baseline)-loss(p)
            sums = np.array([delta[idx].sum() for idx in groups])
            ns = np.array([len(idx) for idx in groups])
            score["gain_vs_level"] = float(delta.mean())
            score["family_bootstrap_gain_95"] = np.quantile(sums[draws].sum(axis=1)/ns[draws].sum(axis=1),[.025,.975]).tolist()
            score["by_family"] = {f:{"n":int(mask.sum()), "loss":float(loss(p)[mask].mean())}
                                  for f in sorted(set(family)) for mask in [family==f]}
            score["by_level"] = {lv:{"n":int(mask.sum()),"loss":float(loss(p)[mask].mean())}
                                 for lv in sorted(set(level)) for mask in [level==lv]}
            if not binary:
                score["median_ae"] = float(np.median(abs(p-y)))
            result[name] = score
        if binary:
            result["training_threshold_policy"] = {
                "thresholds":thresholds,
                "confusion":scores(y,operating.astype(float),True)["confusion"]}
        output[target] = result
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("data_dir",type=Path)
    args=parser.parse_args()
    d,audit=load(args.data_dir)
    d=d[d.consent_given.eq(1)&d.is_pilot.eq(0)&d.attention_check_passed.eq(1)].reset_index(drop=True)
    pairs=[sorted(g[FAMILY].unique()) for _,g in d.groupby(LEVEL)]
    folds=list(map(list,zip(*pairs)))
    cue=[classify(t) for t in d.ad_text]
    flags=np.column_stack([d[LEVEL].eq(k) for k in sorted(d[LEVEL].unique())])
    x=np.column_stack((flags,[c["privacy_score"] for c in cue],[c["pressure_score"] for c in cue]))
    estimates={}
    for lv,g in d.groupby(LEVEL):
        keys=RATINGS[:3]+["high_intrusion_ge5","high_discomfort_ge5"]
        fam=g.groupby(FAMILY)[keys].mean()
        estimates[lv]={"n":len(g),"families":len(fam),
                       "mean":g[keys].mean().to_dict(), "rating_median":g[RATINGS[:3]].median().to_dict(),
                       "family_rating_median_range": {k:[float(g.groupby(FAMILY)[k].median().min()),float(g.groupby(FAMILY)[k].median().max())] for k in RATINGS[:3]}, "family_range":{k:[float(fam[k].min()),float(fam[k].max())] for k in keys}}
    artifact={"version":"primary287_population_v2","levels":estimates,
              "source":"Primary survey population estimates","cutoff":5,
              "support":"Observed families only; family ranges are descriptive, not prediction intervals."}
    output={"files":audit,"seed":SEED,"folds":folds,"grouped":evaluate(d,folds,x),
            "leave_one_family_out":evaluate(d,[[f] for f in sorted(d[FAMILY].unique())],x),
            "cue_variation_by_level":{lv:np.unique(x[d[LEVEL].eq(lv),-2:],axis=0).shape[0]
                                      for lv in sorted(d[LEVEL].unique())}}
    for name,payload in [("primary287_population_v2",artifact),("primary287_optimization_v2",output)]:
        Path(f"results/{name}.json").write_text(json.dumps(payload,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    main()
