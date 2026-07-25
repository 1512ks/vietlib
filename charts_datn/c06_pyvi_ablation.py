"""
Biểu đồ #6 — Tác động tách từ pyvi lên BM25 và pipeline app (trước/sau), 4 metric @5.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, BAR_W_GROUP

metrics = ["nDCG@5", "MRR@5", "MAP@5", "Recall@5"]
data = {
    "BM25": {"before": [0.624, 0.823, 0.569, 0.630], "after": [0.710, 0.901, 0.712, 0.719]},
    "Hybrid+group (app)": {"before": [0.812, 0.943, 0.846, 0.822], "after": [0.842, 0.966, 0.887, 0.840]},
}

fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.0), sharey=True)
x = np.arange(len(metrics)); w = BAR_W_GROUP; off = w/2 + 0.02
for ax, (name, d) in zip(axes, data.items()):
    b1 = ax.bar(x - off, d["before"], w, label="Trước (âm tiết)", color=C["bm25"], zorder=3)
    b2 = ax.bar(x + off, d["after"],  w, label="Sau (pyvi word)", color=C["sample"], zorder=3)
    barlabels(ax, b1, fontsize=8.5); barlabels(ax, b2, fontsize=8.5)
    style_axes(ax)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=10)
    ax.set_title(name, loc="left", fontsize=13, fontweight="bold", color=C["ink"], pad=10)
    ax.set_ylim(0, 1.05)
axes[0].set_ylabel("Giá trị", color=C["muted"])
axes[0].legend(loc="lower right", frameon=False, fontsize=9.5)
fig.suptitle("Tác động tách từ tiếng Việt (pyvi) lên retrieval — sample model",
             fontsize=15, fontweight="bold", x=0.05, ha="left", color=C["ink"], y=1.02)
save(fig, "c06_pyvi_ablation")
