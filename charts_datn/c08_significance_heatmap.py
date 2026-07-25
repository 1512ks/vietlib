"""
Biểu đồ #8 — Ma trận ý nghĩa thống kê (paired t-test, nDCG@5, n=44, sau pyvi).
Ô xanh navy = khác biệt CÓ ý nghĩa (p<0.05); xám = không.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from _style import save, C

labels = ["BM25", "Vector", "Hybrid", "Hybrid+\ngroup"]
n = len(labels)
P = np.full((n, n), np.nan)
pairs = {(0, 1): 0.172, (0, 2): 0.001, (0, 3): 0.000,
         (1, 2): 0.169, (1, 3): 0.002, (2, 3): 0.003}
for (i, j), p in pairs.items():
    P[i, j] = P[j, i] = p
sig = (P < 0.05).astype(float)
sig[np.isnan(P)] = np.nan

fig, ax = plt.subplots(figsize=(6.8, 5.8))
cmap = ListedColormap(["#EDF1F6", C["sample"]])   # xám nhạt / indigo
ax.imshow(sig, cmap=cmap, vmin=0, vmax=1)

for i in range(n):
    for j in range(n):
        if i == j:
            ax.text(j, i, "—", ha="center", va="center", color="#C3CBD6", fontsize=18)
        elif not np.isnan(P[i, j]):
            p = P[i, j]
            has = p < 0.05
            ax.text(j, i, f"p = {p:.3f}", ha="center", va="center",
                    color="white" if has else C["muted"], fontsize=11.5,
                    fontweight="bold" if has else "normal")
            ax.text(j, i + 0.24, "có ý nghĩa" if has else "không",
                    ha="center", va="center", fontsize=9,
                    color="#DCE6F5" if has else "#9AA4B2")

ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=11)
ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=11)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks(np.arange(-.5, n, 1), minor=True)
ax.set_yticks(np.arange(-.5, n, 1), minor=True)
ax.grid(which="minor", color="white", lw=3)
ax.tick_params(which="minor", length=0)
ax.set_title("Kiểm định paired t-test · nDCG@5 (n=44)", loc="left",
             fontsize=15, fontweight="bold", color=C["ink"], pad=18)
ax.annotate("Ô xanh = khác biệt có ý nghĩa thống kê (p < 0.05)", xy=(0, 1),
            xytext=(0, 6), xycoords="axes fraction", textcoords="offset points",
            ha="left", va="bottom", fontsize=10.5, color=C["muted"])
save(fig, "c08_significance_heatmap")
