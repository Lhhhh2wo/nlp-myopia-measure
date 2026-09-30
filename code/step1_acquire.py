# -*- coding: utf-8 -*-
"""
第一步：语料获取（Corpus Acquisition）
-------------------------------------
支持两种模式：
1) real     ：将真实年报 MD&A 纯文本放入 data/raw/（命名规范：
              {股票代码}_{年份}.txt，如 000001_2022.txt），本脚本直接读取整理。
2) simulate ：若 data/raw/ 为空，则生成一份"模拟语料库"用于流程演示
              （60 家公司 x 2021-2023 三年 = 180 份 MD&A 文档），
              生成逻辑内嵌企业异质性，保证测度具有真实的面板结构。

输出：data/corpus_index.csv（语料清单索引）
"""
import os
import re
import csv
import random
import math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
CORPUS_DIR = os.path.join(BASE, "data", "corpus")
INDEX_PATH = os.path.join(BASE, "data", "corpus_index.csv")

random.seed(42)

# ---------- 模拟语料的句式模板池 ----------
SHORT_TPL = [
    "公司全力冲刺{target}，力求尽快实现业绩突破。",
    "管理层强调要马上落实{dept}的整改，立刻见效。",
    "公司对{biz}业务急于求成，要求本季度见效快。",
    "为抢占市场份额，公司抢抓机遇迅速铺开{biz}渠道。",
    "董事会要求各事业部快马加鞭推进{proj}项目，只争朝夕。",
    "公司追求速度优先，希望在眼前的一年内实现短期收益翻番。",
    "面对竞争压力，公司当机立断，即刻启动{proj}专项。",
    "管理层关注短期业绩考核，要求{dept}当期收益不得下滑。",
    "公司急功近利倾向有所显现，短期内追求立竿见影的回报。",
    "为完成年度目标，公司要求各部门赶紧推进{proj}落地。",
    "公司在{biz}领域力求速战速决，尽快形成收入规模。",
    "管理层表示要以只争朝夕的姿态，眼下优先保{target}。",
]

NEUTRAL_TPL = [
    "报告期内，公司围绕既定战略稳步推进各项经营计划。",
    "公司持续完善治理结构，提升规范化运作水平。",
    "报告期内公司实现营业收入{rev}亿元，同比增长{g}%。",
    "公司坚持长期主义理念，持续加大研发投入与人才培养。",
    "公司深耕{biz}领域，注重技术创新与品牌建设。",
    "管理层认为行业竞争格局正在重塑，公司将动态优化产品结构。",
    "公司高度重视环境、社会与治理（ESG）相关工作。",
    "报告期内，公司现金流状况良好，资产负债结构保持稳健。",
    "公司推进数字化转型，信息化建设取得阶段性成果。",
    "公司严格遵守法律法规，规范信息披露，保障股东权益。",
    "公司立足长远，布局{proj}等前瞻性业务方向。",
    "报告期内公司获得授权专利{pat}项，研发体系日趋完善。",
    "公司深化渠道建设，与核心客户建立长期稳定的合作关系。",
    "公司关注宏观经济与政策变化，及时评估相关风险敞口。",
]

DEPT = ["营销", "生产", "供应链", "研发", "运营"]
BIZ = ["电商", "云计算", "新能源", "智能制造", "大健康", "跨境贸易"]
PROJ = ["智慧园区", "数字化中台", "产能扩建", "海外基地", "渠道下沉"]
TARGET = ["年度经营目标", "销售任务", "利润指标", "市场份额目标"]


def _fill(tpl):
    return tpl.format(
        dept=random.choice(DEPT), biz=random.choice(BIZ),
        proj=random.choice(PROJ), target=random.choice(TARGET),
        rev=round(random.uniform(8, 320), 1), g=round(random.uniform(-8, 35), 1),
        pat=random.randint(3, 120),
    )


def simulate_corpus(n_firms=60, years=(2021, 2022, 2023)):
    """生成模拟 MD&A 语料：企业隐含短视倾向 mu_i 决定短期句式占比。"""
    os.makedirs(CORPUS_DIR, exist_ok=True)
    codes = [f"{i:06d}" for i in random.sample(range(1, 999999), n_firms)]
    mu = [random.gauss(0, 1) for _ in codes]      # 企业层面异质性
    index = []
    for k, code in enumerate(codes):
        for year in years:
            p_short = 1 / (1 + math.exp(-(0.6 * mu[k] + random.gauss(0, 0.5))))
            n_sent = random.randint(18, 32)
            sents = []
            for _ in range(n_sent):
                if random.random() < 0.08 + 0.30 * p_short:
                    sents.append(_fill(random.choice(SHORT_TPL)))
                else:
                    sents.append(_fill(random.choice(NEUTRAL_TPL)))
            text = "".join(sents)
            fname = f"{code}_{year}.txt"
            with open(os.path.join(CORPUS_DIR, fname), "w", encoding="utf-8") as f:
                f.write(text)
            index.append({"code": code, "year": year, "file": fname,
                          "source": "simulated_corpora_v1"})
    return index


def load_real_corpus():
    index = []
    for fname in sorted(os.listdir(RAW_DIR)):
        m = re.match(r"^(\d{6})_(\d{4})\.txt$", fname)
        if not m:
            continue
        os.makedirs(CORPUS_DIR, exist_ok=True)
        with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
            text = f.read()
        # 简单去页眉页脚（真实 PDF 解析建议使用 PyMuPDF，见 README）
        text = re.sub(r"第\s*\d+\s*页", "", text)
        with open(os.path.join(CORPUS_DIR, fname), "w", encoding="utf-8") as f:
            f.write(text)
        index.append({"code": m.group(1), "year": int(m.group(2)),
                      "file": fname, "source": "cninfo_annual_report"})
    return index


def main():
    if os.listdir(RAW_DIR):
        print("[step1] 检测到 data/raw/ 下有真实语料，按真实模式处理")
        index = load_real_corpus()
    else:
        print("[step1] data/raw/ 为空，生成模拟语料库（60 家公司 x 3 年）")
        index = simulate_corpus()
    with open(INDEX_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "year", "file", "source"])
        w.writeheader()
        w.writerows(index)
    print(f"[step1] 语料清单已写入 {INDEX_PATH}，共 {len(index)} 份文档")


if __name__ == "__main__":
    main()
