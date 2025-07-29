import os
import pandas as pd
import matplotlib.pyplot as plt

from descriptive_stats import categorize_amalgam


def main():
    df = pd.read_csv("combined_dataset.csv")
    df["Amalgam Group"] = df["amalgam_surfaces"].apply(categorize_amalgam)
    markers = ["NLR", "MLR", "PLR", "SII"]
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    for cycle, df_cycle in df.groupby("Cycle"):
        for marker in markers:
            plt.figure(figsize=(8, 6))
            df_box = df_cycle[["Amalgam Group", marker]].dropna()
            if df_box.empty:
                plt.close()
                continue
            df_box.boxplot(column=marker, by="Amalgam Group")
            plt.title(f"{marker} by Amalgam Group - {cycle}")
            plt.suptitle("")
            plt.xlabel("Amalgam Group")
            plt.ylabel(marker)
            plt.tight_layout()
            fname = f"boxplot_{marker}_{cycle.replace('-', '')}.png"
            plt.savefig(os.path.join(out_dir, fname))
            plt.close('all')


if __name__ == "__main__":
    main()
