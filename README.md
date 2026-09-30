# 管理研究中的 NLP 测度构建：年报 MD&A 管理者短视测度（预演毕业论文配套仓库）

> 大连财经学院 · 大数据管理与应用专业 · 毕业论文方法预备课课后作业
> 论文题目（预演）：**《基于词典法的管理者短视测度构建及其对研发投入的影响研究——来自 A 股上市公司年报 MD&A 的证据》**

## 仓库结构

```
nlp-myopia-measure/
├── code/                       # 可复现代码（五步流水线）
│   ├── run_all.py              # 一键复现入口
│   ├── dictionary.py           # 短期视域词典（43 词）定义与导出
│   ├── step1_acquire.py        # ① 语料获取（支持真实年报 / 模拟语料）
│   ├── step2_preprocess.py     # ② 文本预处理（清洗 + jieba 分词 + 停用词）
│   ├── step3_4_measure.py      # ③④ 词典法特征提取 + 企业-年份面板构建
│   └── step5_validity.py       # ⑤ 信效度检验（聚合/区分/条件均值/预测效度 + OLS）
├── data/
│   ├── raw/                    # 放入真实年报 MD&A 文本（{代码}_{年份}.txt）
│   ├── corpus/                 # step1 输出的标准化语料库
│   ├── tokens/                 # step2 输出的分词结果
│   └── corpus_index.csv        # 语料清单索引（来源留痕）
├── output/
│   ├── dictionary/short_term_dictionary.txt
│   └── results/
│       ├── measure_panel.csv   # 企业-年份测度面板（最终测度结果表）
│       ├── hits_detail.csv     # 词典命中明细（留痕可查）
│       ├── validity_report.json# 信效度检验结果
│       └── ols_results.txt     # 回归分析完整输出
└── thesis/                     # 预演论文全文（Word + Markdown）
```

## 数据来源说明

| 文件 / 目录 | 来源与处理步骤 |
|---|---|
| `data/raw/` | 真实模式下放置年报 MD&A 纯文本，来源为巨潮资讯网（cninfo）年报 PDF，经 PyMuPDF 抽取正文后按 `{股票代码}_{年份}.txt` 命名 |
| `data/corpus/`（本次演示） | 因课程作业无数据库权限，本次演示使用**模拟语料库**：60 家公司 × 2021–2023 年 = 180 份 MD&A 文档，由 `step1_acquire.py` 按"企业隐含短视倾向"生成，用于跑通完整流程 |
| `output/results/measure_panel.csv` | 财务控制变量（Size/Lev/ROA/SOE/RD_Intensity）为**模拟数据**，真实研究中应替换为 CSMAR / Wind 数据库对应字段 |

## 复现步骤（3 条命令）

```bash
pip install -r requirements.txt
python code/run_all.py          # 一键跑完五步流水线
# 查看结果：output/results/measure_panel.csv 与 validity_report.json
```

## 五步流水线 ↔ 代码 ↔ 输出对照

| 步骤 | 脚本 | 关键库/函数 | 输出 |
|---|---|---|---|
| ① 语料获取 | `step1_acquire.py` | 内置生成器 / `open()` | `corpus_index.csv` |
| ② 文本预处理 | `step2_preprocess.py` | 正则清洗、`jieba.lcut`（精确模式）、停用词表 | `data/tokens/` |
| ③ 特征提取 | `step3_4_measure.py` | 词典法"盖章计数" | `hits_detail.csv` |
| ④ 指标构建 | `step3_4_measure.py` | `ShortTerm = 命中词数/总词数×100` | `measure_panel.csv` |
| ⑤ 信效度检验 | `step5_validity.py` | `scipy.pearsonr`、`statsmodels.ols`（HC1 稳健标准误） | `validity_report.json`、`ols_results.txt` |

## 测度公式

$$ShortTerm_{it} = \frac{\sum_{w \in D} n_{w,it}}{N_{it}} \times 100$$

其中 $D$ 为 43 个短期视域词典词（见 `output/dictionary/short_term_dictionary.txt`），
$n_{w,it}$ 为词 $w$ 在公司 $i$ 第 $t$ 年 MD&A 分词结果中的出现次数，$N_{it}$ 为该文档总词数。

## 声明

本仓库为**毕业论文方法预备课的预演作业**，用于完整演练"NLP 测度构建五步流程"，
语料与财务数据均为演示用模拟数据；接通真实数据（年报文本 + CSMAR）后，
同一套代码可直接复用于正式研究。
