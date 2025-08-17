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

# Mapping of survey cycles to Alcohol Use Questionnaire files
ALCOHOL_FILES = {
    "1999-2000": "ALQ.xpt",
    "2001-2002": "ALQ_B.xpt",
    "2003-2004": "ALQ_C.xpt",
    "2005-2006": "ALQ_D.xpt",
    "2007-2008": "ALQ_E.xpt",
    "2009-2010": "ALQ_F.xpt",
    "2011-2012": "ALQ_G.xpt",
    "2013-2014": "ALQ_H.xpt",
    "2015-2016": "ALQ_I.xpt",
    "2017-2018": "ALQ_J.xpt",
}

REQUIRED_LABELS = ["CBC", "Demographics", "Dental", "CRP", "Mercury", "Alcohol"]


def cycles_with_alcohol(log_path: str = "download_log.csv") -> set[str]:
    """Return cycles with all required files including alcohol questionnaire."""
    if not os.path.exists(log_path):
        alt = os.path.join("national_stats", "download_log.csv")
        if os.path.exists(alt):
            log_path = alt
        else:
            return set(ALCOHOL_FILES.keys())
    log_df = pd.read_csv(log_path)
    valid: set[str] = set()
    for cycle, grp in log_df.groupby("Cycle"):
        statuses = {lbl: grp[grp["Label"] == lbl]["Status"].iloc[0] for lbl in grp["Label"].unique()}
        if all(statuses.get(lbl) == "success" for lbl in REQUIRED_LABELS):
            valid.add(cycle)
    return valid


def load_alcohol(data_dir: str, cycles: set[str]) -> pd.DataFrame:
    """Load ALQ101 and ALQ120Q for the given cycles."""
    frames: list[pd.DataFrame] = []
    for cycle in cycles:
        fname = ALCOHOL_FILES.get(cycle)
        if not fname:
            continue
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            continue
        alq, _ = pyreadstat.read_xport(fpath)
        cols = [c for c in ["SEQN", "ALQ101", "ALQ120Q"] if c in alq.columns]
        alq = alq[cols]
        alq["Cycle"] = cycle
        frames.append(alq)
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["SEQN", "ALQ101", "ALQ120Q", "Cycle"])


def classify_drinking(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _classify(row):
        if row.get("ALQ101") == 2:
            return "Lifetime Abstainer"
        if row.get("ALQ101") == 1:
            val = row.get("ALQ120Q")
            if val == 0:
                return "Former Drinker"
            if pd.notna(val) and val > 0:
                return "Current Drinker"
        return np.nan

    df["DrinkingStatus"] = df.apply(_classify, axis=1)
    df["Amalgam Group"] = df["amalgam_surfaces"].apply(categorize_amalgam)
    return df


def process_with_drinking(data_dir: str = "nhanes_data") -> pd.DataFrame:
    base_df, _ = process_cycles(data_dir)
    if base_df.empty:
        return base_df
    valid_cycles = cycles_with_alcohol()
    base_df = base_df[base_df["Cycle"].isin(valid_cycles)].copy()
    alq_df = load_alcohol(data_dir, valid_cycles)
    combined = base_df.merge(alq_df, on=["SEQN", "Cycle"], how="left")
    combined = classify_drinking(combined)
    return combined


def compute_drinking_descriptive(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]
    results = []
    for cycle, df_cycle in df.groupby("Cycle"):
        for drink, df_drink in df_cycle.groupby("DrinkingStatus"):
            for amalgam, df_group in df_drink.groupby("Amalgam Group"):
                for marker in markers:
                    sub = df_group[[marker, "WTMEC2YR"]].dropna()
                    if sub.empty:
                        continue
                    m, sd, lo, hi = weighted_stats(sub[marker], sub["WTMEC2YR"])
                    results.append(
                        {
                            "Cycle": cycle,
                            "DrinkingStatus": drink,
                            "Amalgam Group": amalgam,
                            "Marker": marker,
                            "Mean": m,
                            "SD": sd,
                            "CI_Low": lo,
                            "CI_High": hi,
                            "Sample Size": len(sub),
                        }
                    )
    return pd.DataFrame(results)


def run_drinking_ttests(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]
    comparisons = [("None", "Low"), ("None", "Medium"), ("None", "High")]
    results = []
    for cycle, df_cycle in df.groupby("Cycle"):
        for drink, df_drink in df_cycle.groupby("DrinkingStatus"):
            for var1, var2 in comparisons:
                g1 = df_drink[df_drink["Amalgam Group"] == var1]
                g2 = df_drink[df_drink["Amalgam Group"] == var2]
                for marker in markers:
                    g1_vals = g1[marker].dropna()
                    g2_vals = g2[marker].dropna()
                    if len(g1_vals) < 10 or len(g2_vals) < 10:
                        continue
                    stat, pval = ttest_ind(g1_vals, g2_vals, equal_var=False)
                    results.append(
                        {
                            "Cycle": cycle,
                            "DrinkingStatus": drink,
                            "Marker": marker,
                            "Comparison": f"{var1} vs {var2}",
                            "Group1 n": len(g1_vals),
                            "Group2 n": len(g2_vals),
                            "t-stat": round(stat, 3),
                            "p-value": round(pval, 5),
                            "Significant": pval < 0.05,
                        }
                    )
    return pd.DataFrame(results)


# Regression models with drinking covariates
MARKERS = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]


