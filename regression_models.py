"""Run cubic spline and logistic regression for NHANES markers."""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix

from descriptive_stats import process_cycles

MARKERS = ["NLR", "MLR", "PLR", "SII", "CRP", "BloodMercury"]


def _encode_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """Encode amalgam burden and demographic covariates.

    Parameters
    ----------
    df:
        DataFrame containing columns ``amalgam_surfaces``, ``RIDAGEYR``,
        ``RIAGENDR`` and ``RIDRETH1``.

    Returns
    -------
    DataFrame with numeric covariates and dummy variables ready for modeling.
    """
    covars = df[
        [
            "amalgam_surfaces",
            "RIDAGEYR",
            "RIAGENDR",
            "RIDRETH1",
        ]
    ].copy()
    # Sex: 1=male, 2=female -> female indicator
    covars["female"] = (covars.pop("RIAGENDR") == 2).astype(int)
    race_dummies = pd.get_dummies(covars.pop("RIDRETH1"), prefix="race", drop_first=True)
    covars = pd.concat([covars, race_dummies], axis=1)
    return covars


def fit_cubic_spline(df: pd.DataFrame, marker: str) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fit OLS with a cubic spline for time."""
    data = df[["time", marker, "amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1"]].dropna()
    y = data[marker]
    covars = _encode_covariates(data)
    time_spline = dmatrix(
        "bs(time, degree=3, df=4, include_intercept=False)",
        {"time": data["time"]},
        return_type="dataframe",
    )
    X = pd.concat([time_spline, covars], axis=1)
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return model


def fit_logistic(df: pd.DataFrame, marker: str) -> sm.discrete.discrete_model.BinaryResultsWrapper | None:
    """Fit logistic regression with marker dichotomized at its median.

    Returns ``None`` if the model fails to converge.
    """
    data = df[["time", marker, "amalgam_surfaces", "RIDAGEYR", "RIAGENDR", "RIDRETH1"]].dropna()
    if data.empty:
        return None
    median = data[marker].median()
    data["binary"] = (data[marker] > median).astype(int)
    covars = _encode_covariates(data)
    covars["time"] = data["time"]
    X = sm.add_constant(covars)
    try:
        model = sm.Logit(data["binary"], X).fit(disp=False)
    except Exception as exc:  # pragma: no cover - handle convergence issues
        print(f"Logistic regression failed for {marker}: {exc}")
        return None
    return model


def run_models() -> None:
    """Run regression models for each marker and save results to CSV files."""
    df, _ = process_cycles()
    # Approximate a time variable from the survey cycle start year
    df["time"] = df["Cycle"].str.slice(0, 4).astype(int)

    cubic_coeffs: dict[str, pd.Series] = {}
    cubic_pvals: dict[str, pd.Series] = {}
    log_coeffs: dict[str, pd.Series] = {}
    log_pvals: dict[str, pd.Series] = {}

    for marker in MARKERS:
        cubic_model = fit_cubic_spline(df, marker)
        cubic_coeffs[marker] = cubic_model.params
        cubic_pvals[marker] = cubic_model.pvalues

        log_model = fit_logistic(df, marker)
        if log_model is not None:
            log_coeffs[marker] = log_model.params
            log_pvals[marker] = log_model.pvalues

    pd.DataFrame(cubic_coeffs).T.to_csv("cubic_spline_coeffs.csv")
    pd.DataFrame(cubic_pvals).T.to_csv("cubic_spline_pvalues.csv")
    pd.DataFrame(log_coeffs).T.to_csv("logistic_coeffs.csv")
    pd.DataFrame(log_pvals).T.to_csv("logistic_pvalues.csv")


if __name__ == "__main__":
    run_models()
