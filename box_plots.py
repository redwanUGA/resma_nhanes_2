import os
import re

import pandas as pd
import matplotlib.pyplot as plt

from descriptive_stats import categorize_amalgam


def slugify(value: str) -> str:
    """Simple slugify helper for file names."""
    return re.sub(r"[^A-Za-z0-9]+", "_", value)


def main():
    df = pd.read_csv("combined_dataset.csv")
    df["Amalgam Group"] = df["amalgam_surfaces"].apply(categorize_amalgam)
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    try:
        ttest_df = pd.read_csv("ttest_results.csv")
    except FileNotFoundError:
        print("ttest_results.csv not found, no plots created")
        return

    ttest_sig = ttest_df[ttest_df["Significant"]]
    if ttest_sig.empty:
        print("No significant comparisons found")
        return

    for _, row in ttest_sig.iterrows():
        cycle = row["Cycle"]
        strata = row["Strata"]
        group_val = row["Group"]
        marker = row["Marker"]
        comp_groups = row["Comparison"].split(" vs ")

        df_sub = df[(df["Cycle"] == cycle) & (df[strata] == group_val)]
        df_box = df_sub[df_sub["Amalgam Group"].isin(comp_groups)][
            ["Amalgam Group", marker]
        ].dropna()
        if df_box.empty:
            continue

        plt.figure(figsize=(8, 6))
        df_box.boxplot(column=marker, by="Amalgam Group")
        title = (
            f"{marker} - {cycle} - {strata}: {group_val} ({row['Comparison']})"
        )
        plt.title(title)
        plt.suptitle("")
        plt.xlabel("Amalgam Group")
        plt.ylabel(marker)
        plt.tight_layout()
        fname_parts = [
            "sig_boxplot",
            slugify(marker),
            slugify(cycle),
            slugify(strata),
            slugify(str(group_val)),
            slugify(row["Comparison"]),
        ]
        fname = "_".join(fname_parts) + ".png"
        plt.savefig(os.path.join(out_dir, fname))
        plt.close("all")


if __name__ == "__main__":
    main()
