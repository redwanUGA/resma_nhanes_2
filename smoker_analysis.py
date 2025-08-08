from __future__ import annotations
import os
import numpy as np
import pandas as pd
import pyreadstat
from scipy.stats import ttest_ind
import statsmodels.api as sm
from patsy import dmatrix

from descriptive_stats import (
    process_cycles,
    categorize_amalgam,
    weighted_stats,
)

# Mapping of survey cycles to Smoking Questionnaire files
SMOKING_FILES = {
    "1999-2000": "SMQ.xpt",
    "2001-2002": "SMQ_B.xpt",
    "2003-2004": "SMQ_C.xpt",
    "2009-2010": "SMQ_F.xpt",
    "2011-2012": "SMQ_G.xpt",
    "2013-2014": "SMQ_H.xpt",
    "2015-2016": "SMQ_I.xpt",
    "2017-2018": "SMQ_J.xpt",
}

REQUIRED_LABELS = ["CBC", "Demographics", "Dental", "CRP", "Mercury", "Smoking"]


def cycles_with_smoking(log_path: str = "download_log.csv") -> set[str]:
    """Return cycles with all required files including smoking questionnaire."""
    if not os.path.exists(log_path):
        alt = os.path.join("national_stats", "download_log.csv")
        if os.path.exists(alt):
            log_path = alt
        else:
            return set(SMOKING_FILES.keys())
    log_df = pd.read_csv(log_path)
    valid: set[str] = set()
    for cycle, grp in log_df.groupby("Cycle"):
        statuses = {lbl: grp[grp["Label"] == lbl]["Status"].iloc[0] for lbl in grp["Label"].unique()}
        if all(statuses.get(lbl) == "success" for lbl in REQUIRED_LABELS):
            valid.add(cycle)
    return valid


def load_smoking(data_dir: str, cycles: set[str]) -> pd.DataFrame:
    """Load SMQ020 and SMQ040 for the given cycles."""
    frames = []
    for cycle in cycles:
        fname = SMOKING_FILES.get(cycle)
        if not fname:
            continue
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            continue
        smq, _ = pyreadstat.read_xport(fpath)
        cols = [c for c in ["SEQN", "SMQ020", "SMQ040"] if c in smq.columns]
        smq = smq[cols]
        smq["Cycle"] = cycle
        frames.append(smq)
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["SEQN", "SMQ020", "SMQ040", "Cycle"])


def classify_smoking(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def _classify(row):
        if row.get("SMQ020") == 2:
            return "Never smoker"
        if row.get("SMQ020") == 1:
            if row.get("SMQ040") == 1:
                return "Current daily smoker"
            if row.get("SMQ040") == 2:
                return "Current non-daily smoker"
            if row.get("SMQ040") == 3:
                return "Former smoker"
        return np.nan
    df["SmokingStatus"] = df.apply(_classify, axis=1)
    df["Amalgam Group"] = df["amalgam_surfaces"].apply(categorize_amalgam)
    return df


def process_with_smoking(data_dir: str = "nhanes_data") -> pd.DataFrame:
    base_df, _ = process_cycles(data_dir)
    if base_df.empty:
        return base_df
    valid_cycles = cycles_with_smoking()
    base_df = base_df[base_df["Cycle"].isin(valid_cycles)].copy()
    smq_df = load_smoking(data_dir, valid_cycles)
    combined = base_df.merge(smq_df, on=["SEQN", "Cycle"], how="left")
    combined = classify_smoking(combined)
    return combined


def compute_smoking_descriptive(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]
    results = []
    for cycle, df_cycle in df.groupby("Cycle"):
        for smoke, df_smoke in df_cycle.groupby("SmokingStatus"):
            for amalgam, df_group in df_smoke.groupby("Amalgam Group"):
                for marker in markers:
                    sub = df_group[[marker, "WTMEC2YR"]].dropna()
                    if sub.empty:
                        continue
                    m, sd, lo, hi = weighted_stats(sub[marker], sub["WTMEC2YR"])
                    results.append({
                        "Cycle": cycle,
                        "SmokingStatus": smoke,
                        "Amalgam Group": amalgam,
                        "Marker": marker,
                        "Mean": m,
                        "SD": sd,
                        "CI_Low": lo,
                        "CI_High": hi,
                        "Sample Size": len(sub),
                    })
    return pd.DataFrame(results)


def run_smoking_ttests(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]
    comparisons = [("None", "Low"), ("None", "Medium"), ("None", "High")]
    results = []
    for cycle, df_cycle in df.groupby("Cycle"):
        for smoke, df_smoke in df_cycle.groupby("SmokingStatus"):
            for var1, var2 in comparisons:
                g1 = df_smoke[df_smoke["Amalgam Group"] == var1]
                g2 = df_smoke[df_smoke["Amalgam Group"] == var2]
                for marker in markers:
                    g1_vals = g1[marker].dropna()
                    g2_vals = g2[marker].dropna()
                    if len(g1_vals) < 10 or len(g2_vals) < 10:
                        continue
                    stat, pval = ttest_ind(g1_vals, g2_vals, equal_var=False)
                    results.append({
                        "Cycle": cycle,
                        "SmokingStatus": smoke,
                        "Marker": marker,
                        "Comparison": f"{var1} vs {var2}",
                        "Group1 n": len(g1_vals),
                        "Group2 n": len(g2_vals),
                        "t-stat": round(stat, 3),
                        "p-value": round(pval, 5),
                        "Significant": pval < 0.05,
                    })
    return pd.DataFrame(results)


# Regression models with smoking covariates
MARKERS = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]


