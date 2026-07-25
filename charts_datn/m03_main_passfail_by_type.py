"""
Biểu đồ hệ chính #3 — Kết quả 50 kịch bản generation theo loại (pass/fail).
FACTUAL 16/16 · AUTHOR 13/13 · SEMANTIC 12/14 · HARD 5/7.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, style_axes, titles

types = ["FACTUAL", "AUTHOR", "SEMANTIC", "HARD\n(ngoài kho)"]
passed = [16, 13, 12, 5]
failed = [0, 0, 2, 2]
total  = [p + f for p, f in zip(passed, failed)]

x = np.arange(len(types))
fig, ax = plt.subplots(figsize=(8.6, 5.2))
b1 = ax.bar(x, passed, width=0.5, color=C["sample"], zorder=3, label="Đạt")
b2 = ax.bar(x, failed, width=0.5, bottom=passed, color=C["bad"], zorder=3, label="Không đạt")

for xi, p, t in zip(x, passed, total):
    ax.text(xi, t + 0.15, f"{p}/{t}", ha="center", va="bottom",
            fontsize=12, fontweight="bold", color=C["ink"])
# nhãn số fail
for xi, p, f in zip(x, passed, failed):
    if f:
        ax.text(xi, p + f/2, str(f), ha="center", va="center",
                fontsize=11, fontweight="bold", color="white")

style_axes(ax, ylabel="Số kịch bản")
ax.set_xticks(x); ax.set_xticklabels(types)
ax.set_ylim(0, 18)
titles(ax, "Kết quả 50 kịch bản generation theo loại — hệ chính",
       "Pass rate tổng 46/50 = 92%  ·  FACTUAL & AUTHOR đạt tuyệt đối")
ax.legend(loc="upper right", frameon=False, fontsize=10)
ax.annotate("2 ca HARD lọt = hallucinate\n(Trăm năm cô đơn, Nhà giả kim)",
            xy=(3, 5.5), xytext=(1.75, 15.2), fontsize=9, color=C["bad"], ha="left",
            arrowprops=dict(arrowstyle="->", color=C["bad"], lw=1.2))
save(fig, "m03_main_passfail_by_type")
