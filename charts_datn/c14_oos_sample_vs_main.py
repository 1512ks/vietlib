"""
Biểu đồ #14 — Từ chối OOS: Sample (6/6) vs Hệ chính (5/7, lọt 2 tiểu thuyết NN → hallucinate).
"""
import matplotlib.pyplot as plt
from _style import save, C, style_axes, titles, BAR_W_SINGLE

systems = ["Sample model\n(có ngưỡng confidence)", "Hệ chính\n(chưa có confidence-gate)"]
refused = [6/6, 5/7]
counts  = ["6/6", "5/7"]
colors  = [C["sample"], C["warn"]]

fig, ax = plt.subplots(figsize=(8.2, 5.4))
bars = ax.bar(systems, refused, width=BAR_W_SINGLE, color=colors, zorder=3)
for b, c in zip(bars, counts):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02,
            f"{b.get_height()*100:.1f}%  ({c})", ha="center", va="bottom",
            fontsize=13, fontweight="bold", color=C["ink"])

style_axes(ax, ylabel="OOS Recall (tỉ lệ từ chối đúng câu ngoài kho)")
ax.set_ylim(0, 1.18)
ax.axhline(0.9, color=C["good"], ls=(0, (4, 4)), lw=1.2, alpha=0.6, zorder=2)
ax.text(-0.48, 0.905, "mục tiêu ≥ 0.90", color=C["good"], fontsize=9.5, ha="left", va="bottom")
titles(ax, "Khả năng chống 'bịa' câu ngoài phạm vi",
       "Sample chặn toàn bộ nhờ ngưỡng confidence; hệ chính để lọt tiểu thuyết nước ngoài")

ax.annotate("2 ca LỌT → hallucinate:\n•  Trăm năm cô đơn\n•  Nhà giả kim\n(không có trong kho)",
            xy=(1, 5/7), xytext=(1.28, 0.40), fontsize=10, color=C["bad"], ha="left",
            bbox=dict(boxstyle="round,pad=0.45", fc="#FBEEED", ec=C["bad"], lw=1.2),
            arrowprops=dict(arrowstyle="->", color=C["bad"], lw=1.4))
save(fig, "c14_oos_sample_vs_main")
