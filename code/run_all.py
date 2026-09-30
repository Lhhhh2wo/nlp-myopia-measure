# -*- coding: utf-8 -*-
"""
一键复现：python run_all.py
依次执行五步流水线：语料获取 -> 预处理 -> 特征提取/指标构建 -> 信效度检验
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("导出短期视域词典", "dictionary.py"),
    ("第一步 语料获取", "step1_acquire.py"),
    ("第二步 文本预处理", "step2_preprocess.py"),
    ("第三四步 特征提取与指标构建", "step3_4_measure.py"),
    ("第五步 信效度检验", "step5_validity.py"),
]

for desc, script in STEPS:
    print(f"\n========== {desc} ({script}) ==========")
    r = subprocess.run([sys.executable, os.path.join(HERE, script)])
    if r.returncode != 0:
        sys.exit(f"[run_all] {script} 执行失败，流程终止")
print("\n[run_all] 五步流水线全部执行完毕 ✅")
