"""
Biểu đồ #20 — So sánh TRƯỚC/SAU đổi embedder (sample model, pipeline Hybrid @5).
MiniLM (đa ngôn ngữ, như hệ lớn) → bge-m3 (chuyên tiếng Việt). Ablation THẬT.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles, BAR_W_GROUP, BLUES

metrics = ["nDCG@5", "MRR@5", "Recall@5", "MAP@5"]
before  = [0.420, 0.640, 0.348, 0.330]   # MiniLM
after   = [0.699, 0.902, 0.646, 0.655]   # bge-m3

x = np.arange(len(metrics)); w = BAR_W_GROUP; off = w/2 + 0.02
fig, ax = plt.subplots(figsize=(8.8, 5.2))
b1 = ax.bar(x - off, before, w, label="Trước — MiniLM (đa ngôn ngữ)", color=BLUES[1], zorder=3)
b2 = ax.bar(x + off, after,  w, label="Sau — bge-m3 (tiếng Việt)", color=BLUES[2], zorder=3)
barlabels(ax, b1, fontsize=9.5); barlabels(ax, b2, fontsize=9.5)

# mũi tên +delta trên mỗi cặp
for xi, a, b in zip(x, before, after):
    ax.annotate(f"+{b-a:.2f}", xy=(xi, b + 0.055), ha="center",
                fontsize=9, fontweight="bold", color=C["good"])

style_axes(ax, ylabel="Giá trị (Hybrid @5)")
ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_ylim(0, 1.05)
titles(ax, "So sánh trước – sau: đổi embedder",
       "Sample model · pipeline Hybrid @5 · ablation thật (cùng corpus, cùng code)")
ax.legend(loc="upper center", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.12))
fig.subplots_adjust(bottom=0.18)
save(fig, "c20_embedder_beforeafter")
