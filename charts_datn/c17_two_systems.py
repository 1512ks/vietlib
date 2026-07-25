"""
Biểu đồ #17 — So sánh hai hệ trên các chỉ số CẢ HAI đều đo được.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles, BAR_W_GROUP

metrics = ["nDCG@5", "MRR@5", "OOS Recall", "Citation rate"]
sample = [0.842, 0.966, 1.000, 1.000]
main   = [0.866, 0.919, 0.714, 0.860]

x = np.arange(len(metrics)); w = BAR_W_GROUP; off = w/2 + 0.02
fig, ax = plt.subplots(figsize=(8.8, 5.4))
b1 = ax.bar(x - off, sample, w, label="Sample model (163 chunk, nhãn đầy đủ)", color=C["sample"], zorder=3)
b2 = ax.bar(x + off, main,   w, label="Hệ chính (11.759 chunk, dữ liệu thật)", color=C["main"], zorder=3)
barlabels(ax, b1, fontsize=9.5); barlabels(ax, b2, fontsize=9.5)

style_axes(ax, ylabel="Giá trị")
ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_ylim(0, 1.08)
titles(ax, "So sánh hai hệ trên các chỉ số chung",
       "Faithfulness/Answer Relevance chỉ đo được ở sample (hệ chính thiếu ground-truth answer)")
ax.legend(loc="upper center", ncol=1, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.1))
fig.text(0.5, -0.12, "Recall hệ chính là xấp xỉ keyword; sample là Recall thật.",
         ha="center", fontsize=8.6, color=C["muted"])
save(fig, "c17_two_systems")
