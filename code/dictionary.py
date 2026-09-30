# -*- coding: utf-8 -*-
"""
短期视域（管理者短视）词典
构建方式：参考胡楠等（2021，《管理世界》）"短期视域"词典的构建思路，
以行为经济学短期视域理论为依据，由人工筛选并结合预实验语料多轮校验，
最终确定 43 个短期导向词汇。仅用于教学预演论文的可复现演示。
"""
DICTIONARY = [
    "短期", "尽快", "立刻", "马上", "赶紧", "急切", "迫切", "急于",
    "眼下", "眼前", "当下", "近期", "本季度", "今年内", "应急", "权宜",
    "速成", "速胜", "立竿见影", "见效快", "快速见效", "立见成效",
    "抢抓", "抢占", "抢先", "即刻", "当即", "随即",
    "短期利益", "短期回报", "短期业绩", "短期收益", "当期收益",
    "急功近利", "急于求成", "速战速决", "只争朝夕", "快马加鞭",
    "突飞猛进", "大干快上", "追求速度", "吹糠见米", "事半功倍",
]

if __name__ == "__main__":
    import io, os
    path = os.path.join(os.path.dirname(__file__), "..", "output", "dictionary", "short_term_dictionary.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(DICTIONARY))
    print(f"词典已导出：{path}，共 {len(DICTIONARY)} 个词")
