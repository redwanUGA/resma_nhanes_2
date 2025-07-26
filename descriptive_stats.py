import os
import numpy as np
import pandas as pd
import pyreadstat

CBC_DEMO_DENTAL_FILES = {
    "1999-2000": ("L40_0.xpt", "DEMO.xpt", "OHXDENT.xpt"),
    "2001-2002": ("L25_B.xpt", "DEMO_B.xpt", "OHXDEN_B.xpt"),
    "2003-2004": ("L25_C.xpt", "DEMO_C.xpt", "OHXDEN_C.xpt"),
    "2005-2006": ("CBC_D.xpt", "DEMO_D.xpt", "OHXDEN_D.xpt"),
    "2007-2008": ("CBC_E.xpt", "DEMO_E.xpt", "OHXDEN_E.xpt"),
    "2009-2010": ("CBC_F.xpt", "DEMO_F.xpt", "OHXDEN_F.xpt"),
    "2011-2012": ("CBC_G.xpt", "DEMO_G.xpt", "OHXDEN_G.xpt"),
    "2013-2014": ("CBC_H.xpt", "DEMO_H.xpt", "OHXDEN_H.xpt"),
    "2015-2016": ("CBC_I.xpt", "DEMO_I.xpt", "OHXDEN_I.xpt"),
    "2017-2018": ("CBC_J.xpt", "DEMO_J.xpt", "OHXDEN_J.xpt"),
}


def count_amalgam_surfaces(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in df.columns if c.startswith("OHX") and c.endswith(("TC", "FS", "FT"))]
    df["amalgam_surfaces"] = (df[cols] == 2).sum(axis=1)
    return df[["SEQN", "amalgam_surfaces"]]


def weighted_stats(series: pd.Series, weights: pd.Series):
    try:
        mean = np.average(series, weights=weights)
        variance = np.average((series - mean) ** 2, weights=weights)
    except Exception:
        mean = series.mean()
        variance = series.var()
    std = np.sqrt(variance)
    se = std / np.sqrt(len(series))
    return round(mean, 3), round(std, 3), round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)


def process_cycles(data_dir: str = "nhanes_data"):
    df_all = []
    all_summaries = []
    for cycle, (cbc_file, demo_file, dental_file) in CBC_DEMO_DENTAL_FILES.items():
        try:
            cbc = pyreadstat.read_xport(os.path.join(data_dir, cbc_file))[0]
            demo = pyreadstat.read_xport(os.path.join(data_dir, demo_file))[0]
            dental = pyreadstat.read_xport(os.path.join(data_dir, dental_file))[0]
            dental = count_amalgam_surfaces(dental)

            df = demo.merge(cbc, on="SEQN").merge(dental, on="SEQN", how="left")
            df["Cycle"] = cycle

            df["WBC"] = df.get("LBXWBCSI")
            df["Neutro"] = df["WBC"] * df.get("LBXNEPCT", 0) / 100
            df["Lympho"] = df["WBC"] * df.get("LBXLYPCT", 0) / 100
            df["Mono"] = df["WBC"] * df.get("LBXMOPCT", 0) / 100
            df["Platelets"] = df.get("LBXPLTSI")

            df["NLR"] = df["Neutro"] / df["Lympho"]
            df["MLR"] = df["Mono"] / df["Lympho"]
            df["PLR"] = df["Platelets"] / df["Lympho"]
            df["SII"] = (df["Neutro"] * df["Platelets"]) / df["Lympho"]

            df_all.append(df)

            for marker in ["NLR", "MLR", "PLR", "SII"]:
                sub = df[[marker, "WTMEC2YR"]].dropna()
                if sub.empty:
                    continue
                m, sd, lo, hi = weighted_stats(sub[marker], sub["WTMEC2YR"])
                all_summaries.append({
                    "Cycle": cycle,
                    "Marker": marker,
                    "Mean": m,
                    "SD": sd,
                    "CI_Low": lo,
                    "CI_High": hi,
                    "Sample Size": len(sub),
                })
        except Exception as exc:
            print(f"Skipped {cycle}: {exc}")

    combined_df = pd.concat(df_all, ignore_index=True)
    summary_df = pd.DataFrame(all_summaries)
    return combined_df, summary_df


def categorize_amalgam(surfaces: float):
    if pd.isna(surfaces):
        return np.nan
    if surfaces == 0:
        return "None"
    if surfaces <= 5:
        return "Low"
    if surfaces <= 10:
        return "Medium"
    return "High"


if __name__ == "__main__":
    combined_df, summary_df = process_cycles()
    # Save full combined dataset and summary statistics to CSV files
    combined_df.to_csv("combined_dataset.csv", index=False)
    summary_df.to_csv("summary_statistics.csv", index=False)
    print(summary_df.head())
