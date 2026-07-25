"""
Biểu đồ hệ chính #2 — Metric theo K cho pipeline Hybrid (hệ chính).
Lưu ý: ground-truth theo keyword nên Precision@K = Recall@K (đường trùng).
"""
import matplotlib.pyplot as plt
from _style import save, C, style_axes, titles

K = [1, 3, 5, 10]
P    = [0.880, 0.787, 0.712, 0.538]   # = Recall@K (keyword GT)
nDCG = [0.880, 0.851, 0.866, 0.921]
MRR  = [0.919, 0.919, 0.919, 0.919]

fig, ax = plt.subplots(figsize=(8.8, 5.4))
series = [
    ("Precision@K = Recall@K", P,    C["bad"],    "o"),
    ("nDCG@K",                 nDCG, C["sample"], "^"),
    ("MRR",                    MRR,  C["warn"],   "D"),
]
for name, y, col, mk in series:
    ax.plot(K, y, mk + "-", color=col, lw=2.4, ms=8, label=name, zorder=3)
    ax.annotate(f"{y[-1]:.2f}", (K[-1], y[-1]), textcoords="offset points",
                xytext=(10, -3), ha="left", fontsize=10, fontweight="bold", color=col)

style_axes(ax, ylabel="Giá trị metric")
ax.set_xticks(K); ax.set_xlabel("K (số kết quả top đầu)", color=C["muted"])
ax.set_ylim(0.45, 1.0); ax.set_xlim(0.3, 11.5)
titles(ax, "Diễn biến metric theo K — Hybrid (hệ chính)",
       "Ground-truth theo keyword → Precision@K trùng Recall@K (hạn chế đã nêu)")
ax.legend(loc="lower left", frameon=False, fontsize=10.5)
ax.annotate("P@K giảm còn nDCG@K tăng\n→ chất lượng thứ hạng tốt",
            xy=(10, 0.921), xytext=(5.6, 0.965), fontsize=9.5, color=C["sample"], ha="left")
save(fig, "m02_main_metrics_by_k")