def _encode_covariates(df: pd.DataFrame) -> pd.DataFrame:
    covars = df[
        ["amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1", "DrinkingStatus"]
    ].copy()
    covars = covars.apply(pd.to_numeric, errors="ignore")
    covars["female"] = (covars.pop("RIAGENDR") == 2).astype(int)
    race_dummies = pd.get_dummies(
        covars.pop("RIDRETH1").astype(int), prefix="race", drop_first=True
    )
    drink_dummies = pd.get_dummies(
        covars.pop("DrinkingStatus"), prefix="drink", drop_first=True
    )
    covars = pd.concat([covars, race_dummies, drink_dummies], axis=1)
    return covars.apply(pd.to_numeric, errors="coerce")


def fit_cubic_spline(
    df: pd.DataFrame, marker: str
) -> sm.regression.linear_model.RegressionResultsWrapper:
    cols = [
        "time",
        marker,
        "amalgam_surfaces",
        "RIDAGEYR",
        "RIAGENDR",
        "RIDRETH1",
        "DrinkingStatus",
    ]
    data = df[cols].apply(pd.to_numeric, errors="ignore").dropna()
    y = data[marker].astype(float)
    covars = _encode_covariates(data)
    time_spline = dmatrix(
        "bs(time, degree=3, df=4, include_intercept=False)",
        {"time": data["time"]},
        return_type="dataframe",
    )
    X = pd.concat([time_spline, covars], axis=1).astype(float)
    X = sm.add_constant(X)
    return sm.OLS(y, X).fit()


def fit_logistic(
    df: pd.DataFrame, marker: str
) -> sm.discrete.discrete_model.BinaryResultsWrapper | None:
    cols = [
        "time",
        marker,
        "amalgam_surfaces",
        "RIDAGEYR",
        "RIAGENDR",
        "RIDRETH1",
        "DrinkingStatus",
    ]
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
    pd.DataFrame(cubic_coeffs).T.to_csv(
        os.path.join(out_dir, "drink_cubic_spline_coeffs.csv")
    )
    pd.DataFrame(cubic_pvals).T.to_csv(
        os.path.join(out_dir, "drink_cubic_spline_pvalues.csv")
    )
    pd.DataFrame(log_coeffs).T.to_csv(
        os.path.join(out_dir, "drink_logistic_coeffs.csv")
    )
    pd.DataFrame(log_pvals).T.to_csv(
        os.path.join(out_dir, "drink_logistic_pvalues.csv")
    )


def main() -> None:
    df = process_with_drinking()
    out_dir = "drink"
    os.makedirs(out_dir, exist_ok=True)
    if df.empty or "Cycle" not in df.columns:
        pd.DataFrame().to_csv(
            os.path.join(out_dir, "drinking_desc_stat.csv"), index=False
        )
        pd.DataFrame().to_csv(os.path.join(out_dir, "drink_ttest.csv"), index=False)
        pd.DataFrame().to_csv(
            os.path.join(out_dir, "drink_cubic_spline_coeffs.csv"), index=False
        )
        pd.DataFrame().to_csv(
            os.path.join(out_dir, "drink_cubic_spline_pvalues.csv"), index=False
        )
        pd.DataFrame().to_csv(
            os.path.join(out_dir, "drink_logistic_coeffs.csv"), index=False
        )
        pd.DataFrame().to_csv(
            os.path.join(out_dir, "drink_logistic_pvalues.csv"), index=False
        )
        return
    desc = compute_drinking_descriptive(df)
    desc.to_csv(os.path.join(out_dir, "drinking_desc_stat.csv"), index=False)
    ttests = run_drinking_ttests(df)
    ttests.to_csv(os.path.join(out_dir, "drink_ttest.csv"), index=False)
    run_models(df, out_dir)


if __name__ == "__main__":
    main()

