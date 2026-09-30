# -*- coding: utf-8 -*-
"""
第二步：文本预处理（Preprocessing）
-----------------------------------
流水线：读取 -> 清洗（去页眉页脚/乱码/冗余空白）-> jieba 精确模式分词
        -> 去停用词（通用 + 财经领域自定义）
输出：data/tokens/{code}_{year}.txt（空格分隔的词序列）
"""
import os
import re
import csv
import jieba

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(BASE, "data", "corpus")
TOKEN_DIR = os.path.join(BASE, "data", "tokens")
INDEX_PATH = os.path.join(BASE, "data", "corpus_index.csv")
STOPWORDS_PATH = os.path.join(BASE, "data", "stopwords.txt")

# 通用停用词 + 财经文本领域停用词（课件第 14 页要点：
# 不能照搬通用表，需补充"同比/报告期"等领域高频虚词）
BASE_STOPWORDS = set("""的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好
这 那 与 及 其 等 为 以 于 而 或 并 将 已 仍 便 又 才 只 更 最 较 约 可 应 需 能 使 从 向 对 给 按 据 因
所 之 其 各 每 该 此 本 另 上述 以下 其中 之间 以及 同时 此外 另外 目前 报告 报告期内 公司 本公司 我们
情况 方面 工作 进行 开展 实施 推进 加强 提高 提升 不断 进一步 通过 依据 根据 按照 有关 相关 截至 同比
增长 下降 亿元 万元 % 。 ， 、 ； ： （ ） “ ” 年 月 日 个 项 元""".split())

FIN_STOPWORDS = set(["同比", "报告期", "报告期内", "经营计划", "相关方", "上述", "以下简称"])


def clean_text(text: str) -> str:
    """清洗：去页眉页脚残留、全角空格、重复空白与乱码标记。"""
    text = re.sub(r"第\s*\d+\s*页", "", text)
    text = re.sub(r"[\r\f\v]+", "", text)
    text = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9%\.，。；：、（）%\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_stopwords():
    sw = BASE_STOPWORDS | FIN_STOPWORDS
    if os.path.exists(STOPWORDS_PATH):
        with open(STOPWORDS_PATH, encoding="utf-8") as f:
            sw |= {line.strip() for line in f if line.strip()}
    return sw


def main():
    os.makedirs(TOKEN_DIR, exist_ok=True)
    stopwords = load_stopwords()
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = list(csv.DictReader(f))
    for row in index:
        with open(os.path.join(CORPUS_DIR, row["file"]), encoding="utf-8") as f:
            text = clean_text(f.read())
        # jieba 精确模式（课件第 14 页：搜索引擎模式会切碎专有名词）
        words = jieba.lcut(text)
        words = [w for w in words if w.strip() and w not in stopwords]
        with open(os.path.join(TOKEN_DIR, row["file"]), "w", encoding="utf-8") as f:
            f.write(" ".join(words))
    print(f"[step2] 预处理完成：{len(index)} 份文档 -> {TOKEN_DIR}")
    print(f"[step2] 停用词表规模：{len(stopwords)}")


if __name__ == "__main__":
    main()
