# -*- coding: utf-8 -*-
"""
stats_utils.py —— 纯标准库统计工具
为了把复现门槛降到最低（仅依赖 jieba），本文件用纯 Python 实现了：
  - Pearson 相关系数及 t 检验 p 值（含不完全 Beta 函数）
  - 多元 OLS（正规方程 + 高斯消元求逆）
  - HC1 异方差稳健标准误
  - R²、Steiger 检验
结果与 statsmodels/scipy 一致（回归示例已验证），但无需安装任何二进制依赖。
"""
import math


# ---------- 基础分布 ----------

def _betacf(a, b, x):
    """正则化不完全 Beta 函数的连分式（Lentz 算法）"""
    tiny, eps = 1e-30, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betainc(a, b, x):
    """正则化不完全 Beta 函数 I_x(a, b)"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln_beta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
               + a * math.log(x) + b * math.log(1 - x))
    front = math.exp(ln_beta)
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(ln_beta) * _betacf(b, a, 1 - x) / b


def t_sf_two_sided(t, df):
    """t 分布双侧 p 值"""
    if df <= 0:
        return float("nan")
    return _betainc(df / 2.0, 0.5, df / (df + t * t))


def pearsonr(x, y):
    """Pearson 相关系数及双侧 p 值（等价 scipy.stats.pearsonr）"""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    r = sxy / math.sqrt(sxx * syy)
    df = n - 2
    t = r * math.sqrt(df / max(1e-30, 1 - r * r))
    return r, t_sf_two_sided(abs(t), df)


# ---------- 线性代数 ----------

def mat_inverse(A):
    """高斯-约当消元求逆"""
    n = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-14:
            raise ValueError("矩阵接近奇异")
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
    return [row[n:] for row in M]


def mat_T(A):
    return [list(col) for col in zip(*A)]


def mat_mul(A, B):
    Bt = mat_T(B)
    return [[sum(a * b for a, b in zip(row, col)) for col in Bt] for row in A]


def mat_vec(A, v):
    return [sum(a * b for a, b in zip(row, v)) for row in A]


# ---------- OLS（含 HC1 稳健标准误） ----------

class OLSResult:
    def __init__(self, names, beta, se, tvalues, pvalues, r2, n, k):
        self.names, self.beta, self.se = names, beta, se
        self.tvalues, self.pvalues = tvalues, pvalues
        self.rsquared, self.nobs = r2, n
        self._k = k

    def param(self, name):
        i = self.names.index(name)
        return self.beta[i], self.se[i], self.tvalues[i], self.pvalues[i]

    def summary_text(self, formula):
        lines = [f"OLS 回归（HC1 稳健标准误）  被解释变量按公式：{formula}",
                 f"N = {self.nobs}   R-squared = {self.rsquared:.4f}", "-" * 78,
                 f"{'变量':<22}{'系数':>12}{'HC1标准误':>14}{'t值':>10}{'p值':>12}", "-" * 78]
        for i, nm in enumerate(self.names):
            lines.append(f"{nm:<22}{self.beta[i]:>12.4f}{self.se[i]:>14.4f}"
                         f"{self.tvalues[i]:>10.3f}{self.pvalues[i]:>12.4g}")
        lines.append("-" * 78)
        return "\n".join(lines)


def ols_hc1(y, X, names):
    """
    y: list[float] 因变量；X: list[list[float]] 设计矩阵（已含截距列）
    names: 与 X 列对应的名字。返回 OLSResult。
    beta = (X'X)^-1 X'y；Var(b) = n/(n-k) * (X'X)^-1 X' diag(e^2) X (X'X)^-1
    为避免量纲悬殊导致的数值精度损失，先将各列缩放到单位范数再计算，
    求得的系数与标准误再按原量纲缩放回去（残差对列缩放不变）。
    """
    n, k = len(y), len(X[0])
    d = [math.sqrt(sum(X[i][j] ** 2 for i in range(n))) for j in range(k)]
    Xs = [[row[j] / d[j] for j in range(k)] for row in X]
    Xt = mat_T(Xs)
    XtX = mat_mul(Xt, Xs)
    XtX_inv = mat_inverse(XtX)
    beta_s = mat_vec(XtX_inv, mat_vec(Xt, y))
    resid = [yi - sum(a * b for a, b in zip(xi, beta_s)) for xi, yi in zip(Xs, y)]
    ybar = sum(y) / n
    tss = sum((yi - ybar) ** 2 for yi in y)
    rss = sum(e * e for e in resid)
    r2 = 1 - rss / tss if tss > 0 else float("nan")
    # HC1 稳健方差：Var(b_i) = n/(n-k) * Σ_j (A_ij)^2 e_j^2，其中 A = (X'X)^-1 X'
    # 该逐行平方和形式天然非负，避免三明治乘法的大数相消误差
    A = mat_mul(XtX_inv, Xt)  # k x n
    scale = n / (n - k)
    se_s = [math.sqrt(scale * sum(A[i][j] ** 2 * resid[j] ** 2 for j in range(n)))
            for i in range(k)]
    # 缩放回原量纲
    beta = [beta_s[j] / d[j] for j in range(k)]
    se = [se_s[j] / d[j] for j in range(k)]
    tvals = [b / s if s > 0 else float("nan") for b, s in zip(beta, se)]
    pvals = [t_sf_two_sided(abs(t), n - k) for t in tvals]
    return OLSResult(names, beta, se, tvals, pvals, r2, n, k)


def steiger_z(r1, r2, n):
    """两个相关系数差异的 Steiger 检验（近似 z）"""
    den = math.sqrt(2 / (n - 3))
    return abs(math.atanh(r1) - math.atanh(r2)) / den
