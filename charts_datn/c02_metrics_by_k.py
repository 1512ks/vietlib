"""
Biểu đồ #2 — Metric theo K (1,3,5,10), pipeline app (hybrid+group, sample sau pyvi).
P@K GIẢM còn Recall/nDCG TĂNG theo K.
"""
import matplotlib.pyplot as plt
from _style import save, C, style_axes, titles

K = [1, 3, 5, 10]
P    = [0.932, 0.864, 0.668, 0.405]
R    = [0.277, 0.710, 0.840, 0.930]
nDCG = [0.765, 0.816, 0.842, 0.871]
MRR  = [0.932, 0.966, 0.966, 0.966]

fig, ax = plt.subplots(figsize=(8.8, 5.4))
series = [
    ("Precision@K",     P,    C["bad"],     "o"),
    ("Recall@K (thật)", R,    C["main"],    "s"),
    ("nDCG@K",          nDCG, C["sample"],  "^"),
    ("MRR",             MRR,  C["warn"],    "D"),
]
for name, y, col, mk in series:
    ax.plot(K, y, mk + "-", color=col, lw=2.4, ms=8, label=name, zorder=3)

# chỉ ghi nhãn ở ĐẦU (K=1) và CUỐI (K=10) để tránh rối
for name, y, col, mk in series:
    ax.annotate(f"{y[-1]:.2f}", (K[-1], y[-1]), textcoords="offset points",
                xytext=(10, -3), ha="left", fontsize=10, fontweight="bold", color=col)
ax.annotate(f"{P[0]:.2f}",  (1, P[0]),  textcoords="offset points", xytext=(-4, 8),  ha="right", fontsize=10, color=C["bad"])
ax.annotate(f"{R[0]:.2f}",  (1, R[0]),  textcoords="offset points", xytext=(-4, -14), ha="right", fontsize=10, color=C["main"])

style_axes(ax, ylabel="Giá trị metric")
ax.set_xticks(K); ax.set_xlabel("K (số kết quả top đầu)", color=C["muted"])
ax.set_ylim(0.18, 1.05); ax.set_xlim(0.3, 11.5)
titles(ax, "Diễn biến metric theo K — pipeline app",
       "Precision giảm vì mẫu số = K; Recall & nDCG tăng → chất lượng thực tốt")
ax.legend(loc="center right", frameon=False, fontsize=10.5)

ax.annotate("P@K giảm: mẫu số K,\nmỗi câu ~3–5 chunk relevant",
            xy=(10, 0.405), xytext=(6.2, 0.27), fontsize=9.5, color=C["bad"], ha="left",
            arrowprops=dict(arrowstyle="->", color=C["bad"], lw=1.2))
save(fig, "c02_metrics_by_k")
