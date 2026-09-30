# -*- coding: utf-8 -*-
"""
第三步 + 第四步：特征提取（词典法）与指标构建（Measure Construction）
--------------------------------------------------------------------
词典法测度公式（课件第 15 页）：
    ShortTerm_it = 词典命中词数_it / MD&A总词数_it * 100
分母采用"总词数"口径（决策一），等权计数（决策二），
变量命名 ShortTerm_Ratio（决策三）。

输出：
  output/results/measure_panel.csv  企业-年份面板（含模拟财务控制变量）
  output/results/hits_detail.csv    每份文档的命中明细（可复现留痕）
"""
import os
import csv
import random
import math

from stats_utils import pearsonr  # noqa: F401  (供后续稳健性脚本复用)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_DIR = os.path.join(BASE, "data", "tokens")
INDEX_PATH = os.path.join(BASE, "data", "corpus_index.csv")
DICT_PATH = os.path.join(BASE, "output", "dictionary", "short_term_dictionary.txt")
OUT_PANEL = os.path.join(BASE, "output", "results", "measure_panel.csv")
OUT_HITS = os.path.join(BASE, "output", "results", "hits_detail.csv")

random.seed(42)


def load_dictionary():
    with open(DICT_PATH, encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    if not words:
        from dictionary import DICTIONARY
        words = list(DICTIONARY)
    return set(words)


def main():
    dict_words = load_dictionary()
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = list(csv.DictReader(f))

    # ---------- 第三步：词典法特征提取 ----------
    # 企业隐含短视倾向（用于生成自洽的模拟财务变量，真实数据时直接读 CSMAR）
    latent = {row["code"]: random.gauss(0, 1) for row in index}
    rows, hits = [], []
    for row in index:
        with open(os.path.join(TOKEN_DIR, row["file"]), encoding="utf-8") as f:
            words = f.read().split()
        n_total = len(words)
        n_hits = sum(1 for w in words if w in dict_words)
        short_ratio = n_hits / n_total * 100 if n_total else 0.0
        rows.append({
            "code": row["code"], "year": row["year"],
            "n_words": n_total, "n_hits": n_hits,
            "ShortTerm_Ratio": round(short_ratio, 4),
        })
        hits.append({"code": row["code"], "year": row["year"],
                     "n_hits": n_hits, "n_words": n_total})

    # ---------- 第四步：指标构建 -> 企业-年份面板 ----------
    # 模拟财务控制变量与被解释变量（真实研究请替换为 CSMAR 数据）：
    # rd_intensity = 6.0 - 0.45*ShortTerm_Ratio + 控制变量效应 + 噪声
    for r in rows:
        mu = latent[r["code"]]
        st = r["ShortTerm_Ratio"]
        size = round(random.gauss(22.3 + 0.15 * mu, 1.1), 3)      # ln 总资产
        lev = round(min(0.9, max(0.05, random.gauss(0.42, 0.15))), 3)
        roa = round(random.gauss(0.04 - 0.01 * mu, 0.05), 3)
        soe = 1 if random.random() < 0.35 else 0
        r["Size"] = size
        r["Lev"] = lev
        r["ROA"] = roa
        r["SOE"] = soe
        r["Industry"] = f"{random.choice('ABCDEFGH')}{random.randint(10, 99)}"
        r["RD_Intensity"] = round(
            6.0 - 0.45 * st + 0.6 * size / 22.3 + 0.8 * roa - 0.5 * lev
            - 0.3 * soe + 1.2 * mu / 10 + random.gauss(0, 1.2), 4)

    # 缩尾处理（Winsorize）：对 RD_Intensity 在 1% 和 99% 分位进行缩尾，
    # 消除极端值影响（与论文正文描述一致）
    rds = sorted(r["RD_Intensity"] for r in rows)
    def _pct(arr, p):
        k = (len(arr) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(arr) - 1)
        return arr[lo] + (arr[hi] - arr[lo]) * (k - lo)
    lo1, hi99 = _pct(rds, 0.01), _pct(rds, 0.99)
    for r in rows:
        r["RD_Intensity"] = round(min(max(r["RD_Intensity"], lo1), hi99), 4)

    os.makedirs(os.path.dirname(OUT_PANEL), exist_ok=True)
    cols = ["code", "year", "n_words", "n_hits", "ShortTerm_Ratio",
            "RD_Intensity", "Size", "Lev", "ROA", "SOE", "Industry"]
    with open(OUT_PANEL, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(OUT_HITS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "year", "n_hits", "n_words"])
        w.writeheader()
        w.writerows(hits)
    print(f"[step3-4] 面板已写入 {OUT_PANEL}（{len(rows)} 个企业-年度观测）")
    print(f"[step3-4] 词典规模 {len(dict_words)} 词；命中明细见 {OUT_HITS}")


if __name__ == "__main__":
    main()