def _encode_covariates(df: pd.DataFrame) -> pd.DataFrame:
    covars = df[["amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1", "SmokingStatus"]].copy()
    covars = covars.apply(pd.to_numeric, errors="ignore")
    covars["female"] = (covars.pop("RIAGENDR") == 2).astype(int)
    race_dummies = pd.get_dummies(covars.pop("RIDRETH1").astype(int), prefix="race", drop_first=True)
    smoke_dummies = pd.get_dummies(covars.pop("SmokingStatus"), prefix="smoke", drop_first=True)
    covars = pd.concat([covars, race_dummies, smoke_dummies], axis=1)
    return covars.apply(pd.to_numeric, errors="coerce")


def fit_cubic_spline(df: pd.DataFrame, marker: str) -> sm.regression.linear_model.RegressionResultsWrapper:
    cols = ["time", marker, "amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1", "SmokingStatus"]
    data = df[cols].apply(pd.to_numeric, errors="ignore").dropna()
    y = data[marker].astype(float)
    covars = _encode_covariates(data)
    time_spline = dmatrix("bs(time, degree=3, df=4, include_intercept=False)", {"time": data["time"]}, return_type="dataframe")
    X = pd.concat([time_spline, covars], axis=1).astype(float)
    X = sm.add_constant(X)
    return sm.OLS(y, X).fit()


def fit_logistic(df: pd.DataFrame, marker: str) -> sm.discrete.discrete_model.BinaryResultsWrapper | None:
    cols = ["time", marker, "amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1", "SmokingStatus"]
    data = df[cols].apply(pd.to_numeric, errors="ignore").dropna()
    if data.empty:
        return None
    median = data[marker].median()
    data["binary"] = (data[marker] > median).astype(int)
    covars = _encode_covariates(data)
    covars["time"] = data["time"]
    X = sm.add_constant(covars.astype(float))
    try:
        return sm.Logit(data["binary"], X).fit(disp=False)
    except Exception:
        return None


def run_models(df: pd.DataFrame, out_dir: str) -> None:
    df = df.assign(time=df["Cycle"].str.slice(0, 4).astype(int)).copy()
    cubic_coeffs: dict[str, pd.Series] = {}
    cubic_pvals: dict[str, pd.Series] = {}
    log_coeffs: dict[str, pd.Series] = {}
    log_pvals: dict[str, pd.Series] = {}
    for marker in MARKERS:
        c_model = fit_cubic_spline(df, marker)
        cubic_coeffs[marker] = c_model.params
        cubic_pvals[marker] = c_model.pvalues
        l_model = fit_logistic(df, marker)
        if l_model is not None:
            log_coeffs[marker] = l_model.params
            log_pvals[marker] = l_model.pvalues
    pd.DataFrame(cubic_coeffs).T.to_csv(os.path.join(out_dir, "smoke_cubic_spline_coeffs.csv"))
    pd.DataFrame(cubic_pvals).T.to_csv(os.path.join(out_dir, "smoke_cubic_spline_pvalues.csv"))
    pd.DataFrame(log_coeffs).T.to_csv(os.path.join(out_dir, "smoke_logistic_coeffs.csv"))
    pd.DataFrame(log_pvals).T.to_csv(os.path.join(out_dir, "smoke_logistic_pvalues.csv"))


def main() -> None:
    df = process_with_smoking()
    out_dir = "smoke"
    os.makedirs(out_dir, exist_ok=True)
    if df.empty or "Cycle" not in df.columns:
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoking_desc_stat.csv"), index=False)
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoke_ttest.csv"), index=False)
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoke_cubic_spline_coeffs.csv"), index=False)
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoke_cubic_spline_pvalues.csv"), index=False)
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoke_logistic_coeffs.csv"), index=False)
        pd.DataFrame().to_csv(os.path.join(out_dir, "smoke_logistic_pvalues.csv"), index=False)
        return
    desc = compute_smoking_descriptive(df)
    desc.to_csv(os.path.join(out_dir, "smoking_desc_stat.csv"), index=False)
    ttests = run_smoking_ttests(df)
    ttests.to_csv(os.path.join(out_dir, "smoke_ttest.csv"), index=False)
    run_models(df, out_dir)


if __name__ == "__main__":
    main()
