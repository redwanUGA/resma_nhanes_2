import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri

from descriptive_stats import process_cycles, categorize_amalgam

pandas2ri.activate()


def prepare_groups(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Amalgam Group"] = df["amalgam_surfaces"].apply(categorize_amalgam)
    df["Gender"] = df["RIAGENDR"].replace({1: "Male", 2: "Female"})
    df["Race"] = df["RIDRETH1"].replace({
        1: "Mexican American",
        2: "Other Hispanic",
        3: "Non-Hispanic White",
        4: "Non-Hispanic Black",
        5: "Other Race/Multi-Racial",
    })
    df["AgeGroup"] = pd.cut(
        df["RIDAGEYR"],
        bins=[0, 19, 39, 59, np.inf],
        labels=["0–19", "20–39", "40–59", "60+"],
        right=True,
    )
    return df


def run_t_tests(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII"]
    comparisons = [("None", "Low"), ("None", "Medium"), ("None", "High")]
    strata_vars = ["Gender", "Race", "AgeGroup"]

    results = []
    for cycle, df_cycle in df.groupby("Cycle"):
        for strata in strata_vars:
            for strata_value, df_sub in df_cycle.groupby(strata):
                if pd.isna(strata_value):
                    continue
                for var1, var2 in comparisons:
                    g1 = df_sub[df_sub["Amalgam Group"] == var1]
                    g2 = df_sub[df_sub["Amalgam Group"] == var2]
                    for marker in markers:
                        g1_vals = g1[marker].dropna()
                        g2_vals = g2[marker].dropna()
                        if len(g1_vals) < 10 or len(g2_vals) < 10:
                            continue
                        stat, pval = ttest_ind(g1_vals, g2_vals, equal_var=False)
                        results.append({
                            "Cycle": cycle,
                            "Strata": strata,
                            "Group": strata_value,
                            "Marker": marker,
                            "Comparison": f"{var1} vs {var2}",
                            "Group1 n": len(g1_vals),
                            "Group2 n": len(g2_vals),
                            "t-stat": round(stat, 3),
                            "p-value": round(pval, 5),
                            "Significant": pval < 0.05,
                        })
    return pd.DataFrame(results)


def survey_weighted_anova(df: pd.DataFrame) -> pd.DataFrame:
    markers = ["NLR", "MLR", "PLR", "SII"]
    cols = [
        "WTMEC2YR",
        "SDMVSTRA",
        "SDMVPSU",
        "Amalgam Group",
        "Cycle",
        "Gender",
        "Race",
        "AgeGroup",
    ] + markers
    df_model = df[cols].dropna()
    ro.globalenv["df_r"] = pandas2ri.py2rpy(df_model)

    ro.r("suppressMessages(library(survey))")
    ro.r("anova_all <- data.frame()")
    ro.r(
        """
cycles <- unique(df_r$Cycle)
markers <- c("NLR", "MLR", "PLR", "SII")
for (cy in cycles) {
  df_c <- subset(df_r, Cycle == cy)
  df_c$`Amalgam Group` <- factor(df_c$`Amalgam Group`, levels=c("None","Low","Medium","High"))
  df_c$Gender <- factor(df_c$Gender)
  df_c$Race <- factor(df_c$Race)
  df_c$AgeGroup <- factor(df_c$AgeGroup)
  if (length(unique(df_c$`Amalgam Group`)) < 2 ||
      length(unique(df_c$Gender)) < 2 ||
      length(unique(df_c$Race)) < 2 ||
      length(unique(df_c$AgeGroup)) < 2) next
  design <- svydesign(id=~SDMVPSU, strata=~SDMVSTRA, weights=~WTMEC2YR, data=df_c, nest=TRUE)
  for (m in markers) {
    form_str <- paste0(m, " ~ `Amalgam Group` + Gender + Race + AgeGroup")
    model <- svyglm(as.formula(form_str), design=design)
    for (term in c("Amalgam Group", "Gender", "Race", "AgeGroup")) {
      test <- regTermTest(model, as.formula(paste0("~`", term, "`")))
      fstat <- round(test$Ftest["value"], 3)
      pval <- round(test$p, 5)
      sig <- ifelse(pval < 0.05, TRUE, FALSE)
      anova_all <- rbind(anova_all, data.frame(Cycle=cy, Marker=m, Term=term, F_stat=fstat, p_value=pval, Significant=sig))
    }
  }
}
"""
    )
    return pandas2ri.rpy2py(ro.globalenv["anova_all"])


def main():
    combined, _ = process_cycles()
    combined = prepare_groups(combined)
    ttest_df = run_t_tests(combined)
    # Save t-test results to CSV
    ttest_df.to_csv("ttest_results.csv", index=False)
    print(ttest_df.head())
    # anova_df = survey_weighted_anova(combined)
    # anova_df.to_csv("anova_results.csv", index=False)
    # print(anova_df.head())


if __name__ == "__main__":
    main()
