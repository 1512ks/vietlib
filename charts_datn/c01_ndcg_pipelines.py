"""
Biểu đồ #1 — nDCG@5 của 4 pipeline: Sample model vs Hệ chính (template hiện đại).
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles, BAR_W_GROUP

pipelines = ["BM25", "Vector", "Hybrid", "Hybrid+\n(cấu hình app)"]
sample = [0.710, 0.745, 0.781, 0.842]
main   = [0.809, 0.399, 0.866, 0.866]

x = np.arange(len(pipelines))
w = BAR_W_GROUP
fig, ax = plt.subplots(figsize=(8.6, 5.2))
off = w/2 + 0.02   # khe hở giữa 2 cột trong nhóm
b1 = ax.bar(x - off, sample, w, label="Sample model (163 chunk)",
            color=C["sample"], zorder=3)
b2 = ax.bar(x + off, main,   w, label="Hệ chính (11.759 chunk)",
            color=C["main"], zorder=3)
barlabels(ax, b1, fontsize=10); barlabels(ax, b2, fontsize=10)

style_axes(ax, ylabel="nDCG@5")
ax.set_xticks(x); ax.set_xticklabels(pipelines)
ax.set_ylim(0, 1.0)

# ngưỡng "tốt" 0.8 — đường mảnh, nhãn nằm ở lề phải ngoài vùng cột
ax.axhline(0.8, color=C["good"], lw=1.2, ls=(0, (4, 4)), alpha=0.6, zorder=2)
ax.text(-0.46, 0.808, "ngưỡng tốt 0.8", color=C["good"],
        fontsize=9.5, ha="left", va="bottom")

titles(ax, "nDCG@5 của 4 pipeline retrieval",
       "So sánh trên hai hệ · bộ test 50 câu (sample sau tách từ pyvi)")
ax.legend(loc="lower center", ncol=2, frameon=False,
          bbox_to_anchor=(0.5, -0.22), fontsize=10.5)
fig.subplots_adjust(bottom=0.2)
save(fig, "c01_ndcg_pipelines")
