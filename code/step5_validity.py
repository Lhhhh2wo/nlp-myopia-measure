# -*- coding: utf-8 -*-
"""
第五步：信效度检验（Reliability & Validity）
--------------------------------------------
按课件第 19 页四类效度：
1) 聚合效度：与替代口径（对数命中频数）的 Pearson 相关
2) 区分效度：与"不该相关"的变量（企业规模 Size）的相关应显著更低
3) 条件均值检验：按测度高低分组，RD_Intensity 均值应单调递减
4) 预测效度：ShortTerm_Ratio -> RD_Intensity 的 OLS 回归（HC1 稳健标准误）
输出：output/results/validity_report.json、ols_results.txt
"""
import os
import csv
import json
import math

from stats_utils import pearsonr, ols_hc1, steiger_z

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(BASE, "output", "results", "measure_panel.csv")
OUT_JSON = os.path.join(BASE, "output", "results", "validity_report.json")
OUT_TXT = os.path.join(BASE, "output", "results", "ols_results.txt")


def main():
    with open(PANEL, encoding="utf-8") as f:
        df = list(csv.DictReader(f))
    for r in df:
        r["year"] = int(r["year"])
        for k in ("ShortTerm_Ratio", "RD_Intensity", "Size", "Lev", "ROA", "n_hits"):
            r[k] = float(r[k])
        r["SOE"] = int(r["SOE"])

    n = len(df)
    st = [r["ShortTerm_Ratio"] for r in df]

    # ---------- 聚合效度：替代口径（对数命中频数） ----------
    alt = [math.log1p(r["n_hits"]) * 10 for r in df]
    r_conv, p_conv = pearsonr(st, alt)

    # ---------- 区分效度：与公司规模的相关（应接近 0 且显著更低） ----------
    size = [r["Size"] for r in df]
    r_disc, p_disc = pearsonr(st, size)
    z = steiger_z(r_conv, r_disc, n)

    # ---------- 条件均值检验：按测度四分位分组 ----------
    srt = sorted(df, key=lambda r: r["ShortTerm_Ratio"])
    q = n // 4
    labels = ["Q1(低)", "Q2", "Q3", "Q4(高)"]
    group_means = {}
    for gi, lab in enumerate(labels):
        lo, hi = gi * q, (gi + 1) * q if gi < 3 else n
        group_means[lab] = round(sum(r["RD_Intensity"] for r in srt[lo:hi]) / (hi - lo), 4)

    # ---------- 预测效度：OLS 回归（含年度虚拟变量，HC1 稳健标准误） ----------
    names = ["const", "ShortTerm_Ratio", "Size", "Lev", "ROA", "SOE", "Y2022", "Y2023"]
    X, y = [], []
    for r in df:
        X.append([1.0, r["ShortTerm_Ratio"], r["Size"], r["Lev"],
                  r["ROA"], float(r["SOE"]),
                  1.0 if r["year"] == 2022 else 0.0,
                  1.0 if r["year"] == 2023 else 0.0])
        y.append(r["RD_Intensity"])
    model = ols_hc1(y, X, names)
    b, se, t, p = model.param("ShortTerm_Ratio")

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(model.summary_text(
            "RD_Intensity ~ ShortTerm_Ratio + Size + Lev + ROA + SOE + 年度虚拟变量"))

    report = {
        "n_obs": n,
        "n_firms": len({r["code"] for r in df}),
        "convergent_validity": {"pearson_r": round(r_conv, 4),
                                 "p_value": float(f"{p_conv:.2e}"),
                                 "note": "与替代口径（对数命中频数口径）的相关"},
        "discriminant_validity": {"pearson_r_with_size": round(r_disc, 4),
                                   "p_value": round(p_disc, 4),
                                   "steiger_z_vs_convergent": round(z, 2),
                                   "note": "与规模的低相关 + 与聚合口径的显著差异"},
        "conditional_means": group_means,
        "ols": {"beta_ShortTerm_Ratio": round(b, 4), "se_HC1": round(se, 4),
                 "t_value": round(t, 3), "p_value": float(f"{p:.2e}"),
                 "r_squared": round(model.rsquared, 4), "n": n},
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[step5] 信效度报告 -> {OUT_JSON}\n回归明细 -> {OUT_TXT}")


if __name__ == "__main__":
    main()
